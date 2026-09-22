from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class MaryRuthMenuParser(CatalogParser):
    """Parse MaryRuth's custom header mega menu."""

    def matches(self, html):
        return 'class="header__menu' in html and 'class="mega-menu__column"' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower().rstrip('/')
        return path.startswith('/collections/') and '/products/' not in path

    @staticmethod
    def unique_name(nodes, name, url):
        if name not in nodes:
            return name
        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1] or 'collection'
        candidate = f'{name} ({handle})'
        number = 2
        while candidate in nodes:
            candidate = f'{name} ({handle}) {number}'
            number += 1
        return candidate

    def add_collection(self, nodes, name, href, collector):
        url = collector.normalize_url(href)
        if not name or not self.is_collection(url):
            return False
        name = self.unique_name(nodes, name, url)
        return collector.add_node(nodes, name, url) is not None

    def parse_mega_menu(self, menu, collector):
        result = {}

        featured = {}
        for link in menu.xpath(
            './/*[contains(concat(" ", normalize-space(@class), " "), " mega-menu__featured-item ")][@href]'
        ):
            name_node = link.xpath('.//strong[1]')
            name = self.text(name_node[0]) if name_node else self.text(link)
            self.add_collection(featured, name, link.get('href') or '', collector)
        if featured:
            collector.add_node(result, 'FEATURED', '', featured)

        for column in menu.xpath(
            './/*[contains(concat(" ", normalize-space(@class), " "), " mega-menu__column ")]'
        ):
            title_nodes = column.xpath(
                './*[contains(concat(" ", normalize-space(@class), " "), " mega-menu__title ")][1]'
            )
            title = self.text(title_nodes[0]) if title_nodes else ''
            child = {}
            for link in column.xpath('.//a[@href]'):
                self.add_collection(child, self.text(link), link.get('href') or '', collector)
            if title and child:
                collector.add_node(result, title, '', child)

        footer = {}
        for link in menu.xpath(
            './/*[contains(concat(" ", normalize-space(@class), " "), " mega-menu__footer ")]//a[@href]'
        ):
            self.add_collection(footer, self.text(link), link.get('href') or '', collector)
        if footer:
            collector.add_node(result, 'ALL', '', footer)

        return result

    def parse_page_links(self, tree, collector, known_urls):
        result = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header | ancestor::nav | ancestor::footer'):
                continue
            url = collector.normalize_url(link.get('href') or '')
            if not self.is_collection(url) or url in known_urls:
                continue
            name = self.text(link) or urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            if self.add_collection(result, name, url, collector):
                known_urls.add(url)
        return result

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        result = {}
        known_urls = set()

        menus = tree.xpath('//ul[contains(concat(" ", normalize-space(@class), " "), " header__menu ")]')
        if not menus:
            raise RuntimeError('MaryRuth header menu not found')

        shop_items = menus[-1].xpath(
            './li[./div[@data-mega-main-menu="shop"]'
            ' and ./div[@data-mega-menu="shop"]]'
        )
        if not shop_items:
            raise RuntimeError('MaryRuth Shop mega menu not found')

        item = shop_items[0]
        menu = item.xpath('./div[@data-mega-menu="shop"][1]')[0]
        name_nodes = item.xpath('./div[@data-mega-main-menu="shop"]/button[1]')
        name = self.text(name_nodes[0]) if name_nodes else 'Shop'
        child = self.parse_mega_menu(menu, collector)
        if child:
            collector.add_node(result, name, '', child)
            known_urls.update(
                collector.normalize_url(link.get('href') or '')
                for link in menu.xpath('.//a[@href]')
                if self.is_collection(collector.normalize_url(link.get('href') or ''))
            )

        other = self.parse_page_links(tree, collector, known_urls)
        if other:
            collector.add_node(result, 'Other' if 'Other' not in result else 'Other2', '', other)

        if not result:
            raise RuntimeError('MaryRuth menu did not yield collection links')
        return result


class MaryRuthCatCol(ShopifyCatCol):
    parser_types = (MaryRuthMenuParser,)


if __name__ == '__main__':
    MaryRuthCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()

