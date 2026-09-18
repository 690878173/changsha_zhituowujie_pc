"""Tommy John homepage catalog parser."""

import json
import re
from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


def _text(node):
    return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())


def _is_collection(url):
    path = urlsplit(url or '').path.lower().rstrip('/')
    return path.startswith('/collections/') and '/products/' not in path


class TommyJohnMenuParser(CatalogParser):
    nav_xpath = '//nav[@id="redesign-main-menu-post-holiday"]'

    def matches(self, html):
        return 'redesign-main-menu-post-holiday' in html

    @staticmethod
    def _key(url):
        parts = urlsplit(url)
        host = parts.netloc.lower()
        if host.startswith('www.'):
            host = host[4:]
        return host, parts.path.rstrip('/'), parts.query

    def add_collection(self, nodes, link, collector, seen):
        href = link.get('href') or ''
        normalized = collector.normalize_url(href)
        if not _is_collection(normalized):
            return False
        key = self._key(normalized)
        if key in seen:
            return False
        name = _text(link) or link.get('aria-label') or ''
        if not name:
            return False
        if collector.add_node(nodes, name, href) is None:
            return False
        seen.add(key)
        return True

    @staticmethod
    def _extract_linklist(html):
        """Extract the Shopify ``theme.linklists`` object without executing JS."""
        marker = "theme.linklists['redesign-main-menu-post-holiday']"
        marker_index = html.find(marker)
        if marker_index < 0:
            return None
        start = html.find('{', marker_index)
        if start < 0:
            return None
        depth = 0
        quote = None
        escaped = False
        end = None
        for index in range(start, len(html)):
            char = html[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in ('"', "'"):
                quote = char
            elif char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            return None
        payload = html[start:end]
        payload = re.sub(r'([\{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)', r'\1"\2"\3', payload)
        payload = re.sub(r',\s*([}\]])', r'\1', payload)
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None

    def _add_linklist_node(self, nodes, item, collector):
        name = item.get('title') or ''
        if not name:
            return
        children = {}
        for child in item.get('links') or []:
            self._add_linklist_node(children, child, collector)
        url = item.get('url') or ''
        normalized = collector.normalize_url(url) if _is_collection(url) else ''
        if not normalized and not children:
            return
        collector.add_node(nodes, name, normalized, children)

    def _parse_embedded_menu(self, html, collector):
        menu = self._extract_linklist(html)
        if not menu:
            return None
        result = {}
        for item in menu.get('links') or []:
            self._add_linklist_node(result, item, collector)
        return result or None

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('Tommy John homepage has no main menu')

        result = self._parse_embedded_menu(html, collector)
        if result is None:
            result = {}
            seen = set()
            for link in navs[0].xpath('./ul/li/a[@href]'):
                self.add_collection(result, link, collector, seen)
        else:
            seen = set()
            self._collect_tree_urls(result, seen)

        # Preserve collection links from footer/quick-link menus and homepage sections.
        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav[@id="redesign-main-menu-post-holiday"]'):
                continue
            self.add_collection(extra, link, collector, seen)
        if extra:
            collector.add_node(result, 'Other', '', extra)

        if not result:
            raise RuntimeError('Tommy John homepage has no collection categories')

        for k,v in {'Active':'https://www.tommyjohn.com/collections/active-lifestyle',
                    'Travel':'https://www.tommyjohn.com/collections/travel-essentials',
                    'Daily Wear':'https://www.tommyjohn.com/collections/daily-wear'}.items():

         result['New & Featured']['child'][k] = {'url':v}
        return result

    @staticmethod
    def _collect_tree_urls(nodes, seen):
        for node in nodes.values():
            url = node.get('url')
            if url:
                seen.add(TommyJohnMenuParser._key(url))
            TommyJohnMenuParser._collect_tree_urls(node.get('child') or {}, seen)


class TommyJohnCatCol(ShopifyCatCol):
    parser_types = (TommyJohnMenuParser,)


__all__ = ['TommyJohnCatCol', 'TommyJohnMenuParser']
