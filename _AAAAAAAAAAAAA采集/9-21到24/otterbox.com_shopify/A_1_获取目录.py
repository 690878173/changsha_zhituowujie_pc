from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class OtterboxMenuParser(CatalogParser):
    """Parse OtterBox's server-rendered desktop mega menu."""

    def matches(self, html):
        return 'header-menu__nav' in html and 'mega-menu__column' in html

    @staticmethod
    def text(node):
        values = node.xpath(
            './/text()[not(ancestor::svg) and not(ancestor::*['
            'contains(@class, "mega-menu__link-badge")])]'
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

    def add_unique_collection(self, nodes, name, href, collector):
        url = collector.normalize_url(href)
        if not self.is_collection(url):
            return None
        if name in nodes:
            handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            name = f'{name} ({handle})'
        return self.add_collection(nodes, name, href, collector)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        menus = tree.xpath('//nav[contains(@class, "header-menu__nav")]')
        if not menus:
            raise RuntimeError('OtterBox desktop menu was not found')

        menu = max(menus, key=lambda node: len(node.xpath('.//a[contains(@href, "/collections/")]')))
        result = {}
        known_urls = set()
        top_items = menu.xpath(
            './div[contains(@class, "menu-list")]/overflow-list/li['
            'contains(@class, "menu-list__list-item")]'
        )
        for item in top_items:
            top_links = item.xpath('./a[@href][1]')
            if not top_links:
                continue
            top_link = top_links[0]
            top_name = self.text(top_link)
            children = {}
            for section in item.xpath(
                './div//li[contains(@class, "mega-menu__column")]/'
                'div[contains(@class, "mega-menu__section")]'
            ):
                heading_links = section.xpath('./h2/a[@href][1] | ./a[@href][1]')
                heading_name = self.text(heading_links[0]) if heading_links else ''
                heading_href = heading_links[0].get('href') if heading_links else ''
                leaves = {}
                for link in section.xpath('.//ul[contains(@class, "mega-menu__sublink-list")]//a[@href]'):
                    if self.add_unique_collection(leaves, self.text(link), link.get('href') or '', collector):
                        known_urls.add(collector.normalize_url(link.get('href') or ''))
                if heading_name and (heading_href or leaves):
                    if self.add_collection(children, heading_name, heading_href, collector, leaves):
                        if heading_href:
                            known_urls.add(collector.normalize_url(heading_href))
                else:
                    children.update(leaves)

            if self.add_collection(result, top_name, top_link.get('href') or '', collector, children):
                top_url = collector.normalize_url(top_link.get('href') or '')
                if self.is_collection(top_url):
                    known_urls.add(top_url)

        other = {}
        for link in tree.xpath('//main//a[@href]'):
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            if not self.is_collection(url) or url in known_urls:
                continue
            if self.add_unique_collection(other, self.text(link), href, collector):
                known_urls.add(url)

        if other:
            self.add_collection(result, 'Other' if 'Other' not in result else 'Other2', '', collector, other)
        if not result:
            raise RuntimeError('OtterBox navigation produced no collection URLs')
        return result


class OtterboxCatCol(ShopifyCatCol):
    parser_types = (OtterboxMenuParser,)


if __name__ == '__main__':
    try:
        OtterboxCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        ).run()
    finally:
        Tool.close()



