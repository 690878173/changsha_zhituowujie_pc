"""Uqora homepage catalog parser."""

from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


def _text(node):
    return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())


def _is_collection(url):
    path = urlsplit(url or '').path.lower().rstrip('/')
    return path.startswith('/collections/') and path != '/collections/all' and '/products/' not in path


class UqoraMenuParser(CatalogParser):
    nav_xpath = '//nav[contains(concat(" ", normalize-space(@class), " "), " header__inline-menu ")]'

    def matches(self, html):
        return 'header__inline-menu' in html and 'HeaderMenu-products' in html

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('Uqora homepage has no header menu')
        result = {}
        seen = set()
        for link in navs[0].xpath('./ul/li/a[@href]'):
            href = link.get('href') or ''
            normalized = collector.normalize_url(href)
            if not _is_collection(normalized) or normalized in seen:
                continue
            collector.add_node(result, _text(link), href)
            seen.add(normalized)
        if not result:
            raise RuntimeError('Uqora homepage has no collection categories')

        result['Cart Recommend'] = {'url':'https://uqora.com/collections/cart-recommendations'}
        return result


class UqoraCatCol(ShopifyCatCol):
    parser_types = (UqoraMenuParser,)


__all__ = ['UqoraCatCol', 'UqoraMenuParser']
