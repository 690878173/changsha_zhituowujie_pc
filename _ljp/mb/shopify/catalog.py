"""普通 Shopify 首页目录解析。"""

from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser, CatCol as BaseCatCol


def _clean_text(value):
    text = ' '.join(str(value or '').split())
    for suffix in (' ->', ' >'):
        if text.endswith(suffix):
            text = text[:-len(suffix)].rstrip()
    return text


def _is_collection_url(url):
    path = urlsplit(url or '').path.lower()
    return '/collections' in path and '/product' not in path


def _put_node(collector, nodes, name, url='', child=None):
    """保留分组节点，只有 collection 链接写入目录结果。"""
    normalized_url = collector.normalize_url(url) if url else ''
    if normalized_url and not _is_collection_url(normalized_url):
        normalized_url = ''
    return collector.add_node(nodes, name, normalized_url, child)


class ShopifyThemeParser(CatalogParser):
    """解析 ``nav[data-nav-desktop]`` 主题菜单。"""

    nav_xpath = '//nav[@data-nav-desktop]'

    def matches(self, html):
        return 'data-nav-desktop' in html

    @staticmethod
    def link_text(element):
        return _clean_text(' '.join(element.xpath('.//text()[not(ancestor::svg)]')))

    def parse_links(self, links, collector):
        result = {}
        for link in links:
            name = self.link_text(link)
            if name:
                _put_node(collector, result, name, link.get('href') or '')
        return result

    def parse_group_list(self, menu_list, collector, result):
        for item in menu_list.xpath('./li'):
            nested = item.xpath('./ul[1]')
            heading = item.xpath('./span[1]')
            if nested and heading:
                child = self.parse_links(nested[0].xpath('./li/a[@href]'), collector)
                _put_node(collector, result, self.link_text(heading[0]), '', child)
            elif nested:
                for link in nested[0].xpath('./li/a[@href]'):
                    name = self.link_text(link)
                    if name:
                        _put_node(collector, result, name, link.get('href') or '')
            else:
                for link in item.xpath('./a[@href]'):
                    name = self.link_text(link)
                    if name:
                        _put_node(collector, result, name, link.get('href') or '')

    def parse_submenu(self, submenu, collector):
        result = {}
        columns = submenu.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), " column ")]'
        )
        for column in columns:
            for section in column.xpath('./*'):
                section_class = (section.get('class') or '').split()
                if 'nav-height-grid' in section_class:
                    heading = section.xpath('./span[1]')
                    if heading:
                        child = self.parse_links(section.xpath('./a[@href]'), collector)
                        _put_node(collector, result, self.link_text(heading[0]), '', child)
                elif section.tag == 'ul':
                    self.parse_group_list(section, collector, result)
        for image_group in submenu.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), " image-links ")]'
        ):
            for link in image_group.xpath('./a[@href]'):
                name = self.link_text(link)
                if name:
                    _put_node(collector, result, name, link.get('href') or '')
        return result

    def parse_menu_list(self, menu_list, collector, result):
        children = list(menu_list)
        for index, item in enumerate(children):
            if item.tag != 'li':
                continue
            links = item.xpath('./a[@href] | ./label/a[@href]')
            if not links:
                continue
            link = links[0]
            child = {}
            next_class = (
                (children[index + 1].get('class') or '').split()
                if index + 1 < len(children)
                else []
            )
            if 'sub-menu' in next_class:
                child = self.parse_submenu(children[index + 1], collector)
            _put_node(collector, result, self.link_text(link), link.get('href') or '', child)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 nav[data-nav-desktop] 菜单')
        result = {}
        for menu_list in navs[0].xpath('./ul'):
            self.parse_menu_list(menu_list, collector, result)
        if not result:
            raise RuntimeError('Shopify 主题菜单没有可用目录')
        return result


