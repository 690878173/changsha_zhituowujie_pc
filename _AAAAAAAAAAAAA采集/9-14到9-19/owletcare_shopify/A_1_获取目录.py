"""Collect Owlet's public collection catalog."""

from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol


save_path = Tool.File.path_add_site('data/ml.json')


def _text(node):
    return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())


def _is_collection(url):
    path = urlsplit(url or '').path.lower().rstrip('/')
    return path.startswith('/collections/') and '/products/' not in path


class OwletMenuParser(CatalogParser):
    """Read menu collections and explicitly supplied public collections."""

    extra_collections = (
        ('Owlet', '/collections/owlet'),
        ('Accessories', '/collections/accessories'),
        ('Main Products', '/collections/main-products'),
        ('All Products', '/collections/all-products'),
        ('Shop All', '/collections/all'),
        ('Best Selling Products', '/collections/best-selling-products'),
        ('Newest Products', '/collections/newest-products'),
        ('All 1', '/collections/all-1'),
        ('O-com Products', '/collections/o-com-products'),
        ('Foundation Products', '/collections/foundation-products'),
        ('Briggs and Barret Foundations Products', '/collections/briggs-and-barret-foundations-products'),
        ('Foundations', '/collections/foundations'),
        ('Cam Test', '/collections/cam-test'),
        ('Sock Shop', '/collections/sock-shop'),
        ('B2B', '/collections/b2b'),
        ('Active Products', '/collections/active-products'),
        ('Homepage', '/collections/homepage'),
        ('Monitors', '/collections/monitors'),
        ('All Products 1', '/collections/all-products-1'),
        ('Prime Day', '/collections/prime-day'),
        ('The Give Back Shop', '/collections/the-give-back-shop'),
        ('Black Friday Cyber Monday Sale', '/collections/black-friday-cyber-monday-sale'),
        ('Shop', '/collections/shop'),
        ("Mother's Day", '/collections/mothers-day'),
        ("Father's Day", '/collections/fathers-day'),
        ('CPAP Shop', '/collections/cpap-shop'),
        ('Labor Day', '/collections/labor-day'),
    )

    def matches(self, html):
        return 'xo-menu-horizontal' in html and '/collections/' in html

    @staticmethod
    def _key(url):
        parts = urlsplit(url)
        host = parts.netloc.lower().removeprefix('www.')
        return host, parts.path.rstrip('/'), parts.query

    def _add(self, nodes, name, href, collector, seen):
        normalized = collector.normalize_url(href)
        if not _is_collection(normalized):
            return False
        key = self._key(normalized)
        if key in seen or not name:
            return False
        if collector.add_node(nodes, name, href) is None:
            return False
        seen.add(key)
        return True

    def _add_link(self, nodes, link, collector, seen):
        return self._add(
            nodes,
            _text(link) or link.get('aria-label') or '',
            link.get('href') or '',
            collector,
            seen,
        )

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(
            '//nav[contains(concat(" ", normalize-space(@class), " "), " xo-header__center ")]'
        )
        mega_menus = tree.xpath(
            '//div[contains(concat(" ", normalize-space(@class), " "), " mega-menu-1__desktop ")]'
        )
        if not navs or not mega_menus:
            raise RuntimeError('Owlet homepage has no desktop navigation')

        result = {}
        shop = {}
        shop_seen = set()
        for link in mega_menus[0].xpath('.//a[@href]'):
            self._add_link(shop, link, collector, shop_seen)
        if shop:
            collector.add_node(result, 'Shop', '', shop)

        other = {}
        other_seen = set()
        for name, href in self.extra_collections:
            self._add(other, name, href, collector, other_seen)
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav') or link.xpath(
                'ancestor::*[contains(concat(" ", normalize-space(@class), " "), " mega-menu-1 ")]'
            ):
                continue
            self._add_link(other, link, collector, other_seen)
        if other:
            collector.add_node(result, 'Other', '', other)

        if not shop and not other:
            raise RuntimeError('Owlet homepage has no collection categories')
        return result


M = CatCol(Tool, base_url, save_path)
M.parser_types = (OwletMenuParser,)


if __name__ == '__main__':
    M.run()
