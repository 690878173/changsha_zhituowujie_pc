"""Ergobaby 首页目录解析。

首页主题同时渲染两套自研菜单：桌面端 ``header-menu`` 里的 ``ul.menu-list``
mega menu，以及移动端 ``nav.menu-drawer__navigation`` 抽屉菜单。两者都匹配不到
内置 Shopify 解析器，因此在站点注册专属解析器。

解析器只保留 collection 链接，排除 product / pages 链接，并保留真实菜单层级。
桌面一级菜单的 ``Bouncers`` / ``Strollers`` 指向单品页，而同一份菜单的
``Shop All`` 子菜单给出了这两个分类的真实 collection 地址，因此用
``ROOT_COLLECTIONS`` 还原一级分类。移动端抽屉与桌面端是同一份导航，按层级合并
进同一棵树，同一层级已经出现过的名称或链接不再重复。导航栏之外的 collection
链接（公告栏、首页卡片等）统一挂到一级目录 ``Other``。
"""

from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


# 桌面一级菜单的链接被主题指向单品页，这里按同一份菜单 Shop All 子菜单中
# 同名条目给出的真实 collection 地址还原一级分类。
ROOT_COLLECTIONS = {
    'Bouncers': '/en-us/collections/baby-bouncers',
    'Strollers': '/en-us/collections/strollers',
}


def _cls(token):
    """构造按 class 整词匹配的 XPath 条件。"""
    return f'contains(concat(" ", normalize-space(@class), " "), " {token} ")'


def _text(node):
    return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())


