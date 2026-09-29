from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class ArraeMenuParser(CatalogParser):
    """Parse Arrae's server-rendered header menu and page collection tiles."""

    def matches(self, html):
        return 'js-header' in html and 'tvg_nav_item_jcRWAa_nav-item' in html

    @staticmethod
    def text(node):
        values = node.xpath(
            './/text()[not(ancestor::style) and not(ancestor::script) and not(ancestor::svg)]'
        )
        return ' '.join(' '.join(values).split())

    @staticmethod
    def has_class(node, class_name):
        return class_name in (node.get('class') or '').split()

    @staticmethod
    def is_collection(url):
        return urlsplit(url or '').path.rstrip('/').lower().startswith('/collections/')

    def add_collection(self, nodes, name, href, collector, child=None):
        url = collector.normalize_url(href) if href else ''
        if url and not self.is_collection(url):
            url = ''
        if not name or (not url and not child):
            return None
        return collector.add_node(nodes, name, url, child)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        header = tree.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " js-header ")]')
        if not header:
            raise RuntimeError('页面中未找到 Arrae 导航')

        result = {}
        header_urls = set()
        nav_items = header[0].xpath(
            './/li[contains(concat(" ", normalize-space(@class), " "), '
            '" tvg_nav_item_jcRWAa_nav-item ")]'
        )
        for item in nav_items:
            top_labels = item.xpath(
                './*[contains(concat(" ", normalize-space(@class), " "), '
                '" tvg_nav_item_jcRWAa_nav-link ")]'
                '//span[contains(concat(" ", normalize-space(@class), " "), '
                '" tvg_nav_item_jcRWAa_nav-link__text ")][1]'
            )
            if not top_labels:
                continue
            top_name = self.text(top_labels[0])
            children = {}
            seen_item_urls = set()

            columns = item.xpath(
                './/*[contains(@class, "tvg_nav_collection_tiles_WlBwgG_col") '
                'or contains(@class, "tvg_nav_links_C5T6DG_col") '
                'or contains(@class, "tvg_nav_quick_links_OFlaMW_root")]'
            )
            for column in columns:
                leaves = {}
                for link in column.xpath('.//a[@href]'):
                    href = link.get('href') or ''
                    url = collector.normalize_url(href)
                    if not self.is_collection(url):
                        continue
                    name = self.text(link) or link.get('aria-label') or urlsplit(url).path.rsplit('/', 1)[-1]
                    if self.add_collection(leaves, name, href, collector) is not None:
                        header_urls.add(url)
                        seen_item_urls.add(url)

                headings = column.xpath(
                    './/*[contains(@class, "tvg_nav_collection_tiles_WlBwgG_heading") '
                    'or contains(@class, "tvg_nav_links_C5T6DG_heading")][1]'
                )
                heading = self.text(headings[0]) if headings else ''
                if heading and leaves:
                    self.add_collection(children, heading, '', collector, leaves)
                else:
                    children.update(leaves)

            for link in item.xpath('.//a[@href]'):
                href = link.get('href') or ''
                url = collector.normalize_url(href)
                if not self.is_collection(url) or url in seen_item_urls:
                    continue
                name = self.text(link) or link.get('aria-label') or urlsplit(url).path.rsplit('/', 1)[-1]
                if self.add_collection(children, name, href, collector) is not None:
                    header_urls.add(url)
                    seen_item_urls.add(url)

            if children:
                self.add_collection(result, top_name, '', collector, children)

        other = {}
        other_urls = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::*[contains(concat(" ", normalize-space(@class), " "), " js-header ")]'):
                continue
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            if not self.is_collection(url) or url in header_urls or url in other_urls:
                continue
            name = self.text(link) or link.get('aria-label') or urlsplit(url).path.rsplit('/', 1)[-1]
            if self.add_collection(other, name, href, collector) is not None:
                other_urls.add(url)

        if other:
            self.add_collection(result, 'Other' if 'Other' not in result else 'Other2', '', collector, other)
        if not result:
            raise RuntimeError('Arrae 导航未产出任何 collection')
        return result


class ArraeCatCol(ShopifyCatCol):
    parser_types = (ArraeMenuParser,)


if __name__ == '__main__':
    ArraeCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()
