"""Tweezerman 首页目录解析。

Tweezerman 使用自定义主题：桌面端有两个 ``nav.header__menu``，分别是主站菜单
和宠物站菜单（位于 ``div.pet-menu``）。顶层项是 ``div.nav-item-wrapper`` /
``div.menu__item``，下拉内容在按钮内部的 ``div.header__dropdown``：侧边快捷
链接在 ``ul.left-nav-list``，分组标题是 ``a.navlink--child``，分组子项是
``a.navlink--grandchild``。宠物站菜单合并到主菜单的 ``TWEEZERMAN PET`` 分组，
导航栏之外的 collection 链接统一挂到 ``Other``。

该结构不属于 ``_ljp.mb.shopify`` 内置的 ``header__inline-menu`` /
``data-nav-desktop`` / ``details-mega`` 任一菜单，因此在站点 ``catalog.py``
注册自己的解析器。
"""

from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class TweezermanCatalogParser(CatalogParser):
    """解析主站与宠物站导航，并保留真实父子层级。"""

    nav_xpath = '//nav[contains(concat(" ", normalize-space(@class), " "), " header__menu ")]'
    pet_nav_xpath = (
        'ancestor::div[contains(concat(" ", normalize-space(@class), " "), " pet-menu ")]'
    )
    page_group_name = 'Other'
    pet_group_name = 'TWEEZERMAN PET'
    trailing_marks = ('›', '»', '→')

    def matches(self, html):
        return 'header__menu' in html and 'header__dropdown' in html

    @staticmethod
    def class_tokens(element):
        return (element.get('class') or '').split()

    def link_text(self, element, skip_button=False):
        """读取链接文本，跳过 svg 与 sr-only 文案。"""
        ignore_button = ' and not(ancestor::button)' if skip_button else ''
        text = ' '.join(
            element.xpath(
                './/text()[not(ancestor::svg)'
                ' and not(ancestor::*[contains(concat(" ", normalize-space(@class), " "),'
                ' " sr-only ")])'
                f'{ignore_button}]'
            )
        )
        text = ' '.join(text.split())
        for mark in self.trailing_marks:
            if text.endswith(mark):
                text = text[:-len(mark)].rstrip()
        return text

    @staticmethod
    def is_collection_url(url):
        path = urlsplit(url or '').path.lower()
        return '/collections' in path and '/product' not in path

    def put_node(self, collector, nodes, name, url='', child=None):
        """只保留 collection 链接，无链接但有子级的分组继续保留。"""
        normalized = collector.normalize_url(url) if url else ''
        if normalized and not self.is_collection_url(normalized):
            normalized = ''
        return collector.add_node(nodes, name, normalized, child)

    # ---- 下拉菜单 ----

    def parse_family(self, family, collector, nodes):
        """解析一个 ``dropdown__family`` 分组。"""
        children = {}
        for link in family.xpath('./a[contains(@class, "navlink--grandchild")]'):
            self.put_node(collector, children, self.link_text(link), link.get('href') or '')
        heads = family.xpath('./a[contains(@class, "navlink--child")]')
        if not heads:
            # 图片分组没有标题，子级提升到当前层级
            for name, node in children.items():
                nodes.setdefault(name, node)
            return
        self.put_node(
            collector,
            nodes,
            self.link_text(heads[0]),
            heads[0].get('href') or '',
            children,
        )

    def parse_dropdown(self, dropdown, collector):
        """解析下拉内容：分组、分组标题链接和侧边快捷链接。"""
        children = {}
        for inner in dropdown.xpath('.//div[contains(@class, "header__dropdown__inner")]'):
            for block in inner:
                if block.tag == 'div' and 'dropdown__family' in self.class_tokens(block):
                    self.parse_family(block, collector, children)
            for link in inner.xpath('./a[contains(@class, "navlink--child")]'):
                self.put_node(collector, children, self.link_text(link), link.get('href') or '')
        for link in dropdown.xpath('.//ul[contains(@class, "left-nav-list")]/li/a[@href]'):
            self.put_node(collector, children, self.link_text(link), link.get('href') or '')
        return children

    def menu_items(self, nav, collector):
        """返回一个 ``nav.header__menu`` 的顶层目录项。"""
        items = []
        for item in nav.xpath('./div[contains(@class, "header__menu__inner")]/div'):
            links = item.xpath('./a[@href][1]')
            if not links:
                continue
            link = links[0]
            # 顶层链接里的下拉开关按钮文案不属于目录名
            name = self.link_text(link, skip_button=True)
            if not name:
                continue
            dropdowns = item.xpath('.//div[contains(@class, "header__dropdown")]')
            child = self.parse_dropdown(dropdowns[0], collector) if dropdowns else {}
            items.append((name, link.get('href') or '', child))
        return items

    # ---- 宠物站菜单 ----

    @staticmethod
    def merge_children(target, source):
        for name, node in source.items():
            if name in target:
                existing = target[name]
                TweezermanCatalogParser.merge_children(existing['child'], node['child'])
                # 宠物站菜单里的分组链接更完整，用它覆盖主菜单里的简写链接
                if node.get('url'):
                    existing['url'] = node['url']
            else:
                target[name] = node

    def attach_pet_menu(self, collector, result, items):
        """把宠物站菜单合并到 ``TWEEZERMAN PET`` 分组下。"""
        node = result.get(self.pet_group_name)
        if node is None:
            self.put_node(collector, result, self.pet_group_name)
            node = result.get(self.pet_group_name)
        if node is None:
            return
        for name, url, child in items:
            if collector.normalize_url(url) == node['url']:
                # 宠物站 SHOP 与 TWEEZERMAN PET 同址，只合并其子级
                self.merge_children(node['child'], child)
                continue
            self.put_node(collector, node['child'], name, url, child)

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
        heads = link.xpath('./h1 | ./h2 | ./h3 | ./h4 | ./h5 | ./h6')
        for head in heads:
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
            if link.xpath('ancestor::nav'):
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
        menus = tree.xpath(self.nav_xpath)
        if not menus:
            raise RuntimeError('页面中未找到 header__menu 导航')

        result = {}
        pet_items = []
        for nav in menus:
            items = self.menu_items(nav, collector)
            if nav.xpath(self.pet_nav_xpath):
                pet_items = items
                continue
            for name, url, child in items:
                self.put_node(collector, result, name, url, child)
        if pet_items:
            self.attach_pet_menu(collector, result, pet_items)
        if len(result) < 2:
            raise RuntimeError('首页导航没有多个可用的分类分组')

        extra = self.parse_page_links(tree, collector, self.known_urls(result))
        if extra:
            group_name = self.page_group_name
            index = 2
            while group_name in result:
                group_name = f'{self.page_group_name}{index}'
                index += 1
            self.put_node(collector, result, group_name, '', extra)


        dic = {'Award':'https://tweezerman.com/collections/award-winning-classics'}

        result['Other']['child'].update({'Award':'https://tweezerman.com/collections/award-winning-classics'})
        return result


class TweezermanCatCol(ShopifyCatCol):
    """Tweezerman 目录采集器。"""

    parser_types = (TweezermanCatalogParser,)
    skip_url_ls = []
    no_url_ls = []


__all__ = ['TweezermanCatCol', 'TweezermanCatalogParser']
