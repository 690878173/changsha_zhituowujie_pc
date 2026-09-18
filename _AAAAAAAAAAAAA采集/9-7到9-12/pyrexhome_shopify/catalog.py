"""Pyrex Home 首页目录解析。

Pyrex Home 使用自定义主题，页面里有两套 ``ul.main-nav``：

- 桌面主菜单在 ``nav[aria-label="Primary"]`` 下，顶层 ``li`` 直接是
  ``a.main-nav__item--primary`` 或 ``details.js-mega-nav``；下拉列在
  ``div.main-nav__child`` 的 ``ul.child-nav`` 里。
- 移动端完整菜单在 ``<mobile-menu>`` 里（该主题把空的 ``nav`` 写成了自闭合
  标签，因此这里的 ``ul.main-nav`` 并不在 ``nav`` 内），比桌面菜单多了
  ``Snapware`` 品牌分组，并使用 ``nav-menu > details > ul.main-nav__grandchild``
  表达三级目录。

该结构不属于 ``_ljp.mb.shopify`` 内置的 ``header__inline-menu`` /
``data-nav-desktop`` / ``main-menu-panel`` / ``details-mega`` 任一菜单，因此在
站点 ``catalog.py`` 注册自己的解析器。桌面菜单作为主目录树；移动端菜单里桌面
已覆盖的链接会被去掉，其余目录与首页促销位等链接统一挂在自定义一级目录
``Other`` 下。

站点要求目录最多三级。移动端菜单的 ``Pyrex`` / ``Snapware`` 品牌层自身没有
collection 链接，只是把并列的子分类包成一层；把它保留成 ``Other`` 的子级会
直接顶出四级目录，因此这类品牌容器不额外占层，``Other`` 下直接保留
``Plastic Food Storage`` / ``Glass Food Storage`` 这样的真实分组。
层级必须保持原样，不允许用合并名称的方式压缩。
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


class PyrexhomeCatalogParser(CatalogParser):
    """解析品牌主菜单，并把浅层补充链接收敛到 ``Other``。"""

    nav_xpath = '//nav[@aria-label="Primary"]'
    mobile_menu_xpath = '//mobile-menu'
    page_group_name = 'Other'
    max_depth = 3
    heading_tags = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
    cta_suffixes = ('shop now', 'view all', 'learn more', 'shop all')

    def matches(self, html):
        return 'main-nav' in html and 'main-nav__child' in html

    @staticmethod
    def link_text(element) -> str:
        return _clean_text(' '.join(element.xpath('.//text()[not(ancestor::svg)]')))

    @staticmethod
    def is_hidden_item(element) -> bool:
        """跳过 ``md:hidden`` / ``lg:hidden`` 的移动端返回按钮与标题副本。"""
        return any(
            token.endswith(':hidden') for token in (element.get('class') or '').split()
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

    # ---- 菜单解析 ----

    def parse_leaf_list(self, menu_list, collector):
        """解析一层 ``li``：链接叶子、``nav-menu`` 分组或嵌套列表。"""
        result = {}
        for item in menu_list.xpath('./li'):
            if self.is_hidden_item(item):
                continue
            nav_menu = item.xpath('./nav-menu[1]')
            if nav_menu:
                self.parse_nav_menu(nav_menu[0], collector, result)
                continue
            links = item.xpath('./a[@href][1]')
            if links:
                link = links[0]
                name = self.link_text(link)
                if name:
                    self.put_node(
                        collector, result, name, link.get('href') or ''
                    )
                continue
            nested = item.xpath('./ul[1]')
            if nested:
                self.merge_children(
                    result, self.parse_leaf_list(nested[0], collector)
                )
        return result

    def parse_nav_menu(self, nav_menu, collector, result):
        """解析 ``nav-menu`` 三级分组：``summary`` 标题 + 子列表。"""
        details = nav_menu.xpath('.//details[1]')
        if not details:
            return
        detail = details[0]
        summary = detail.xpath('./summary[1]')
        name = ''
        url = ''
        if summary:
            links = summary[0].xpath('.//a[@href][1]')
            if links:
                name = self.link_text(links[0])
                url = links[0].get('href') or ''
            else:
                name = self.link_text(summary[0])
        children = {}
        for child_list in detail.xpath('.//ul[contains(@class, "main-nav__grandchild")]'):
            self.merge_children(
                children, self.parse_leaf_list(child_list, collector)
            )
        if url:
            children = self.drop_group_duplicates(collector, url, children)
        if not name:
            self.merge_children(result, children)
            return
        self.put_node(collector, result, name, url, children)

    @staticmethod
    def drop_group_duplicates(collector, url, children):
        """去掉与分组自身同址的 ``View all`` 叶子，分组链接已表达同一目录。"""
        normalized_url = collector.normalize_url(url)
        return {
            name: node
            for name, node in children.items()
            if node.get('url') != normalized_url or node.get('child')
        }

    def parse_top_list(self, menu_list, collector):
        """解析 ``ul.main-nav`` 的顶层项。"""
        result = {}
        for item in menu_list.xpath('./li'):
            if self.is_hidden_item(item):
                continue
            details = item.xpath('./details[1]')
            if not details:
                links = item.xpath('./a[@href][1]')
                if links:
                    name = self.link_text(links[0])
                    if name:
                        self.put_node(
                            collector, result, name, links[0].get('href') or ''
                        )
                continue
            detail = details[0]
            summary = detail.xpath('./summary[1]')
            if not summary:
                continue
            links = summary[0].xpath('.//a[@href][1]')
            if links:
                name = self.link_text(links[0])
                url = links[0].get('href') or ''
            else:
                name = self.link_text(summary[0])
                url = ''
            if not name:
                continue
            children = {}
            for child_list in detail.xpath(
                './/div[contains(@class, "main-nav__child")]'
                '//ul[contains(concat(" ", normalize-space(@class), " "), " child-nav ")]'
            ):
                self.merge_children(
                    children, self.parse_leaf_list(child_list, collector)
                )
            self.put_node(collector, result, name, url, children)
        return result

    @staticmethod
    def merge_children(target, source):
        for name, node in source.items():
            target.setdefault(name, node)

    def put_node_unique(self, collector, nodes, name, url='', child=None):
        """插入节点；同名但不同 URL 时用 handle 后缀区分，避免丢链接。"""
        normalized_url = collector.normalize_url(url) if url else ''
        if normalized_url and not _is_collection_url(normalized_url):
            normalized_url = ''
        child = child or {}
        if not normalized_url and not child:
            return None
        target_name = name
        if target_name in nodes and (nodes[target_name].get('url') or '') != normalized_url:
            handle = collector.tool.URL.get_handle(normalized_url)
            target_name = f'{name} ({handle})' if handle else name
            index = 2
            while target_name in nodes:
                target_name = f'{name} ({handle}-{index})'
                index += 1
        return collector.add_node(nodes, target_name, normalized_url, child)

    def merge_nodes(self, collector, target, source):
        for name, node in source.items():
            self.put_node_unique(
                collector,
                target,
                name,
                node.get('url') or '',
                node.get('child') or {},
            )

    def prune_tree(self, nodes, known):
        """去掉主目录已覆盖的链接，并丢弃剩余的空分组。"""
        result = {}
        for name, node in nodes.items():
            child = self.prune_tree(node.get('child') or {}, known)
            url = node.get('url') or ''
            if url in known:
                url = ''
            if url or child:
                result[name] = {'url': url, 'child': child}
        return result

    def lift_brand_wrappers(self, nodes):
        """去掉没有 collection 链接的品牌容器层，保留其下的真实分组。"""
        result = {}
        for name, node in nodes.items():
            child = self.lift_brand_wrappers(node.get('child') or {})
            url = node.get('url') or ''
            if not url and child:
                for child_name, child_node in child.items():
                    result.setdefault(child_name, child_node)
                continue
            result[name] = {'url': url, 'child': child}
        return result

    @classmethod
    def tree_depth(cls, nodes, depth=1):
        """返回目录树的最大层级；无 URL 的分组同样计入层级。"""
        deepest = 0
        for node in nodes.values():
            child = node.get('child') or {}
            deepest = max(
                deepest,
                depth if not child else cls.tree_depth(child, depth + 1),
            )
        return deepest

    # ---- 导航栏之外的 collection ----

    @staticmethod
    def known_urls(nodes, found=None):
        if found is None:
            found = set()
        for node in nodes.values():
            if node.get('url'):
                found.add(node['url'])
            PyrexhomeCatalogParser.known_urls(node.get('child') or {}, found)
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
        for section in link.xpath('ancestor::section[1]'):
            for tag in self.heading_tags:
                heads = section.xpath(f'.//{tag}[1]')
                if heads:
                    name = self.link_text(heads[0])
                    if name:
                        return name
        name = self.link_text(link)
        lowered = name.lower()
        for suffix in self.cta_suffixes:
            if lowered.endswith(suffix):
                name = name[: -len(suffix)].rstrip()
                lowered = name.lower()
        return name

    def parse_page_links(self, tree, collector, known):
        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav[@aria-label="Primary"]') or link.xpath(
                'ancestor::mobile-menu'
            ):
                continue
            href = link.get('href') or ''
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue
            url = collector.normalize_url(href)
            if not url or url in known or not _is_collection_url(url):
                continue
            if urlsplit(url).path.rstrip('/').endswith('/collections'):
                continue
            name = self.page_link_name(link)
            if not name:
                continue
            if self.put_node(collector, extra, name, href) is not None:
                known.add(url)
        return extra

    # ---- 入口 ----

    @staticmethod
    def main_lists(containers):
        """返回容器内的 ``ul.main-nav`` 列表。"""
        lists = []
        for container in containers:
            lists.extend(
                container.xpath(
                    './/ul[contains(concat(" ", normalize-space(@class), " "),'
                    ' " main-nav ")]'
                )
            )
        return lists

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        nav_lists = self.main_lists(tree.xpath(self.nav_xpath))
        mobile_lists = self.main_lists(tree.xpath(self.mobile_menu_xpath))
        if nav_lists:
            result = self.parse_top_list(nav_lists[0], collector)
        elif mobile_lists:
            result = self.parse_top_list(mobile_lists[0], collector)
            mobile_lists = []
        else:
            raise RuntimeError('页面中未找到 main-nav 菜单')
        if not result:
            raise RuntimeError('main-nav 没有可用目录')

        known = self.known_urls(result)
        extra = {}
        for mobile_list in mobile_lists:
            self.merge_nodes(
                collector,
                extra,
                self.lift_brand_wrappers(
                    self.prune_tree(
                        self.parse_top_list(mobile_list, collector), known
                    )
                ),
            )
        known.update(self.known_urls(extra))
        self.merge_nodes(
            collector, extra, self.parse_page_links(tree, collector, known)
        )
        if extra:
            group_name = self.page_group_name
            index = 2
            while group_name in result:
                group_name = f'{self.page_group_name}{index}'
                index += 1
            self.put_node(collector, result, group_name, '', extra)
        depth = self.tree_depth(result)
        if depth > self.max_depth:
            raise RuntimeError(f'目录层级 {depth} 超过站点上限 {self.max_depth}')
        return result


class PyrexhomeCatCol(ShopifyCatCol):
    """Pyrex Home 目录采集器。"""

    parser_types = (PyrexhomeCatalogParser,)
    skip_url_ls = []
    no_url_ls = []


__all__ = ['PyrexhomeCatCol', 'PyrexhomeCatalogParser']
