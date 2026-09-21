from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class RuffwearMenuParser(CatalogParser):
    """Parse Ruffwear's desktop Shop mega menu and collection cards."""

    def matches(self, html):
        return 'data-drawer="drawer-megamenu-1"' in html and 'class="subnav__links"' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower().rstrip('/')
        return path.startswith('/collections/') and '/products/' not in path

    def add_collection(self, nodes, name, href, collector):
        url = collector.normalize_url(href)
        if not name or not self.is_collection(url):
            return False
        return collector.add_node(nodes, name, url) is not None

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        result = {}
        known_urls = set()

        menu = tree.xpath('//header//div[@data-drawer="drawer-megamenu-1"][1]')
        if not menu:
            raise RuntimeError('Ruffwear Shop mega menu not found')

        shop_children = {}
        for group in menu[0].xpath(
            './/div[contains(concat(" ", normalize-space(@class), " "), " link-list ")]'
        ):
            title_nodes = group.xpath('./h2[1]')
            title = self.text(title_nodes[0]) if title_nodes else ''
            children = {}
            for link in group.xpath('./ul/li/a[@href]'):
                if self.add_collection(children, self.text(link), link.get('href') or '', collector):
                    known_urls.add(collector.normalize_url(link.get('href') or ''))
            if title and children:
                collector.add_node(shop_children, title, '', children)

        if shop_children:
            collector.add_node(result, 'Shop', '', shop_children)

        other = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header | ancestor::nav | ancestor::footer'):
                continue
            url = collector.normalize_url(link.get('href') or '')
            if url in known_urls or not self.is_collection(url):
                continue
            name = self.text(link) or urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            if self.add_collection(other, name, link.get('href') or '', collector):
                known_urls.add(url)

        if other:
            collector.add_node(result, 'Other' if 'Other' not in result else 'Other2', '', other)
        if not result:
            raise RuntimeError('Ruffwear navigation did not yield collection links')
        return result


class RuffwearCatCol(ShopifyCatCol):
    parser_types = (RuffwearMenuParser,)


if __name__ == '__main__':
    RuffwearCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()



