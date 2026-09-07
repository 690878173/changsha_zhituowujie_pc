"""普通 Shopify 主题的目录采集。"""

from lxml import html as lxml_html

from _ljp.mb.catalog import CatalogCollectorBase, CatalogParser, clean_text


class ShopifyThemeParser(CatalogParser):
    """解析 ``nav[data-nav-desktop]`` 主题菜单。"""

    nav_xpath = '//nav[@data-nav-desktop]'

    def matches(self, html):
        return 'data-nav-desktop' in html

    @staticmethod
    def link_text(element):
        values = element.xpath('.//text()[not(ancestor::svg)]')
        return clean_text(' '.join(values))

    def parse_links(self, links, collector, depth=1):
        result = {}
        for link in links:
            name = self.link_text(link)
            if name:
                collector.put_node(result, name, link.get('href') or '', depth=depth)
        return result

    def parse_group_list(self, menu_list, collector, result):
        for item in menu_list.xpath('./li'):
            nested = item.xpath('./ul[1]')
            heading = item.xpath('./span[1]')
            if nested and heading:
                child = self.parse_links(nested[0].xpath('./li/a[@href]'), collector, 2)
                collector.put_node(result, self.link_text(heading[0]), '', child, 1)
            elif nested:
                for link in nested[0].xpath('./li/a[@href]'):
                    name = self.link_text(link)
                    if name:
                        collector.put_node(result, name, link.get('href') or '', depth=1)
            else:
                result.update(self.parse_links(item.xpath('./a[@href]'), collector, 1))

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
                        child = self.parse_links(section.xpath('./a[@href]'), collector, 2)
                        collector.put_node(result, self.link_text(heading[0]), '', child, 1)
                elif section.tag == 'ul':
                    self.parse_group_list(section, collector, result)
        image_groups = submenu.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), " image-links ")]'
        )
        for image_group in image_groups:
            result.update(self.parse_links(image_group.xpath('./a[@href]'), collector, 1))
        return result

    def parse_menu_list(self, menu_list, collector, result):
        children = list(menu_list)
        for index, item in enumerate(children):
            if item.tag != 'li':
                continue
            # 可展开菜单的链接位于 label 内，普通菜单项直接位于 li 内。
            links = item.xpath('./a[@href] | ./label/a[@href]')
            if not links:
                continue
            link = links[0]
            name = self.link_text(link)
            child = {}
            next_class = (
                (children[index + 1].get('class') or '').split()
                if index + 1 < len(children)
                else []
            )
            if 'sub-menu' in next_class:
                child = self.parse_submenu(children[index + 1], collector)
            collector.put_node(result, name, link.get('href') or '', child, 0)

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
        values = element.xpath('.//text()[not(ancestor::svg)]')
        return clean_text(' '.join(values))

    def parse_links(self, links, collector, depth=1):
        result = {}
        for link in links:
            name = self.link_text(link)
            if name:
                collector.put_node(result, name, link.get('href') or '', depth=depth)
        return result

    def parse_child_panel(self, panel, collector):
        result = {}
        menu_lists = panel.xpath(
            './ul[contains(concat(" ", normalize-space(@class), " "), " main-menu-links ")]'
        )
        if not menu_lists:
            return result
        for item in menu_lists[0].xpath('./li'):
            item_classes = self.class_tokens(item)
            if 'has-inline-dropdown' in item_classes:
                buttons = item.xpath('./button[1]')
                nested = item.xpath(
                    './ul[contains(concat(" ", normalize-space(@class), " "), " inline-dropdown-list ")][1]'
                )
                if buttons and nested:
                    children = self.parse_links(nested[0].xpath('./li/a[@href]'), collector, 2)
                    collector.put_node(result, self.link_text(buttons[0]), '', children, 1)
                continue
            links = item.xpath('./a[@href][1]')
            if links:
                link = links[0]
                collector.put_node(result, self.link_text(link), link.get('href') or '', depth=1)
        return result

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 nav[aria-label="Primary"] 菜单')
        panels = navs[0].xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), " main-menu-panel ")]'
        )
        root_panels = [
            panel for panel in panels
            if 'main-menu-panel--child' not in self.class_tokens(panel)
        ]
        child_panels = [
            panel for panel in panels
            if 'main-menu-panel--child' in self.class_tokens(panel)
        ]
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
            collector.put_node(result, self.link_text(link), link.get('href') or '', child, 0)
        if not result:
            raise RuntimeError('Shopify 主菜单没有可用目录')
        return result


class CatalogCollector(CatalogCollectorBase):
    """普通 Shopify 自己的目录采集器。"""

    parser_types = (ShopifyThemeParser, ShopifyMainMenuParser)


def collect_catalog(tool, base_url, html_path, save_path, collector_cls=CatalogCollector):
    """使用普通 Shopify 内置解析器采集目录。"""
    return collector_cls(tool, base_url, html_path, save_path).run()


__all__ = [
    'CatalogCollector',
    'CatalogParser',
    'ShopifyThemeParser',
    'ShopifyMainMenuParser',
    'collect_catalog',
]
