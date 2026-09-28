"""Collect Four Sigmatic's custom mega-menu into Shopify collection paths."""

import re
from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class FourSigmaticMenuParser(CatalogParser):
    """Parse the site's server-rendered desktop and mobile mega menus."""

    top_item_class = 'lsg-mega-menu__linklist-item'
    top_link_class = 'lsg-mega-menu__linklist-link'
    child_link_class = 'lsg-mega-menu__btn--shop-all-sub'
    allowed_hosts = {'us.foursigmatic.com', 'www.us.foursigmatic.com'}

    def matches(self, html):
        return self.top_item_class in html and '/collections/' in html

    @staticmethod
    def text(value):
        return ' '.join(str(value or '').split())

    @classmethod
    def display_name(cls, value):
        return re.sub(r'^shop all\s+', '', cls.text(value), flags=re.IGNORECASE)

    @classmethod
    def is_collection(cls, url):
        parts = urlsplit(url or '')
        return (
            (not parts.netloc or parts.netloc.lower() in cls.allowed_hosts)
            and parts.path.rstrip('/').lower().startswith('/collections/')
        )

    def collection_url(self, href, collector):
        if not href or href == '#':
            return ''
        url = collector.normalize_url(href)
        return url if self.is_collection(url) else ''

    def add_item(self, nodes, title, href, collector, child=None):
        url = self.collection_url(href, collector)
        if not title or (not url and not child):
            return None
        return collector.add_node(nodes, title, url, child)

    def link_text(self, link, url):
        text = self.text(' '.join(link.xpath('.//text()[not(ancestor::svg)]')))
        if not text:
            text = self.text(link.get('aria-label') or link.get('title'))
        if text:
            return self.display_name(text)
        return urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1].replace('-', ' ').title()

    def child_nodes(self, top_item, parent_url, collector):
        children = {}
        seen_urls = set()
        child_links = top_item.xpath(
            './/a[contains(concat(" ", normalize-space(@class), " "), '
            '" lsg-mega-menu__btn--shop-all-sub ")][@href]'
        )
        for link in child_links:
            url = self.collection_url(link.get('href'), collector)
            if not url or url == parent_url or url in seen_urls:
                continue
            if self.add_item(children, self.link_text(link, url), link.get('href'), collector) is not None:
                seen_urls.add(url)
        return children

    @classmethod
    def known_urls(cls, nodes, found=None):
        if found is None:
            found = set()
        for node in nodes.values():
            if node.get('url'):
                found.add(node['url'])
            cls.known_urls(node.get('child') or {}, found)
        return found

    def parse_navigation(self, tree, collector):
        result = {}
        seen_top_urls = set()
        top_items = tree.xpath(
            '//ul[contains(concat(" ", normalize-space(@class), " "), '
            '" lsg-mega-menu__linklist ")]/li[contains('
            'concat(" ", normalize-space(@class), " "), '
            '" lsg-mega-menu__linklist-item ")]'
        )
        for item in top_items:
            links = item.xpath(
                './a[contains(concat(" ", normalize-space(@class), " "), '
                '" lsg-mega-menu__linklist-link ")][@href]'
            )
            if not links:
                continue
            link = links[0]
            url = self.collection_url(link.get('href'), collector)
            if not url or url in seen_top_urls:
                continue
            title = self.link_text(link, url)
            children = self.child_nodes(item, url, collector)
            if self.add_item(result, title, link.get('href'), collector, children) is not None:
                seen_top_urls.add(url)
        return result

    def parse_other(self, tree, collector, known_urls):
        other = {}
        other_urls = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath(
                'ancestor::div[contains(concat(" ", normalize-space(@class), " "), '
                '" lsg-mega-menu ")]'
            ):
                continue
            url = self.collection_url(link.get('href'), collector)
            if not url or url in known_urls or url in other_urls:
                continue
            if self.add_item(other, self.link_text(link, url), link.get('href'), collector) is not None:
                other_urls.add(url)
        return other

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        result = self.parse_navigation(tree, collector)
        if not result:
            raise RuntimeError('Four Sigmatic mega-menu produced no collection URLs')

        other = self.parse_other(tree, collector, self.known_urls(result))
        if other:
            name = 'Other' if 'Other' not in result else 'Other2'
            self.add_item(result, name, '', collector, other)
        return result


class FourSigmaticCatCol(ShopifyCatCol):
    parser_types = (FourSigmaticMenuParser,)


if __name__ == '__main__':
    try:
        FourSigmaticCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        ).run()
    finally:
        Tool.close()
