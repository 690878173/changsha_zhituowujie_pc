from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class TopoDesignsMenuParser(CatalogParser):
    menu_xpath = (
        '//nav[contains(concat(" ", normalize-space(@class), " "), '
        '" header__inline-menu ")]'
    )
    group_xpath = (
        './div//div[contains(concat(" ", normalize-space(@class), " "), '
        '" mega-menu__links-wrapper ")]/ul[contains('
        'concat(" ", normalize-space(@class), " "), " mega-menu__list ")]/li'
    )

    def matches(self, html):
        return 'mega-menu__links-wrapper' in html and 'header__inline-menu' in html

    @staticmethod
    def text(node):
        return ' '.join(node.xpath('.//text()[not(ancestor::svg)]')).strip()

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower()
        return path.startswith('/collections/') and '/products/' not in path

    def add_collection(self, nodes, name, link, collector, child=None):
        href = link.get('href') or ''
        if name and self.is_collection(href):
            collector.add_node(nodes, name, href, child)

    def main_link_name(self, link):
        heading = link.xpath('.//h1[1] | .//h2[1] | .//h3[1]')
        if heading:
            name = self.text(heading[0])
            if name:
                return name
        text = self.text(link)
        if text and len(text) < 80 and text.lower() not in {'shop now', 'view all'}:
            return text
        return urlsplit(link.get('href') or '').path.rstrip('/').rsplit('/', 1)[-1].replace('-', ' ').title()

    @staticmethod
    def known_urls(nodes, urls=None):
        if urls is None:
            urls = set()
        for node in nodes.values():
            if node['url']:
                urls.add(node['url'])
            TopoDesignsMenuParser.known_urls(node['child'], urls)
        return urls

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        menus = tree.xpath(self.menu_xpath)
        if not menus:
            raise RuntimeError('页面中未找到 Topo Designs 桌面目录')

        result = {}
        for details in menus[0].xpath('./ul/li/header-menu/details'):
            root_name = self.text(details.xpath('./summary/span[1]')[0])
            root_url = (details.xpath('./summary/@data-href') or [''])[0]
            groups = {}
            for group in details.xpath(self.group_xpath):
                links = group.xpath('./a[@href][1]')
                if not links:
                    continue
                link = links[0]
                child = {}
                for leaf in group.xpath('./ul[1]/li/a[@href]'):
                    self.add_collection(child, self.text(leaf), leaf, collector)
                self.add_collection(groups, self.text(link), link, collector, child)
            if root_name and groups:
                collector.add_node(
                    result,
                    root_name,
                    root_url if self.is_collection(root_url) else '',
                    groups,
                )

        known = self.known_urls(result)
        extra = {}
        for link in tree.xpath('//main//a[@href]'):
            href = link.get('href') or ''
            normalized = collector.normalize_url(href)
            if not self.is_collection(href) or normalized in known:
                continue
            name = self.main_link_name(link)
            if name and collector.add_node(extra, name, href) is not None:
                known.add(normalized)
        if extra:
            other_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, other_name, '', extra)

        if not result:
            raise RuntimeError('Topo Designs 菜单没有可用 collection')
        return result


class TopoDesignsCatCol(ShopifyCatCol):
    parser_types = (TopoDesignsMenuParser,)
