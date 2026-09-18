"""Kerasal 首页目录解析。

Kerasal 使用自定义 Shopify 主题：桌面导航是 ``ul.menu.list-unstyled``，每个
``li`` 里是 ``<a class="menu-item">``；带子级的分组用 ``mega-menu-horizontal``
包裹，卡片链接位于 ``div.mega-menu-horizontal__inner`` 的 promotion 区块中，
卡片名称写在 ``div.font-navigation`` 里。移动端抽屉和促销图片只是同一份菜单的
镜像，导航栏之外的 collection 链接统一挂到 ``Other``。

该结构不属于 ``_ljp.mb.shopify`` 内置的 ``header__inline-menu`` /
``data-nav-desktop`` / ``details-mega`` 任一菜单，因此在站点 ``catalog.py``
注册自己的解析器。
"""

from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class KerasalCatalogParser(CatalogParser):
    """解析 Kerasal 桌面导航，并保留分组层级。"""

    menu_xpath = (
        '//ul[contains(concat(" ", normalize-space(@class), " "), " menu ")]'
        '[contains(concat(" ", normalize-space(@class), " "), " list-unstyled ")]'
    )
    dropdown_xpath = './/div[contains(@class, "mega-menu-horizontal__inner")]'
    page_group_name = 'Other'

    def matches(self, html):
        return 'list-unstyled' in html and 'mega-menu-horizontal' in html

    @staticmethod
    def is_collection_url(url):
        path = urlsplit(url or '').path.lower()
        return '/collections' in path and '/product' not in path

    def link_text(self, element):
        """读取链接文本，跳过 svg 图标文案。"""
        text = ' '.join(element.xpath('.//text()[not(ancestor::svg)]'))
        return ' '.join(text.split())

    def put_node(self, collector, nodes, name, url='', child=None):
        """只保留 collection 链接，无链接但有子级的分组继续保留。"""
        normalized = collector.normalize_url(url) if url else ''
        if normalized and not self.is_collection_url(normalized):
            normalized = ''
        return collector.add_node(nodes, name, normalized, child)

    def parse_dropdown(self, item, collector):
        """解析一个 ``li`` 的 mega menu 卡片链接。"""
        children = {}
        for inner in item.xpath(self.dropdown_xpath):
            for link in inner.xpath('.//a[@href]'):
                self.put_node(
                    collector,
                    children,
                    self.link_text(link),
                    link.get('href') or '',
                )
        return children

    def menu_items(self, nav, collector):
        """返回顶层目录项 ``(名称, URL, 子级)``。"""
        items = []
        for item in nav.xpath('./li'):
            links = item.xpath('.//a[contains(@class, "menu-item")][1]')
            if not links:
                continue
            link = links[0]
            name = self.link_text(link)
            if not name:
                continue
            items.append((name, link.get('href') or '', self.parse_dropdown(item, collector)))
        return items

    # ---- 导航栏之外的 collection 链接 ----

    def known_urls(self, nodes, found=None):
        if found is None:
            found = set()
        for node in nodes.values():
            if node.get('url'):
                found.add(node['url'])
            self.known_urls(node.get('child') or {}, found)
        return found

    def page_link_name(self, link):
        for head in link.xpath('./h1 | ./h2 | ./h3 | ./h4 | ./h5 | ./h6'):
            name = self.link_text(head)
            if name:
                return name
        for attr in ('aria-label', 'title'):
            name = ' '.join((link.get(attr) or '').split())
            if name:
                return name
        return self.link_text(link)

    def parse_page_links(self, tree, collector, known):
        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::ul[contains(concat(" ", normalize-space(@class), " "),'
                          ' " list-unstyled ")]'):
                continue
            href = link.get('href') or ''
            if not href or href.startswith('#'):
                continue
            url = collector.normalize_url(href)
            if not url or url in known or not self.is_collection_url(url):
                continue
            if urlsplit(url).path.rstrip('/').endswith('/collections'):
                continue
            if self.put_node(collector, extra, self.page_link_name(link), href) is not None:
                known.add(url)
        return extra

    # ---- 入口 ----

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        menus = tree.xpath(self.menu_xpath)
        if not menus:
            raise RuntimeError('页面中未找到 ul.menu.list-unstyled 导航')

        result = {}
        for name, url, child in self.menu_items(menus[0], collector):
            self.put_node(collector, result, name, url, child)
        if not result:
            raise RuntimeError('首页导航没有可用的分类分组')

        extra = self.parse_page_links(tree, collector, self.known_urls(result))
        if extra:
            group_name = self.page_group_name
            index = 2
            while group_name in result:
                group_name = f'{self.page_group_name}{index}'
                index += 1
            self.put_node(collector, result, group_name, '', extra)
        return result


class KerasalCatCol(ShopifyCatCol):
    """Kerasal 目录采集器。"""

    parser_types = (KerasalCatalogParser,)
    skip_url_ls = []
    no_url_ls = []


__all__ = ['KerasalCatCol', 'KerasalCatalogParser']
