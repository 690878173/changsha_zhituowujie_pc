from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class LonoWearMenuParser(CatalogParser):
    nav_xpath = '//nav[contains(concat(" ", normalize-space(@class), " "), " header__link-list ")]'

    def matches(self, html):
        return 'header__link-list' in html and 'v-grid-link' in html

    @staticmethod
    def text(node):
        return ' '.join(node.xpath('.//text()[not(ancestor::svg)]')).strip()

    @staticmethod
    def is_collection(url):
        return urlsplit(url or '').path.lower().startswith('/collections/')

    def add_collection(self, nodes, link, collector):
        href = link.get('href') or ''
        name = self.text(link)
        if name and self.is_collection(href):
            return collector.add_node(nodes, name, href)
        return None

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 Lono Wear 主导航')

        result = {}
        known = set()
        for link in navs[0].xpath('.//a[@href]'):
            if self.add_collection(result, link, collector) is not None:
                known.add(collector.normalize_url(link.get('href')))

        extra = {}
        for link in tree.xpath('//main//a[@href]'):
            href = link.get('href') or ''
            normalized = collector.normalize_url(href)
            if self.is_collection(href) and normalized not in known:
                if self.add_collection(extra, link, collector) is not None:
                    known.add(normalized)
        if extra:
            collector.add_node(result, 'Other' if 'Other' not in result else 'Other2', '', extra)

        if not result:
            raise RuntimeError('Lono Wear 没有可用 collection')
        return result


class LonoWearCatCol(ShopifyCatCol):
    parser_types = (LonoWearMenuParser,)
