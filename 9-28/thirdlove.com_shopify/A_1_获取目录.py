"""Collect ThirdLove's server-rendered collection navigation."""

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class ThirdLoveMenuParser(CatalogParser):
    """Parse the header custom elements and their inline submenu payloads."""

    submenu_pattern = re.compile(
        r'theme\.menuSubItems\[\s*"(?P<key>[^"]+)"\s*\]\s*=\s*'
    )

    def matches(self, html):
        return 'component-menu-item' in html and 'theme.menuSubItems[' in html

    @staticmethod
    def text(value):
        return ' '.join(str(value or '').split())

    @staticmethod
    def menu_key(title):
        return re.sub(r'[^\w&]', '-', title.lower()).lower()

    @staticmethod
    def is_collection(url):
        return urlsplit(url or '').path.rstrip('/').lower().startswith('/collections/')

    def collection_url(self, href, collector):
        if not href or href == '#':
            return ''
        url = collector.normalize_url(href)
        parts = urlsplit(url)
        if parts.netloc.lower() in {'thirdlove.com', 'www.thirdlove.com'}:
            path = parts.path
            if parts.query:
                path = f'{path}?{parts.query}'
            url = collector.normalize_url(path)
        return url if self.is_collection(url) else ''

    def add_node(self, nodes, title, href, collector, child=None):
        url = self.collection_url(href, collector)
        if not title or (not url and not child):
            return None
        return collector.add_node(nodes, title, url, child)

    def submenu_data(self, html):
        decoder = json.JSONDecoder()
        menus = {}
        for match in self.submenu_pattern.finditer(html):
            try:
                items, _ = decoder.raw_decode(html[match.end():].lstrip())
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f'Unable to parse ThirdLove submenu payload: {match.group("key")}'
                ) from exc
            if isinstance(items, list):
                menus[match.group('key')] = items
        return menus

    def build_items(self, items, collector, depth):
        nodes = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            title = self.text(item.get('title'))
            child = self.build_items(item.get('subItems') or [], collector, depth + 1)
            if depth >= 3:
                self.add_node(nodes, title, item.get('url') or '', collector)
                for child_title, child_node in child.items():
                    collector.add_node(
                        nodes,
                        child_title,
                        child_node.get('url') or '',
                        child_node.get('child') or {},
                    )
            else:
                self.add_node(nodes, title, item.get('url') or '', collector, child)
        return nodes

    @classmethod
    def known_urls(cls, nodes, found=None):
        if found is None:
            found = set()
        for node in nodes.values():
            if node.get('url'):
                found.add(node['url'])
            cls.known_urls(node.get('child') or {}, found)
        return found

    def link_title(self, link, url):
        title = self.text(' '.join(link.xpath('.//text()[not(ancestor::svg)]')))
        if not title:
            title = self.text(link.get('aria-label') or link.get('title'))
        if title:
            return title
        return urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1].replace('-', ' ').title()

    def parse_other(self, tree, collector, known_urls):
        other = {}
        other_urls = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav'):
                continue
            url = self.collection_url(link.get('href') or '', collector)
            if not url or url in known_urls or url in other_urls:
                continue
            if self.add_node(other, self.link_title(link, url), url, collector) is not None:
                other_urls.add(url)
        return other

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        submenus = self.submenu_data(html)
        menu_items = tree.xpath(
            '//nav[contains(concat(" ", normalize-space(@class), " "), '
            '" menu-container ")]//component-menu-item'
        )
        if not menu_items:
            raise RuntimeError('ThirdLove desktop navigation was not found')

        result = {}
        for item in menu_items:
            title = self.text(item.get('title'))
            children = self.build_items(submenus.get(self.menu_key(title), []), collector, 2)
            self.add_node(result, title, item.get('url') or '', collector, children)

        if not result:
            raise RuntimeError('ThirdLove navigation produced no collection URLs')

        other = self.parse_other(tree, collector, self.known_urls(result))
        if other:
            self.add_node(
                result,
                'Other' if 'Other' not in result else 'Other2',
                '',
                collector,
                other,
            )
        return result


class ThirdLoveCatCol(ShopifyCatCol):
    parser_types = (ThirdLoveMenuParser,)


if __name__ == '__main__':
    try:
        ThirdLoveCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        ).run()
    finally:
        Tool.close()
