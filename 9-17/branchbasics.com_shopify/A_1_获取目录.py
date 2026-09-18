"""阶段 1：抓取 Branch Basics 的公开商品目录。"""

from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class BranchBasicsMenuParser(CatalogParser):
    """解析 Branch Basics 自定义的桌面 Shop mega menu。"""

    desktop_nav_xpath = (
        '//nav[@aria-label="Main Menu" and contains(@class, "tw:md:grid")]'
    )

    def matches(self, html):
        return (
            'aria-label="Main Menu"' in html
            and 'shop-linklist-' in html
            and 'data-navlink-type="global-subnav"' in html
        )

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower().rstrip('/')
        return path.startswith('/collections/') and '/products/' not in path

    @staticmethod
    def unique_name(nodes, name, url):
        if name not in nodes:
            return name
        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1] or 'collection'
        candidate = f'{name} ({handle})'
        number = 2
        while candidate in nodes:
            candidate = f'{name} ({handle}) {number}'
            number += 1
        return candidate

    def add_collection(self, nodes, name, href, collector, known_urls):
        url = collector.normalize_url(href)
        if not name or not self.is_collection(url) or url in known_urls:
            return False
        name = self.unique_name(nodes, name, url)
        if collector.add_node(nodes, name, url) is None:
            return False
        known_urls.add(url)
        return True

    def parse_shop_menu(self, nav, collector, known_urls):
        result = {}
        for item in nav.xpath('./ul[1]/li'):
            button = item.xpath('./button[1]')
            if not button:
                continue
            name = self.text(button[0])
            child = {}
            for link in item.xpath('./div//a[@data-navlink-type="global-subnav" and @href]'):
                link_name = (link.get('data-navlink-text') or self.text(link)).strip()
                self.add_collection(child, link_name, link.get('href') or '', collector, known_urls)
            if child:
                collector.add_node(result, name, '', child)
        return result

    def parse_page_links(self, tree, collector, known_urls):
        result = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header | ancestor::nav'):
                continue
            name = (link.get('aria-label') or self.text(link)).strip()
            self.add_collection(result, name, link.get('href') or '', collector, known_urls)
        return result

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.desktop_nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 Branch Basics 桌面主导航')

        known_urls = set()
        result = self.parse_shop_menu(navs[0], collector, known_urls)
        if not result:
            raise RuntimeError('Branch Basics Shop 菜单没有 collection 链接')

        other = self.parse_page_links(tree, collector, known_urls)
        if other:
            collector.add_node(result, 'Other' if 'Other' not in result else 'Other2', '', other)
        return result


class BranchBasicsCatCol(ShopifyCatCol):
    parser_types = (BranchBasicsMenuParser,)


if __name__ == '__main__':
    BranchBasicsCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()