class ErgobabyMenuParser(CatalogParser):
    """解析 Ergobaby 首页的桌面 mega menu 与移动端抽屉菜单。"""

    desktop_nav_xpath = f'//header-menu//nav/ul[{_cls("menu-list")}]'
    drawer_nav_xpath = f'//nav[{_cls("menu-drawer__navigation")}]/ul[{_cls("menu-drawer__menu")}]'
    nav_ancestor_xpath = (
        f'ancestor::header-menu | ancestor::nav[{_cls("menu-drawer__navigation")}]'
    )
    desktop_submenu_xpath = f'./div[{_cls("menu-list__submenu")}]'
    list_modern_xpath = f'.//ul[{_cls("list-modern")}]/li/a[@href]'
    center_group_xpath = f'.//ul[{_cls("mega--center-menu")}]/li'
    center_label_xpath = f'./span[{_cls("center-menu__label")}]'
    center_link_xpath = f'./ul[{_cls("center-menu__submenu")}]/li/a[@href]'
    drawer_childlist_xpath = f'.//ul[{_cls("menu-drawer__menu--childlist")}]'
    drawer_nested_xpath = f'./ul[{_cls("menu-drawer__menu")}]'
    skip_schemes = ('#', 'mailto:', 'tel:', 'javascript:')
    page_group_name = 'Other'

    def matches(self, html):
        return 'menu-list__list-item' in html and 'menu-drawer__navigation' in html

    @staticmethod
    def is_collection(url):
        """只接受 collection 链接，排除 product 链接与空 collection 根路径。

        站点链接带 ``/en-us`` 区域前缀，因此按路径片段判断而不是按前缀判断。
        """
        path = urlsplit(url or '').path.lower().rstrip('/')
        return '/collections/' in path and '/products/' not in path

    def clean_url(self, url, collector):
        """把链接规范为绝对 URL；非 collection 链接返回空字符串。"""
        if not url:
            return ''
        normalized = collector.normalize_url(url)
        return normalized if self.is_collection(normalized) else ''

    @staticmethod
    def level_urls(nodes):
        return {node['url'] for node in nodes.values() if node.get('url')}

    def put_node(self, nodes, name, url, child, collector, parent_url='', skip_duplicates=False):
        """写入节点；非 collection 链接置空，空分组丢弃，同名节点合并子级。"""
        normalized = self.clean_url(url, collector)
        if not normalized and not child:
            return None
        name = collector.normalize_name(name)
        if not name:
            return None
        if skip_duplicates and normalized and (
            normalized == parent_url or normalized in self.level_urls(nodes)
        ):
            return None
        existing = nodes.get(name)
        if isinstance(existing, dict):
            if normalized and not existing.get('url'):
                existing['url'] = normalized
            for child_name, child_node in (child or {}).items():
                existing['child'].setdefault(child_name, child_node)
            return existing
        return collector.add_node(nodes, name, normalized, child or {})

    def root_url(self, name, href, collector):
        """一级菜单链接优先取自身 collection，其次取站点给出的同名分类映射。"""
        return self.clean_url(href, collector) or self.clean_url(
            ROOT_COLLECTIONS.get(name, ''), collector
        )

    def parse_desktop_submenu(self, submenu, collector):
        """解析一个桌面一级菜单的二级面板。"""
        result = {}
        for link in submenu.xpath(self.list_modern_xpath):
            self.put_node(result, _text(link), link.get('href') or '', {}, collector)
        for group in submenu.xpath(self.center_group_xpath):
            labels = group.xpath(self.center_label_xpath)
            if not labels:
                continue
            leaves = {}
            for link in group.xpath(self.center_link_xpath):
                self.put_node(leaves, _text(link), link.get('href') or '', {}, collector)
            if leaves:
                self.put_node(result, _text(labels[0]), '', leaves, collector)
        return result

    def parse_desktop(self, tree, collector):
        navs = tree.xpath(self.desktop_nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 header-menu 的 ul.menu-list 菜单')
        result = {}
        for item in navs[0].xpath('./li'):
            links = item.xpath('./a[@href]')
            if not links:
                continue
            name = _text(links[0])
            if not name:
                continue
            submenus = item.xpath(self.desktop_submenu_xpath)
            child = self.parse_desktop_submenu(submenus[0], collector) if submenus else {}
            self.put_node(
                result,
                name,
                self.root_url(name, links[0].get('href') or '', collector),
                child,
                collector,
            )
        return result

    def merge_drawer_list(self, menu, nodes, collector, parent_url=''):
        """把移动端抽屉菜单按层级合并进同一棵树。

        同名节点直接并入其子级，因此同级重复的 collection 链接（例如抽屉里的
        ``View All Carriers`` 与上级 ``Baby Carriers`` 同链接）会被跳过。
        """
        for item in menu.xpath('./li'):
            details = item.xpath('./details')
            if details:
                summaries = details[0].xpath('./summary')
                name = _text(summaries[0]) if summaries else ''
                if not name:
                    continue
                childlists = details[0].xpath(self.drawer_childlist_xpath)
                existing = nodes.get(collector.normalize_name(name))
                if isinstance(existing, dict):
                    if childlists:
                        self.merge_drawer_list(
                            childlists[0], existing['child'], collector,
                            existing.get('url') or parent_url,
                        )
                    continue
                child = {}
                if childlists:
                    child = self.merge_drawer_list(childlists[0], {}, collector, parent_url)
                self.put_node(
                    nodes, name, '', child, collector,
                    parent_url=parent_url, skip_duplicates=True,
                )
                continue
            links = item.xpath('./a[@href]')
            if not links:
                continue
            link = links[0]
            url = self.clean_url(link.get('href') or '', collector)
            child = {}
            nested = item.xpath(self.drawer_nested_xpath)
            if nested:
                child = self.merge_drawer_list(nested[0], {}, collector, url or parent_url)
            self.put_node(
                nodes, _text(link), link.get('href') or '', child, collector,
                parent_url=parent_url, skip_duplicates=True,
            )
        return nodes

    @staticmethod
    def tree_urls(nodes, found=None):
        """收集目录树中已经出现的绝对链接，供 ``Other`` 去重。"""
        if found is None:
            found = set()
        for node in nodes.values():
            if node.get('url'):
                found.add(node['url'])
            ErgobabyMenuParser.tree_urls(node.get('child') or {}, found)
        return found

    @staticmethod
    def page_link_name(link):
        """导航外链接命名：``aria-label`` 优先，其次链接文本。"""
        label = ' '.join(str(link.get('aria-label') or '').split())
        return label or _text(link)

    def parse_page_links(self, tree, collector, known):
        """收集导航栏之外的 collection 链接，作为 ``Other`` 的二级目录。

        同一 URL 在页面上有多处入口时取最短的可见文案作为目录名，公告栏的整句
        促销文案因此不会成为分类名。
        """
        names = {}
        order = []
        for link in tree.xpath('//a[@href]'):
            if link.xpath(self.nav_ancestor_xpath):
                continue
            href = link.get('href') or ''
            if not href or href.startswith(self.skip_schemes):
                continue
            url = self.clean_url(href, collector)
            if not url or url in known:
                continue
            name = self.page_link_name(link)
            if not name:
                continue
            if url not in names:
                names[url] = name
                order.append(url)
            elif len(name) < len(names[url]):
                names[url] = name
        extra = {}
        for url in order:
            if self.put_node(extra, names[url], url, {}, collector, skip_duplicates=True) is not None:
                known.add(url)
        return extra

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        result = self.parse_desktop(tree, collector)
        drawer_navs = tree.xpath(self.drawer_nav_xpath)
        if drawer_navs:
            self.merge_drawer_list(drawer_navs[0], result, collector)
        extra = self.parse_page_links(tree, collector, self.tree_urls(result))
        if extra:
            self.put_node(result, self.page_group_name, '', extra, collector)
        if not result:
            raise RuntimeError('Ergobaby 首页菜单没有可用目录')
        return result


class ErgobabyCatCol(ShopifyCatCol):
    """站点目录采集器：只注册 Ergobaby 专属解析器。"""

    parser_types = (ErgobabyMenuParser,)


__all__ = ['ErgobabyCatCol', 'ErgobabyMenuParser']
