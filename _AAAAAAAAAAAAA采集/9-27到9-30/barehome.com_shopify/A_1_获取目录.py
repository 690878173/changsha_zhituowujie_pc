from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import base_url, Tool
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


save_path = Tool.File.path_add_site('data/ml.json')


class BareHomeMenuParser(CatalogParser):
    """Parse Bare Home's server-rendered three-level mega menu."""

    def matches(self, html):
        return 'header__inline-menu' in html and 'mega-menu__list' in html

    @staticmethod
    def text(node):
        text = ' '.join(' '.join(node.xpath(
            './/text()[not(ancestor::svg) and not(ancestor::*[contains(@class, "mega-menu__sale-badge")])]'
        )).split())
        return text.replace('\u2122', '').strip()

    @staticmethod
    def is_collection(url):
        return urlsplit(url or '').path.rstrip('/').lower().startswith('/collections/')

    def collection_url(self, href, collector):
        url = collector.normalize_url(href) if href else ''
        return url if self.is_collection(url) else ''

    def add_node(self, nodes, name, href, collector, child=None):
        url = self.collection_url(href, collector)
        if not name or (not url and not child):
            return None
        return collector.add_node(nodes, name, url, child)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        nav = tree.xpath('//nav[contains(@class, "header__inline-menu")]')
        if not nav:
            raise RuntimeError('Bare Home desktop navigation was not found')

        result = {}
        known_urls = set()
        for link in tree.xpath('//nav//a[@href]'):
            url = self.collection_url(link.get('href') or '', collector)
            if url:
                known_urls.add(url)
        for details in nav[0].xpath('./ul/li/header-menu/details'):
            summary = details.xpath('./summary[1]')
            if not summary:
                continue
            summary = summary[0]
            top_name = self.text(summary)
            top_href = summary.get('data-url') or ''
            children = {}
            for section in details.xpath('./div//ul[contains(@class, "mega-menu__list")]/li'):
                heading = section.xpath('./a[1]')
                if not heading:
                    continue
                heading = heading[0]
                leaves = {}
                for link in section.xpath('./ul/li/a[@href]'):
                    name = self.text(link)
                    href = link.get('href') or ''
                    if self.add_node(leaves, name, href, collector):
                        known_urls.add(self.collection_url(href, collector))
                if self.add_node(children, self.text(heading), heading.get('href') or '', collector, leaves):
                    heading_url = self.collection_url(heading.get('href') or '', collector)
                    if heading_url:
                        known_urls.add(heading_url)

            if self.add_node(result, top_name, top_href, collector, children):
                top_url = self.collection_url(top_href, collector)
                if top_url:
                    known_urls.add(top_url)

        other = {}
        other_urls = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav[contains(@class, "header__inline-menu")]'):
                continue
            href = link.get('href') or ''
            url = self.collection_url(href, collector)
            if not url or url in known_urls or url in other_urls:
                continue
            name = self.text(link) or urlsplit(url).path.rsplit('/', 1)[-1]
            self.add_node(other, name, href, collector)
            other_urls.add(url)

        if other:
            self.add_node(result, 'Other' if 'Other' not in result else 'Other2', '', collector, other)
        if not result:
            raise RuntimeError('Bare Home navigation produced no collection URLs')
        return result


class BareHomeCatCol(ShopifyCatCol):
    parser_types = (BareHomeMenuParser,)


if __name__ == '__main__':
    try:
        BareHomeCatCol(
            Tool,
            base_url,
            save_path,
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        ).run()
    finally:
        Tool.close()
