"""Collect Tatcha's public Shopify collection navigation."""

from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class TatchaShopMenuParser(CatalogParser):
    """Parse the public Shop mega menu rendered on Tatcha's homepage."""

    def matches(self, page_html):
        return 'header__primary-nav' in page_html and 'mega-menu-shop' in page_html

    @staticmethod
    def clean_name(value):
        return ' '.join(str(value or '').split()).replace(',', ' ')

    def collection_url(self, href):
        if not href or href == '#':
            return ''
        absolute_url = Tool.URL.add_site(href)
        parts = urlsplit(absolute_url)
        if parts.netloc.lower() not in {'tatcha.com', 'www.tatcha.com'}:
            return ''
        path = parts.path.rstrip('/')
        if not path.startswith('/collections/') or path == '/collections':
            return ''
        return urlunsplit((parts.scheme, parts.netloc, path, '', ''))

    def link_name(self, link, url):
        name = self.clean_name(' '.join(link.xpath('.//text()[not(ancestor::script)]')))
        if name:
            return name
        for value in (link.get('aria-label'), link.get('title'), *link.xpath('.//img/@alt')):
            name = self.clean_name(value)
            if name:
                return name
        return urlsplit(url).path.rsplit('/', 1)[-1].replace('-', ' ').title()

    def add_node(self, nodes, name, href='', child=None):
        name = self.clean_name(name)
        url = self.collection_url(href)
        child = child or {}
        if not name or (not url and not child):
            return None

        unique_name = name
        suffix = urlsplit(url).path.rsplit('/', 1)[-1] if url else 'group'
        number = 2
        while unique_name in nodes:
            existing = nodes[unique_name]
            if existing.get('url') == url:
                return existing
            unique_name = f'{name} ({suffix if number == 2 else f"{suffix} {number}"})'
            number += 1
        return self.collector.add_node(nodes, unique_name, url, child)

    def group_nodes(self, shop_item):
        groups = {}
        group_xpath = (
            './/header-mega-menu[contains(concat(" ", normalize-space(@class), " "), '
            '" mega-menu-shop ")]//div[contains(concat(" ", normalize-space(@class), " "), '
            '" mega-menu__navigation ")]/div[contains(concat(" ", normalize-space(@class), " "), '
            '" v-stack ")]'
        )
        for group in shop_item.xpath(group_xpath):
            headers = group.xpath('./a[contains(concat(" ", normalize-space(@class), " "), " bold ")]')
            if not headers:
                continue
            child = {}
            for link in group.xpath('./ul[contains(@class, "mega-menu__linklist")]//a[@href]'):
                url = self.collection_url(link.get('href'))
                if url:
                    self.add_node(child, self.link_name(link, url), link.get('href'))
            if child:
                self.add_node(groups, self.link_name(headers[0], ''), child=child)
        return groups

    @classmethod
    def known_urls(cls, nodes, result=None):
        if result is None:
            result = set()
        for node in nodes.values():
            if node.get('url'):
                result.add(node['url'])
            cls.known_urls(node.get('child') or {}, result)
        return result

    def other_nodes(self, tree, known_urls):
        other = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav | ancestor::cart-drawer'):
                continue
            url = self.collection_url(link.get('href'))
            if not url or url in known_urls:
                continue
            if self.add_node(other, self.link_name(link, url), link.get('href')):
                known_urls.add(url)
        return other

    def parse(self, page_html, collector):
        self.collector = collector
        tree = lxml_html.fromstring(page_html)
        shop_items = tree.xpath(
            '//nav[contains(concat(" ", normalize-space(@class), " "), " header__primary-nav ")]'
            '/ul[contains(concat(" ", normalize-space(@class), " "), " contents ")]'
            '/li[.//header-mega-menu[contains(concat(" ", normalize-space(@class), " "), '
            '" mega-menu-shop ")]]'
        )
        if not shop_items:
            raise RuntimeError('Tatcha Shop mega menu was not found')

        shop_item = shop_items[0]
        shop_links = shop_item.xpath('./a[contains(@href, "/collections/")]')
        if not shop_links:
            raise RuntimeError('Tatcha Shop collection link was not found')

        result = {}
        shop_url = self.collection_url(shop_links[0].get('href'))
        shop_child = self.group_nodes(shop_item)
        self.add_node(result, self.link_name(shop_links[0], shop_url), shop_links[0].get('href'), shop_child)
        if not self.known_urls(result):
            raise RuntimeError('Tatcha Shop mega menu produced no collection URLs')

        other = self.other_nodes(tree, self.known_urls(result))
        if other:
            self.add_node(result, 'Other' if 'Other' not in result else 'Other2', child=other)
        return result


if __name__ == '__main__':
    try:
        catalog = ShopifyCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        )
        catalog.parser_types = (TatchaShopMenuParser, *catalog.parser_types)
        catalog.run()
    finally:
        Tool.close()
