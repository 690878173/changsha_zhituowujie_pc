from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.mg_shopify.catalog import CatCol as MgShopifyCatCol


class HoneyloveMenuParser(CatalogParser):
    """Parse Honeylove's Hydrogen-rendered desktop and mobile menus."""

    def matches(self, html):
        return 'main-header' in html and '/collections/' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        return urlsplit(url or '').path.rstrip('/').lower().startswith('/collections/')

    def add_collection(self, nodes, name, href, collector, child=None):
        url = collector.normalize_url(href) if href else ''
        if url and not self.is_collection(url):
            url = ''
        if not name or (not url and not child):
            return None
        return collector.add_node(nodes, name, href if url else '', child)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        headers = tree.xpath('//header[contains(@class, "main") or .//*[contains(@class, "main-header")]]')
        if not headers:
            raise RuntimeError('首页中未找到 Honeylove 主导航')
        header = headers[0]

        result = {}
        header_urls = set()

        # The desktop bar contains the canonical top-level collection links.
        desktop = header.xpath(
            './div[contains(@class, "hidden") and contains(@class, "desktop:flex") '
            'and contains(@class, "justify-center") and contains(@class, "items-center")]'
        )
        if desktop:
            for link in desktop[0].xpath('.//a[@href]'):
                href = link.get('href') or ''
                url = collector.normalize_url(href)
                if not self.is_collection(url):
                    continue
                name = self.text(link)
                if self.add_collection(result, name, href, collector) is not None:
                    header_urls.add(url)

        # React streaming may place the resolved mobile menu in a hidden sibling
        # (outside ``header``), so locate its stable group labels globally.
        headings = tree.xpath(
            '//*[contains(@class, "font-safiroRegular") and '
            'normalize-space(string())="Bundle and Save"]'
        )
        for heading in headings:
            group_name = self.text(heading)
            grid = heading.getparent().xpath('./div[contains(@class, "grid")][1]')
            if not grid:
                continue
            children = {}
            for link in grid[0].xpath('./a[@href]'):
                href = link.get('href') or ''
                url = collector.normalize_url(href)
                if not self.is_collection(url):
                    continue
                name = self.text(link)
                if self.add_collection(children, name, href, collector) is not None:
                    header_urls.add(url)
            self.add_collection(result, group_name, '', collector, children)

        # Collection links elsewhere on the page are retained under Other.
        other = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header'):
                continue
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            if not self.is_collection(url) or url in header_urls:
                continue
            name = self.text(link) or urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            self.add_collection(other, name, href, collector)
        if other:
            other_name = 'Other'
            while other_name in result:
                other_name += '2'
            self.add_collection(result, other_name, '', collector, other)

        if not result:
            raise RuntimeError('Honeylove 导航未产出任何 collection')
        return result


class HoneyloveCatCol(MgShopifyCatCol):
    parser_types = (HoneyloveMenuParser,)


if __name__ == '__main__':
    HoneyloveCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()
