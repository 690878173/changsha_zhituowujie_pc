from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class MousMenuParser(CatalogParser):
    """Parse Mous's server-rendered desktop mega menu without mobile duplicates."""

    def matches(self, html):
        return 'top-level-links-wrapper' in html and 'mega-menu-columns' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    def link_text(self, node):
        labels = node.xpath('.//span[contains(@class, "menu-link-text")][1]')
        return self.text(labels[0]) if labels else self.text(node)

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
        menu = tree.xpath('//*[contains(@class, "top-level-links-wrapper")]')
        if not menu:
            raise RuntimeError('页面中未找到 Mous 桌面导航')

        result = {}
        header_urls = set()
        for group in menu[0].xpath('.//*[contains(@class, "top-level-links")]/div[contains(@class, "link-group")]'):
            top = group.xpath('./div[contains(@class, "top-level-link")][1]')
            if not top:
                continue
            top_name = self.text(top[0])
            top_href = top[0].get('data-href') or ''
            children = {}

            for column in group.xpath('.//nav[contains(@class, "mega-menu-columns")]//div[contains(@class, "mega-menu-column")]'):
                heading = column.xpath('./div[contains(@class, "mega-menu-column__heading")][1]')
                if not heading:
                    continue
                column_name = self.text(heading[0])
                all_link = column.xpath('./a[contains(@class, "mega-menu-column__all")][1]')
                column_href = all_link[0].get('href') if all_link else ''
                leaves = {}
                for link in column.xpath('.//a[contains(@class, "mega-menu-link")][@href]'):
                    name = self.link_text(link)
                    href = link.get('href') or ''
                    if self.add_collection(leaves, name, href, collector) is not None:
                        header_urls.add(collector.normalize_url(href))
                if self.add_collection(children, column_name, column_href, collector, leaves) is not None:
                    if column_href:
                        header_urls.add(collector.normalize_url(column_href))

            for link in group.xpath('.//div[contains(@class, "mega-menu-media")]//a[@href]'):
                name = self.text(link)
                href = link.get('href') or ''
                if self.add_collection(children, name, href, collector) is not None:
                    header_urls.add(collector.normalize_url(href))

            if self.add_collection(result, top_name, top_href, collector, children) is not None and top_href:
                header_urls.add(collector.normalize_url(top_href))

        other = {}
        for link in tree.xpath('//a[@href][not(ancestor::footer)]'):
            if link.xpath('ancestor::*[contains(@class, "header-sticky-container")]'):
                continue
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            if not self.is_collection(url) or url in header_urls:
                continue
            name = self.text(link) or urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            if self.add_collection(other, name, href, collector) is not None:
                header_urls.add(url)

        if other:
            self.add_collection(result, 'Other' if 'Other' not in result else 'Other2', '', collector, other)
        if not result:
            raise RuntimeError('Mous 导航未产出任何 collection')
        return result


class MousCatCol(ShopifyCatCol):
    parser_types = (MousMenuParser,)


if __name__ == '__main__':
    MousCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()
