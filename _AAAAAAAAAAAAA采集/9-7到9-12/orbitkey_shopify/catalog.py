"""Orbitkey 首页目录解析。

Orbitkey 使用自定义主题：桌面导航是 ``ul#AccessibleNav``，顶层 ``li`` 直接是
``a.site-nav__link`` 或带 ``ul.site-nav__dropdown`` 的 mega menu。下拉里
``li.dropdown-submenu-linklist`` 是分组（标题链接在 ``p.h4`` 内），分组子项在
``ul.menu-link > li > a``；``li.dropdown-submenu-all-button`` 是 Shop All 链接；
``li.dropdown-submenu-image`` 是图片磁贴。因此目录天然是
顶层 -> 分组 -> 叶子 三级。

该结构不属于 ``_ljp.mb.shopify`` 内置的 ``header__inline-menu`` /
``data-nav-desktop`` / ``main-menu-panel`` / ``details-mega`` 任一菜单，因此在站点
``catalog.py`` 注册自己的解析器。导航栏之外的 collection 链接（页脚、首页模块
等）挂在自定义一级目录 ``Other`` 下。
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


class OrbitkeyCatalogParser(CatalogParser):
    """解析 ``#AccessibleNav`` 三级菜单，并补充导航栏之外的 collection。"""

    menu_xpath = '//ul[@id="AccessibleNav"]'
    page_group_name = 'Other'
    heading_tags = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

    def matches(self, html):
        return 'AccessibleNav' in html and 'mega-menu-wrapper' in html

    @staticmethod
    def link_text(element) -> str:
        return _clean_text(' '.join(element.xpath('.//text()[not(ancestor::svg)]')))

    def image_alt_text(self, element) -> str:
        for image in element.xpath('.//img'):
            name = _clean_text(image.get('alt'))
            if name:
                return name
        return ''

    def put_node(self, collector, nodes, name, url='', child=None):
        """只保留 collection 链接；无链接但有子级的分组继续保留。"""
        normalized_url = collector.normalize_url(url) if url else ''
        if normalized_url and not _is_collection_url(normalized_url):
            normalized_url = ''
        child = child or {}
        if not normalized_url and not child:
            return None
        return collector.add_node(nodes, name, normalized_url, child)

    def parse_leaf_list(self, menu_list, collector):
        """解析 ``ul.menu-link`` 的叶子链接。"""
        result = {}
        for item in menu_list.xpath('./li'):
            links = item.xpath('./a[@href][1]')
            if not links:
                nested = item.xpath('./ul[1]')
                if nested:
                    self.merge_children(
                        result, self.parse_leaf_list(nested[0], collector)
                    )
                continue
            link = links[0]
            name = self.link_text(link) or self.image_alt_text(link)
            if name:
                self.put_node(collector, result, name, link.get('href') or '')
        return result

    def primary_link(self, item):
        """返回一个下拉项的主链接：图片磁贴优先标题，其次按钮。"""
        for path in (
            './/*[contains(@class, "mega-menu--image-title")]//a[@href][1]',
            './/*[contains(@class, "all-product-button")]//a[@href][1]',
        ):
            links = item.xpath(path)
            if links:
                return links[0]
        links = item.xpath('.//a[@href][1]')
        return links[0] if links else None

    def parse_dropdown_item(self, item, collector, result):
        """解析一个 ``li.dropdown-submenu``：分组或单个链接。"""
        menu_lists = item.xpath('.//ul[contains(@class, "menu-link")]')
        if menu_lists:
            heads = item.xpath('.//p[contains(@class, "h4")][1]/a[@href][1]')
            if heads:
                name = self.link_text(heads[0])
                url = heads[0].get('href') or ''
            else:
                heads = item.xpath('.//p[contains(@class, "h4")][1]')
                name = self.link_text(heads[0]) if heads else ''
                url = ''
            if not name:
                return
            children = self.parse_leaf_list(menu_lists[0], collector)
            self.put_node(collector, result, name, url, children)
            return
        link = self.primary_link(item)
        if link is None:
            return
        name = (
            self.link_text(link)
            or self.image_alt_text(item)
            or _clean_text(link.get('aria-label'))
        )
        if name:
            self.put_node(collector, result, name, link.get('href') or '')

    @staticmethod
    def is_nested_submenu(item) -> bool:
        return bool(item.xpath('ancestor::li[contains(@class, "dropdown-submenu")]'))

    def parse_dropdown(self, dropdown, collector, result):
        for item in dropdown.xpath('.//li[contains(@class, "dropdown-submenu")]'):
            if self.is_nested_submenu(item):
                continue
            self.parse_dropdown_item(item, collector, result)

    def parse_top_list(self, menu, collector):
        result = {}
        for item in menu.xpath('./li'):
            links = item.xpath('./a[@href][1]')
            if not links:
                continue
            link = links[0]
            name = self.link_text(link)
            if not name:
                continue
            children = {}
            for dropdown in item.xpath('./ul[contains(@class, "site-nav__dropdown")]'):
                self.parse_dropdown(dropdown, collector, children)
            self.put_node(collector, result, name, link.get('href') or '', children)
        return result

    @staticmethod
    def merge_children(target, source):
        for name, node in source.items():
            target.setdefault(name, node)

    @staticmethod
    def known_urls(nodes, found=None):
        if found is None:
            found = set()
        for node in nodes.values():
            if node.get('url'):
                found.add(node['url'])
            OrbitkeyCatalogParser.known_urls(node.get('child') or {}, found)
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
        name = self.image_alt_text(link)
        if name:
            return name
        name = self.link_text(link)
        if name:
            return name
        return ''

    def parse_page_links(self, tree, collector, known):
        """收集导航栏之外的 collection 链接。"""
        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::ul[@id="AccessibleNav"]'):
                continue
            href = link.get('href') or ''
            if not href or href.startswith('#'):
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

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        menus = tree.xpath(self.menu_xpath)
        if not menus:
            raise RuntimeError('页面中未找到 AccessibleNav 菜单')
        result = self.parse_top_list(menus[0], collector)
        if not result:
            raise RuntimeError('AccessibleNav 没有可用目录')

        known = self.known_urls(result)
        extra = self.parse_page_links(tree, collector, known)
        if extra:
            group_name = self.page_group_name
            index = 2
            while group_name in result:
                group_name = f'{self.page_group_name}{index}'
                index += 1
            self.put_node(collector, result, group_name, '', extra)
        return result


class OrbitkeyCatCol(ShopifyCatCol):
    """Orbitkey 目录采集器。"""

    parser_types = (OrbitkeyCatalogParser,)
    skip_url_ls = []
    no_url_ls = []


__all__ = ['OrbitkeyCatCol', 'OrbitkeyCatalogParser']
