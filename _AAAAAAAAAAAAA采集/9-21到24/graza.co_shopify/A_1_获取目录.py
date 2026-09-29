"""Collect Graza's server-rendered header navigation into collection paths."""

import json
from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class GrazaMenuParser(CatalogParser):
    def matches(self, html):
        return '<header-bar' in html and ':navigation=' in html

    @staticmethod
    def text(value):
        return ' '.join(str(value or '').split())

    @staticmethod
    def is_collection(url):
        return urlsplit(url or '').path.rstrip('/').lower().startswith('/collections/')

    def normalize_collection(self, href, collector):
        url = collector.normalize_url(href) if href else ''
        return url if self.is_collection(url) else ''

    def add_item(self, nodes, name, href, collector, child=None):
        url = self.normalize_collection(href, collector)
        if not name or (not url and not child):
            return None
        return collector.add_node(nodes, name, url, child)

    def add_shop_groups(self, result, navigation, collector):
        shop = next((item for item in navigation if item.get('type') == 'shop'), None)
        if not shop:
            return set()

        shop_nodes = {}
        known_urls = set()
        for entries in (shop.get('links') or {}).values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                leaves = {}
                for child in entry.get('links') or []:
                    if not isinstance(child, dict):
                        continue
                    child_url = self.normalize_collection(child.get('url'), collector)
                    child_node = self.add_item(
                        leaves, self.text(child.get('title')), child.get('url'), collector
                    )
                    if child_url and child_node is not None:
                        known_urls.add(child_url)

                entry_url = self.normalize_collection(entry.get('url'), collector)
                entry_node = self.add_item(
                    shop_nodes, self.text(entry.get('title')), entry.get('url'), collector, leaves
                )
                if entry_node is not None:
                    if entry_url:
                        known_urls.add(entry_url)

        if shop_nodes:
            self.add_item(result, self.text(shop.get('title')), '', collector, shop_nodes)
        return known_urls

    def add_mobile_collections(self, result, navigation, collector, known_urls):
        shop = next((item for item in navigation if item.get('type') == 'shop'), None)
        if not shop:
            return
        shop_nodes = result.get(self.text(shop.get('title')), {}).get('child', {})
        for entry in (shop.get('links') or {}).get('secondary', []):
            if not isinstance(entry, dict):
                continue
            url = self.normalize_collection(entry.get('url'), collector)
            mobile_node = self.add_item(
                shop_nodes, self.text(entry.get('title')), entry.get('url'), collector
            ) if url and url not in known_urls else None
            if mobile_node is not None:
                known_urls.add(url)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        header = tree.xpath("//*[local-name() = 'header-bar' and @*[name() = ':navigation']]")
        if not header:
            raise RuntimeError('Graza header navigation was not found')
        navigation = json.loads(header[0].get(':navigation'))

        result = {}
        known_urls = self.add_shop_groups(result, navigation.get('desktop') or [], collector)
        self.add_mobile_collections(result, navigation.get('mobile') or [], collector, known_urls)

        other = {}
        other_urls = set()
        for link in tree.xpath('//a[@href][not(ancestor::header-bar)]'):
            href = link.get('href') or ''
            url = self.normalize_collection(href, collector)
            if not url or url in known_urls or url in other_urls:
                continue
            name = self.text(' '.join(link.xpath('.//text()'))) or urlsplit(url).path.rsplit('/', 1)[-1]
            if self.add_item(other, name, href, collector) is not None:
                other_urls.add(url)

        if other:
            self.add_item(result, 'Other' if 'Other' not in result else 'Other2', '', collector, other)
        if not result:
            raise RuntimeError('Graza navigation produced no collection URLs')
        return result


class GrazaCatCol(ShopifyCatCol):
    parser_types = (GrazaMenuParser,)


if __name__ == '__main__':
    try:
        GrazaCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        ).run()
    finally:
        Tool.close()



