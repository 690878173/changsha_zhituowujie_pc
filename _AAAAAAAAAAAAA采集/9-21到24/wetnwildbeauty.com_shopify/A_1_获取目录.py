from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class WetNWildMenuParser(CatalogParser):
    """Parse Wet n Wild's page-menu mega navigation and homepage collection cards."""

    def matches(self, html):
        return 'id="page-menu"' in html and 'main-nav__mega-title' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        return urlsplit(url or '').path.lower().rstrip('/').startswith('/collections/')

    def add_collection(self, nodes, name, href, collector, child=None):
        url = collector.normalize_url(href) if href else ''
        if url and not self.is_collection(url):
            url = ''
        if not name or (not url and not child):
            return None
        return collector.add_node(nodes, name, url, child)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        menus = tree.xpath('//*[@id="page-menu"]')
        if not menus:
            raise RuntimeError('页面中未找到 #page-menu 导航')

        result = {}
        known_urls = set()
        menu = menus[0]
        root_lists = menu.xpath('.//ul[1]')
        if not root_lists:
            raise RuntimeError('#page-menu 中未找到一级菜单')

        for item in root_lists[0].xpath('./li'):
            top_links = item.xpath('./a[@href][1]')
            if not top_links:
                continue
            top_link = top_links[0]
            top_name = self.text(top_link)
            top_url = collector.normalize_url(top_link.get('href') or '')
            children = {}

            for group in item.xpath('./ul[1]/li'):
                group_links = group.xpath('./a[@href][1]')
                if not group_links:
                    continue
                group_link = group_links[0]
                group_name = self.text(group_link)
                group_url = collector.normalize_url(group_link.get('href') or '')
                leaves = {}
                for leaf_link in group.xpath('./ul[1]/li/a[@href]'):
                    leaf_name = self.text(leaf_link)
                    leaf_url = collector.normalize_url(leaf_link.get('href') or '')
                    if self.is_collection(leaf_url):
                        self.add_collection(leaves, leaf_name, leaf_url, collector)
                        known_urls.add(leaf_url)

                if self.is_collection(group_url):
                    self.add_collection(children, group_name, group_url, collector, leaves)
                    known_urls.add(group_url)
                elif leaves:
                    self.add_collection(children, group_name, '', collector, leaves)

            if self.is_collection(top_url):
                self.add_collection(result, top_name, top_url, collector, children)
                known_urls.add(top_url)
            elif children:
                self.add_collection(result, top_name, '', collector, children)

        other = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::*[@id="page-menu"] | ancestor::footer'):
                continue
            url = collector.normalize_url(link.get('href') or '')
            if not self.is_collection(url) or url in known_urls:
                continue
            name = self.text(link) or urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            if self.add_collection(other, name, url, collector) is not None:
                known_urls.add(url)

        if other:
            self.add_collection(result, 'Other' if 'Other' not in result else 'Other2', '', collector, other)
        if not result:
            raise RuntimeError('Wet n Wild 导航未产出任何 collection')
        return result


class WetNWildCatCol(ShopifyCatCol):
    parser_types = (WetNWildMenuParser,)


if __name__ == '__main__':
    WetNWildCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()