class ShopifyMainMenuParser(CatalogParser):
    """解析 ``main-menu-panel`` 多层主题菜单。"""

    nav_xpath = '//nav[@aria-label="Primary"]'

    def matches(self, html):
        return 'aria-label="Primary"' in html and 'main-menu-panel' in html

    @staticmethod
    def class_tokens(element):
        return (element.get('class') or '').split()

    @staticmethod
    def link_text(element):
        return _clean_text(' '.join(element.xpath('.//text()[not(ancestor::svg)]')))

    def parse_links(self, links, collector):
        result = {}
        for link in links:
            name = self.link_text(link)
            if name:
                _put_node(collector, result, name, link.get('href') or '')
        return result

    def parse_child_panel(self, panel, collector):
        result = {}
        menu_lists = panel.xpath(
            './ul[contains(concat(" ", normalize-space(@class), " "), " main-menu-links ")]'
        )
        if not menu_lists:
            return result
        for item in menu_lists[0].xpath('./li'):
            if 'has-inline-dropdown' in self.class_tokens(item):
                buttons = item.xpath('./button[1]')
                nested = item.xpath(
                    './ul[contains(concat(" ", normalize-space(@class), " "), " inline-dropdown-list ")][1]'
                )
                if buttons and nested:
                    child = self.parse_links(nested[0].xpath('./li/a[@href]'), collector)
                    _put_node(collector, result, self.link_text(buttons[0]), '', child)
                continue
            links = item.xpath('./a[@href][1]')
            if links:
                link = links[0]
                _put_node(collector, result, self.link_text(link), link.get('href') or '')
        return result

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 nav[aria-label="Primary"] 菜单')
        panels = navs[0].xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), " main-menu-panel ")]'
        )
        root_panels = [panel for panel in panels if 'main-menu-panel--child' not in self.class_tokens(panel)]
        child_panels = [panel for panel in panels if 'main-menu-panel--child' in self.class_tokens(panel)]
        if not root_panels:
            raise RuntimeError('页面中未找到 Shopify 主菜单面板')
        root_lists = root_panels[0].xpath(
            './ul[contains(concat(" ", normalize-space(@class), " "), " main-menu-links ")]'
        )
        if not root_lists:
            raise RuntimeError('Shopify 主菜单面板没有菜单项')

        result = {}
        child_index = 0
        for item in root_lists[0].xpath('./li'):
            links = item.xpath('./a[@href][1]')
            if not links:
                continue
            link = links[0]
            child = {}
            if 'has-children' in self.class_tokens(item) and child_index < len(child_panels):
                child = self.parse_child_panel(child_panels[child_index], collector)
                child_index += 1
            _put_node(collector, result, self.link_text(link), link.get('href') or '', child)
        if not result:
            raise RuntimeError('Shopify 主菜单没有可用目录')
        return result


class HeaderInlineMenuParser(CatalogParser):
    """解析 Dawn 系 ``header__inline-menu`` 三层菜单。"""

    menu_xpath = '//nav[contains(concat(" ", normalize-space(@class), " "), " header__inline-menu ")]'

    def matches(self, html):
        return 'header__inline-menu' in html

    @staticmethod
    def text(node, xpath):
        return _clean_text(' '.join(node.xpath(xpath)))

    def parse_leaf_nodes(self, nodes, collector):
        result = {}
        for node in nodes:
            links = node.xpath('./a[@href][1]')
            if not links:
                continue
            link = links[0]
            name = _clean_text(' '.join(link.xpath('.//text()[not(ancestor::svg)]')))
            if name:
                _put_node(collector, result, name, link.get('href') or '')
        return result

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        menus = tree.xpath(self.menu_xpath)
        if not menus:
            raise RuntimeError('页面中未找到 header__inline-menu 菜单')
        result = {}
        for details in menus[0].xpath('./ul/li/header-menu/details'):
            name = self.text(details, './summary/span//text()')
            if not name:
                continue
            child = {}
            for group in details.xpath('./div/ul/li'):
                group_name = self.text(group, './span//text()')
                leaves = self.parse_leaf_nodes(group.xpath('./ul/li'), collector)
                if group_name:
                    _put_node(collector, child, group_name, '', leaves)
                else:
                    for leaf_name, leaf in leaves.items():
                        _put_node(collector, child, leaf_name, leaf['url'], leaf['child'])
            _put_node(collector, result, name, '', child)
        if not result:
            raise RuntimeError('header__inline-menu 没有可用目录')
        return result


