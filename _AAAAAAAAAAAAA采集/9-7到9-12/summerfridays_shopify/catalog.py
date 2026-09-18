"""Summer Fridays 首页目录解析。

Summer Fridays 使用自定义主题：桌面导航是 ``nav.desktop-menu__main``，顶层项为
``ul.desktop-menu__main-menu > li``，顶层链接是 ``a.desktop-menu__link``，下拉内容
在 ``div.desktop-menu__submenu``。mega 下拉由多个
``ul.desktop-menu__submenu-items`` 列组成：普通列直接是 ``li > a``；分组列的
``li`` 先给出 ``span`` 标题（如 ``By Skin Type``），其后的兄弟 ``li > a`` 才是该
分组的子级。About 下拉只包含 ``/pages/`` 链接，Blog 顶层链接是 ``/blogs/``。

该结构不属于 ``_ljp.mb.shopify`` 内置的 ``header__inline-menu`` /
``data-nav-desktop`` / ``main-menu-panel`` / ``details-mega`` 任一菜单，因此在站点
``catalog.py`` 注册自己的解析器。导航栏之外的 collection 链接（首页专题卡片等）
统一挂在自定义一级目录 ``Other`` 下。
"""

from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


def _clean_text(value) -> str:
    return ' '.join(str(value or '').split())


def _is_collection_url(url: str) -> bool:
    path = urlsplit(url or '').path.lower()
    return '/collections' in path and '/product' not in path


class SummerFridaysCatalogParser(CatalogParser):
    """解析 ``desktop-menu__main`` 三层菜单，并补充导航栏之外的 collection。"""

    nav_xpath = (
        '//nav[contains(concat(" ", normalize-space(@class), " "),'
        ' " desktop-menu__main ")]'
    )
    page_group_name = 'Other'
    heading_tags = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

    def matches(self, html):
        return 'desktop-menu__main' in html and 'desktop-menu__submenu' in html

    @staticmethod
    def link_text(element) -> str:
        return _clean_text(
            ' '.join(element.xpath('.//text()[not(ancestor::svg)]'))
        )

    def put_node(self, collector, nodes, name, url='', child=None):
        """只保留 collection 链接；无链接但有子级的分组继续保留。"""
        normalized_url = collector.normalize_url(url) if url else ''
        if normalized_url and not _is_collection_url(normalized_url):
            normalized_url = ''
        child = child or {}
        if not normalized_url and not child:
            return None
        return collector.add_node(nodes, name, normalized_url, child)

    def parse_list(self, menu_list, collector, result):
        """解析一个链接列表；分组标题后的兄弟项归入该分组。"""
        group = None
        for item in menu_list.xpath('./li'):
            nested = item.xpath('./ul[1]')
            links = item.xpath('./a[@href][1]')
            if links:
                link = links[0]
                name = self.link_text(link)
                if not name:
                    continue
                child = self.parse_list(nested[0], collector, {}) if nested else {}
                target = group if group is not None else result
                self.put_node(collector, target, name, link.get('href') or '', child)
                continue
            heading = self.heading_node(item)
            if heading is not None:
                name = self.link_text(heading)
                child = self.parse_list(nested[0], collector, {}) if nested else {}
                # 分组标题即使暂时没有叶子也要先建节点，后续兄弟链接写入其 child。
                group = collector.add_node(result, name, '', child)
                continue
            if nested:
                self.merge_children(result, self.parse_list(nested[0], collector, {}))
                group = None
        return result

    def heading_node(self, item):
        """返回 ``li`` 自身的非链接标题节点，没有则返回 ``None``。"""
        for tag in self.heading_tags + ('span', 'p'):
            nodes = item.xpath(f'./{tag}[1]')
            if nodes and self.link_text(nodes[0]):
                return nodes[0]
        return None

    @staticmethod
    def merge_children(target, source):
        for name, node in source.items():
            target.setdefault(name, node)

    def submenu_lists(self, submenu):
        """返回下拉中不嵌套于其它列表的链接列表（每个 mega 列一个）。"""
        lists = list(submenu.iter('ul'))
        return [
            menu_list
            for menu_list in lists
            if not any(ancestor in lists for ancestor in menu_list.iterancestors('ul'))
        ]

    def menu_items(self, nav, collector):
        result = {}
        for item in nav.xpath('.//ul[contains(@class, "desktop-menu__main-menu")]/li'):
            links = item.xpath('./a[@href][1]')
            if not links:
                continue
            link = links[0]
            name = self.link_text(link)
            if not name:
                continue
            child = {}
            for submenu in item.xpath('./div[contains(@class, "desktop-menu__submenu")]'):
                for menu_list in self.submenu_lists(submenu):
                    self.parse_list(menu_list, collector, child)
            self.put_node(collector, result, name, link.get('href') or '', child)
        return result

    @staticmethod
    def known_urls(nodes, found=None):
        if found is None:
            found = set()
        for node in nodes.values():
            if node.get('url'):
                found.add(node['url'])
            SummerFridaysCatalogParser.known_urls(node.get('child') or {}, found)
        return found

    def page_link_name(self, link):
        for tag in self.heading_tags:
            heads = link.xpath(f'.//{tag}[1]')
            if heads:
                name = self.link_text(heads[0])
                if name:
                    return name
        for attr in ('aria-label', 'title'):
            name = _clean_text(link.get(attr))
            if name:
                return name
        return self.link_text(link)

    def parse_page_links(self, tree, collector, known):
        """收集导航栏之外的 collection 链接。"""
        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav'):
                continue
            href = link.get('href') or ''
            if not href or href.startswith('#'):
                continue
            url = collector.normalize_url(href)
            if not url or url in known or not _is_collection_url(url):
                continue
            if urlsplit(url).path.rstrip('/').endswith('/collections'):
                continue
            if self.put_node(
                collector, extra, self.page_link_name(link), href
            ) is not None:
                known.add(url)
        return extra

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 desktop-menu__main 导航')
        result = self.menu_items(navs[0], collector)
        if not result:
            raise RuntimeError('desktop-menu__main 没有可用目录')

        extra = self.parse_page_links(tree, collector, self.known_urls(result))
        if extra:
            group_name = self.page_group_name
            index = 2
            while group_name in result:
                group_name = f'{self.page_group_name}{index}'
                index += 1
            self.put_node(collector, result, group_name, '', extra)
        return result


class SummerFridaysCatCol(ShopifyCatCol):
    """Summer Fridays 目录采集器。"""

    parser_types = (SummerFridaysCatalogParser,)
    skip_url_ls = []
    no_url_ls = []


__all__ = ['SummerFridaysCatCol', 'SummerFridaysCatalogParser']
