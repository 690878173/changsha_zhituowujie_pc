from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html
from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class KyteBabyMenuParser(CatalogParser):
    """Parse Kyte Baby's server-rendered desktop mega menu."""

    def matches(self, html):
        return 'desktop-navigation' in html and 'mega-menu__columns-wrapper' in html

    @staticmethod
    def text(node):
        values = node.xpath(
            './/text()[not(ancestor::style) and not(ancestor::script) and not(ancestor::svg)]'
        )
        return ' '.join(' '.join(values).split())

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
        menus = tree.xpath(
            '//desktop-navigation/ul[contains(concat(" ", normalize-space(@class), " "), '
            '" header__linklist ")]'
        )
        if not menus:
            raise RuntimeError('Kyte Baby desktop navigation was not found')

        result = {}
        header_urls = set()
        for item in menus[0].xpath('./li[contains(@class, "header__linklist-item")]'):
            top_links = item.xpath('./a[@href][1]')
            if not top_links:
                continue
            top_link = top_links[0]
            top_name = self.text(top_link)
            top_url = collector.normalize_url(top_link.get('href') or '')
            children = {}

            for column in item.xpath('.//div[contains(@class, "mega-menu__column")]'):
                heading_links = column.xpath('./a[@href][1]')
                heading_nodes = heading_links or column.xpath('./span[1]')
                heading_name = self.text(heading_nodes[0]) if heading_nodes else ''
                heading_href = heading_links[0].get('href') if heading_links else ''
                leaves = {}
                for link in column.xpath('./ul//a[@href]'):
                    if self.add_collection(leaves, self.text(link), link.get('href') or '', collector) is not None:
                        header_urls.add(collector.normalize_url(link.get('href') or ''))
                if heading_name and (heading_href or leaves):
                    if self.add_collection(children, heading_name, heading_href, collector, leaves) is not None:
                        if heading_href:
                            header_urls.add(collector.normalize_url(heading_href))
                else:
                    children.update(leaves)

            for link in item.xpath('.//a[contains(@class, "mega-menu__image-push")][@href]'):
                label_nodes = link.xpath('.//p[contains(@class, "mega-menu__heading")][1]')
                name = self.text(label_nodes[0]) if label_nodes else self.text(link)
                if self.add_collection(children, name, link.get('href') or '', collector) is not None:
                    header_urls.add(collector.normalize_url(link.get('href') or ''))

            if self.add_collection(result, top_name, top_link.get('href') or '', collector, children) is not None:
                if self.is_collection(top_url):
                    header_urls.add(top_url)

        other = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::desktop-navigation'):
                continue
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            if not self.is_collection(url) or url in header_urls:
                continue
            name = self.text(link) or link.get('aria-label') or urlsplit(url).path.rsplit('/', 1)[-1]
            if self.add_collection(other, name, href, collector) is not None:
                header_urls.add(url)

        if other:
            self.add_collection(result, 'Other' if 'Other' not in result else 'Other2', '', collector, other)
        if not result:
            raise RuntimeError('Kyte Baby navigation produced no collection URLs')
        return result


class KyteBabyCatCol(ShopifyCatCol):
    parser_types = (KyteBabyMenuParser,)


if __name__ == '__main__':
    try:
        KyteBabyCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        ).run()
    finally:
        Tool.close()
