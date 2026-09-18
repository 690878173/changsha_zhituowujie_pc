"""Good Clean Love homepage catalog parser."""

from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


def _text(node):
    return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())


def _is_collection(url):
    path = urlsplit(url or '').path.lower().rstrip('/')
    return (
        path.startswith('/collections/')
        and path != '/collections/all'
        and '/products/' not in path
    )


class GoodCleanLoveMenuParser(CatalogParser):
    nav_xpath = '//nav[@aria-label="Primary" and contains(@class, "main-nav")]'

    def matches(self, html):
        return 'class="main-nav"' in html and 'mega-menu__menu-title' in html

    @staticmethod
    def _key(url):
        parts = urlsplit(url)
        host = parts.netloc.lower()
        if host.startswith('www.'):
            host = host[4:]
        return host, parts.path.rstrip('/'), parts.query

    def add_collection(self, nodes, link, collector, seen):
        href = link.get('href') or ''
        normalized = collector.normalize_url(href)
        if not _is_collection(normalized):
            return False
        key = self._key(normalized)
        if key in seen:
            return False
        name = _text(link) or link.get('aria-label') or ''
        if not name:
            return False
        if name in nodes:
            name = f'{name} ({urlsplit(normalized).path.rstrip("/").rsplit("/", 1)[-1]})'
        if collector.add_node(nodes, name, href) is None:
            return False
        seen.add(key)
        return True

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('Good Clean Love homepage has no primary menu')
        result = {}
        seen = set()
        for item in navs[0].xpath('./div/ul[contains(@class, "main-nav__menu")]/li'):
            parent = item.xpath('./button[contains(@class, "main-nav__link")][1]')
            if parent:
                name = _text(parent[0])
                child = {}
                for index, column in enumerate(item.xpath('.//div[contains(@class, "mega-menu__column")]'), 1):
                    leaves = {}
                    for link in column.xpath('.//a[@href]'):
                        self.add_collection(leaves, link, collector, seen)
                    if not leaves:
                        continue
                    titles = column.xpath('.//p[contains(@class, "mega-menu__menu-title")][1]')
                    group = _text(titles[0]) if titles else f'Section {index}'
                    collector.add_node(child, group, '', leaves)
                collector.add_node(result, name, '', child)
                continue
            link = item.xpath('./a[@href][1]')
            if link:
                self.add_collection(result, link[0], collector, seen)

        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav[@aria-label="Primary"]'):
                continue
            self.add_collection(extra, link, collector, seen)
        if extra:
            collector.add_node(result, 'Other', '', extra)
        if not result:
            raise RuntimeError('Good Clean Love homepage has no collection categories')
        return result


class GoodCleanLoveCatCol(ShopifyCatCol):
    parser_types = (GoodCleanLoveMenuParser,)


__all__ = ['GoodCleanLoveCatCol', 'GoodCleanLoveMenuParser']
