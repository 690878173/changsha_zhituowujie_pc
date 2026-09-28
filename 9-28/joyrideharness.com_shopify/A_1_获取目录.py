"""Collect Joyride's desktop, mobile, and homepage collection navigation."""

from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


save_path = Tool.File.path_add_site('data/ml.json')


class JoyrideMenuParser(CatalogParser):
    """Parse the VASTA header and Joyride's separately rendered mobile menu."""

    def matches(self, page_html):
        return (
            'ip-header__navigation' in page_html
            and 'shopify-section-custom-menu-mobile' in page_html
        )

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def fallback_name(url):
        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
        return handle.replace('-', ' ').title()

    def collection_url(self, href, collector):
        if not href or href.startswith('#'):
            return ''

        url = collector.normalize_url(href)
        path_parts = [part for part in urlsplit(url).path.split('/') if part]
        if len(path_parts) != 2 or path_parts[0].lower() != 'collections':
            return ''
        return url

    def link_name(self, link, url):
        mobile_title = link.xpath(
            './/*[contains(concat(" ", normalize-space(@class), " "), '
            '" new-menu-link__title ")]'
        )
        name = self.text(mobile_title[0]) if mobile_title else self.text(link)
        return name or self.fallback_name(url)

    def add_collection(self, nodes, link, collector):
        url = self.collection_url(link.get('href') or '', collector)
        if not url:
            return False

        base_name = self.link_name(link, url)
        if any(
            name == base_name and node.get('url') == url
            for name, node in nodes.items()
        ):
            return False

        name = base_name
        suffix = 2
        while name in nodes:
            name = f'{base_name} ({suffix})'
            suffix += 1

        collector.add_node(nodes, name, url)
        return True

    def parse(self, page_html, collector):
        tree = lxml_html.fromstring(page_html)
        primary_navigation = tree.xpath(
            '//nav[contains(concat(" ", normalize-space(@class), " "), '
            '" ip-header__navigation ")]'
        )
        mobile_navigation = tree.xpath('//*[@id="NavDrawer"]')
        if not primary_navigation or not mobile_navigation:
            raise RuntimeError('Joyride desktop or mobile navigation was not found')

        result = {}
        navigation_urls = set()

        # The header and mobile drawer are the two primary navigation versions
        # on this theme. Footer and homepage links are collected into Other.
        for link in primary_navigation[0].xpath('.//a[@href]'):
            if self.add_collection(result, link, collector):
                navigation_urls.add(self.collection_url(link.get('href'), collector))
        for link in mobile_navigation[0].xpath('.//a[@href]'):
            if self.add_collection(result, link, collector):
                navigation_urls.add(self.collection_url(link.get('href'), collector))

        if not navigation_urls:
            raise RuntimeError('Joyride navigation produced no collection URLs')

        other = {}
        other_urls = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath(
                'ancestor::nav[contains(concat(" ", normalize-space(@class), " "), '
                '" ip-header__navigation ")] | ancestor::*[@id="NavDrawer"]'
            ):
                continue
            url = self.collection_url(link.get('href') or '', collector)
            if not url or url in navigation_urls or url in other_urls:
                continue
            if self.add_collection(other, link, collector):
                other_urls.add(url)
        if other:
            group_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, group_name, '', other)

        return result


class JoyrideCatCol(ShopifyCatCol):
    parser_types = (JoyrideMenuParser,)


if __name__ == '__main__':
    try:
        JoyrideCatCol(
            Tool,
            base_url,
            save_path,
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        ).run()
    finally:
        Tool.close()
