from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


save_path = Tool.File.path_add_site('data/ml.json')


class BalaMenuParser(CatalogParser):
    """Parse Bala's server-rendered desktop and mobile menus."""

    def matches(self, page_html):
        return 'data-section-type="header"' in page_html and 'id="mobile-menu"' in page_html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        return urlsplit(url or '').path.rstrip('/').lower().startswith('/collections/')

    def collection_url(self, href, collector):
        if not href or href.startswith('#'):
            return ''
        url = collector.normalize_url(href)
        return url if self.is_collection(url) else ''

    @staticmethod
    def fallback_name(url):
        handle = unquote(urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1])
        return handle.replace('-', ' ').title()

    def add_collection(self, nodes, name, href, collector):
        url = self.collection_url(href, collector)
        if not url or any(item.get('url') == url for item in nodes.values()):
            return ''

        base_name = self.text(name) if hasattr(name, 'xpath') else ' '.join((name or '').split())
        base_name = base_name or self.fallback_name(url)
        node_name = base_name
        suffix = 2
        while node_name in nodes:
            node_name = f'{base_name} ({suffix})'
            suffix += 1

        collector.add_node(nodes, node_name, url)
        return url

    def parse(self, page_html, collector):
        tree = lxml_html.fromstring(page_html)
        headers = tree.xpath('//header[@data-section-type="header"]')
        if not headers:
            raise RuntimeError('Bala primary header was not found')

        navs = headers[0].xpath('.//nav[./ul[@role="list"]]')
        if not navs:
            raise RuntimeError('Bala desktop navigation was not found')

        result = {}
        known_urls = set()
        for menu in navs[0].xpath('./ul[@role="list"]/li'):
            mega_groups = menu.xpath(
                './div[contains(concat(" ", normalize-space(@class), " "), " group/megamenu ")]'
                '//div[./h2 and ./ul]'
            )
            trigger = menu.xpath('./div[1]')
            menu_name = self.text(trigger[0]) if trigger else ''
            if mega_groups and menu_name:
                menu_children = {}
                for group in mega_groups:
                    heading = self.text(group.xpath('./h2')[0])
                    group_children = {}
                    for link in group.xpath('./ul/li/a[@href]'):
                        url = self.add_collection(
                            group_children,
                            link,
                            link.get('href'),
                            collector,
                        )
                        if url:
                            known_urls.add(url)
                    if group_children:
                        collector.add_node(menu_children, heading, '', group_children)
                if menu_children:
                    collector.add_node(result, menu_name, '', menu_children)

            for link in menu.xpath('./a[@href]'):
                url = self.add_collection(result, link, link.get('href'), collector)
                if url:
                    known_urls.add(url)

        # The mobile menu is a second copy of the navigation. Its URLs must be
        # excluded from Other even when it has no additional collection path.
        for mobile_menu in tree.xpath('//*[@id="mobile-menu"]'):
            for link in mobile_menu.xpath('.//a[@href]'):
                url = self.collection_url(link.get('href'), collector)
                if url:
                    known_urls.add(url)

        if not result or not known_urls:
            raise RuntimeError('Bala navigation produced no collection URLs')

        other = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath(
                'ancestor::header[@data-section-type="header"] | ancestor::*[@id="mobile-menu"]'
            ):
                continue
            url = self.collection_url(link.get('href'), collector)
            if not url or url in known_urls:
                continue
            if self.add_collection(other, link, link.get('href'), collector):
                known_urls.add(url)
        if other:
            group_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, group_name, '', other)

        return result


class BalaCatCol(ShopifyCatCol):
    parser_types = (BalaMenuParser,)


if __name__ == '__main__':
    try:
        BalaCatCol(
            Tool,
            base_url,
            save_path,
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        ).run()
    finally:
        Tool.close()