class MegaMenuDetailsParser(CatalogParser):
    """解析 ``nav[aria-label="Primary"]`` 里 ``details[is="details-mega"]`` 的 mega menu。

    顶层是 ``summary`` 中的菜单名，展开层里每个 ``li`` 是一个分组，分组可以继续
    通过 ``ul/li`` 下钻。``mega-menu__shop_all`` 容器只代表上一级的 Shop All
    链接，它自身不成节点，子级提升到上一级，因此目录最多三级。只保留
    collection 链接，无链接但有子级的分组保留。导航栏之外的 collection 链接
    （首页卡片、抽屉等）统一挂到 ``page_group_name`` 这个自定义一级目录下。
    """

    nav_xpath = '//nav[@aria-label="Primary"]'
    item_list_xpath = (
        './/ul[contains(concat(" ", normalize-space(@class), " "), " mega-menu__list ")]/li'
    )
    shop_all_xpath = (
        './div[contains(concat(" ", normalize-space(@class), " "), " mega-menu__shop_all ")]'
        '//a[@href]'
    )
    heading_class_xpath = 'contains(concat(" ", normalize-space(@class), " "), " heading ")'
    page_group_name = 'Other'

    def matches(self, html):
        return (
            'aria-label="Primary"' in html
            and 'details-mega' in html
            and 'mega-menu__list' in html
        )

    @staticmethod
    def link_text(element):
        """读取链接文本，跳过主题用于 hover 动画的 ``btn-duplicate`` 副本。"""
        return _clean_text(
            ' '.join(
                element.xpath(
                    './/text()[not(ancestor::svg)'
                    ' and not(ancestor::*[contains(concat(" ", normalize-space(@class), " "),'
                    ' " btn-duplicate ")])]'
                )
            )
        )

    def group_heading(self, node):
        """读取 ``li`` 自身的 ``h2`` 标题，返回 ``(名称, 链接)``。"""
        heads = node.xpath('./h2[1]')
        if not heads:
            return '', ''
        links = heads[0].xpath('./a[@href][1]')
        if links:
            return self.link_text(links[0]), links[0].get('href') or ''
        return self.link_text(heads[0]), ''

    def parse_groups(self, nodes, collector):
        """递归解析同一层级的分组节点。"""
        result = {}
        for node in nodes:
            if node.tag != 'li':
                continue
            child = self.parse_groups(node.xpath('./ul[1]/li'), collector)
            shop_all = node.xpath(self.shop_all_xpath)
            name, url = self.group_heading(node)
            if not name and shop_all:
                # Shop All 容器：链接归上一级，子级提升到当前层级
                for child_name, child_node in child.items():
                    result.setdefault(child_name, child_node)
                continue
            if not name:
                links = node.xpath('./a[@href][1]')
                if links:
                    name = self.link_text(links[0])
                    url = links[0].get('href') or ''
            _put_node(collector, result, name, url, child)
        return result

    def page_link_name(self, link):
        """首页卡片优先用标题，其次 ``aria-label``，最后回退到链接文本。"""
        heads = link.xpath(f'.//span[{self.heading_class_xpath}][1]')
        if heads:
            name = self.link_text(heads[0])
            if name:
                return name
        label = _clean_text(link.get('aria-label'))
        if label:
            return label
        return self.link_text(link)

    @staticmethod
    def collect_urls(nodes, found=None):
        """收集目录树里已经出现的绝对链接。"""
        if found is None:
            found = set()
        for node in nodes.values():
            url = node.get('url')
            if url:
                found.add(url)
            MegaMenuDetailsParser.collect_urls(node.get('child') or {}, found)
        return found

    def parse_page_links(self, tree, collector, known):
        """收集导航栏之外的 collection 链接。"""
        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav[@aria-label="Primary"]'):
                continue
            href = link.get('href') or ''
            if not href or href.startswith('#'):
                continue
            url = collector.normalize_url(href)
            if not url or url in known or not _is_collection_url(url):
                continue
            if urlsplit(url).path.rstrip('/').endswith('/collections'):
                continue
            if _put_node(collector, extra, self.page_link_name(link), href) is not None:
                known.add(url)
        return extra

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 nav[aria-label="Primary"] 菜单')
        result = {}
        for item in navs[0].xpath('./ul/li'):
            details = item.xpath('./details[1]')
            if not details:
                links = item.xpath('./a[@href][1]')
                if links:
                    _put_node(collector, result, self.link_text(links[0]), links[0].get('href') or '')
                continue
            detail = details[0]
            names = detail.xpath(
                './summary//span[contains(concat(" ", normalize-space(@class), " "), " btn-text ")][1]'
            )
            shop_all = detail.xpath(
                './/div[contains(concat(" ", normalize-space(@class), " "), " mega-menu__shop_all ")]'
                '//a[@href][1]'
            )
            _put_node(
                collector,
                result,
                self.link_text(names[0]) if names else '',
                shop_all[0].get('href') if shop_all else '',
                self.parse_groups(detail.xpath(self.item_list_xpath), collector),
            )
        if not result:
            raise RuntimeError('Primary mega menu 没有可用目录')
        extra = self.parse_page_links(tree, collector, self.collect_urls(result))
        if extra:
            _put_node(collector, result, self.page_group_name, '', extra)
        return result


class CatCol(BaseCatCol):
    """普通 Shopify 目录采集器。"""

    parser_types = (
        HeaderInlineMenuParser,
        ShopifyThemeParser,
        ShopifyMainMenuParser,
        MegaMenuDetailsParser,
    )
    skip_url_ls = []
    no_url_ls = []


__all__ = [
    'CatCol',
    'HeaderInlineMenuParser',
    'MegaMenuDetailsParser',
    'ShopifyMainMenuParser',
    'ShopifyThemeParser',
]
