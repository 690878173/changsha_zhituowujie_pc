"""阶段 1：抓取 Verb Products 的 Shopify 公开商品目录。"""

from pathlib import Path
import sys
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol


if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


class VerbMenuParser(CatalogParser):
    """解析 Verb 当前主题的 ``Shop`` 四列菜单及首页 collection 卡片。"""

    menu_xpath = (
        '//nav[@aria-label="Header Menu"]//div['
        'contains(concat(" ", normalize-space(@class), " "), '
        '" nav-header-menu-dropdown-content ")]'
    )

    def matches(self, page_html):
        return (
            'aria-label="Header Menu"' in page_html
            and 'nav-header-menu-dropdown-content' in page_html
            and 'menu-dropdown__inner-submenu' in page_html
        )

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower().rstrip('/')
        return path.startswith('/collections/') and path != '/collections'

    @staticmethod
    def handle_name(url):
        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
        return handle.replace('-', ' ').title()

    def add_collection(self, nodes, name, href, collector):
        url = collector.normalize_url(href)
        if not self.is_collection(url):
            return None
        return collector.add_node(nodes, name, url)

    def page_link_name(self, link, url):
        headings = link.xpath('.//h1[1] | .//h2[1] | .//h3[1]')
        if headings:
            name = self.text(headings[0])
            if name:
                return name

        label = ' '.join((link.get('aria-label') or '').split())
        if label and not label.lower().startswith('shop '):
            return label

        text = self.text(link)
        if text and len(text) <= 40 and text.lower() not in {'shop now', 'learn more'}:
            return text
        return self.handle_name(url)

    def parse_menu(self, menu, collector):
        shop_children = {}
        groups = menu.xpath(
            './/div[contains(concat(" ", normalize-space(@class), " "), '
            '" menu-dropdown__inner-submenu ")]'
        )
        for group in groups:
            items = group.xpath('./ul/li')
            if not items:
                continue
            heading = self.text(items[0])
            if not heading:
                continue
            leaves = {}
            for item in items[1:]:
                links = item.xpath('./a[@href][1]')
                if links:
                    link = links[0]
                    self.add_collection(leaves, self.text(link), link.get('href') or '', collector)
            if leaves:
                collector.add_node(shop_children, heading, '', leaves)
        return shop_children

    def parse_page_links(self, tree, collector):
        other = {}
        seen_urls = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav-header | ancestor::nav-drawer'):
                continue
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            if not self.is_collection(url) or url in seen_urls:
                continue
            name = self.page_link_name(link, url)
            if self.add_collection(other, name, href, collector) is not None:
                seen_urls.add(url)
        return other

    def parse(self, page_html, collector):
        tree = lxml_html.fromstring(page_html)
        menus = tree.xpath(self.menu_xpath)
        if not menus:
            raise RuntimeError('Verb homepage has no Shop menu')

        result = {}
        shop_children = self.parse_menu(menus[0], collector)
        if not shop_children:
            raise RuntimeError('Verb Shop menu has no collection groups')
        collector.add_node(result, 'Shop', '', shop_children)

        other = self.parse_page_links(tree, collector)
        if other:
            other_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, other_name, '', other)
        return result


if __name__ == '__main__':
    try:
        catalog = CatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '1' / 'homepage.html',
        )
        catalog.parser_types = (VerbMenuParser, *catalog.parser_types)
        catalog.run()
    finally:
        Tool.close()
