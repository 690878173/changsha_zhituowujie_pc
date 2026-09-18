"""Buff City Soap homepage catalog parser."""

import json
from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


def _text(node):
    return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())


def _is_collection(url):
    path = urlsplit(url or '').path.lower().rstrip('/')
    return path.startswith('/collections/') and '/products/' not in path


class BuffCitySoapMenuParser(CatalogParser):
    menu_xpath = '//header[contains(concat(" ", normalize-space(@class), " "), " buff-meganav ")]'

    def matches(self, html):
        return 'buff-meganav__menu' in html and 'buff-meganav__dropdown' in html

    @staticmethod
    def _key(url):
        parts = urlsplit(url)
        host = parts.netloc.lower()
        if host.startswith('www.'):
            host = host[4:]
        return host, parts.path.rstrip('/'), parts.query

    def add_collection(self, nodes, link, collector, seen):
        href = link.get('href') or ''
        # Collection filters in query parameters do not identify a separate
        # catalog node, so retain only the canonical path.
        parts = urlsplit(href)
        href = parts._replace(query='', fragment='').geturl()
        normalized = collector.normalize_url(href)
        if not _is_collection(normalized):
            return False
        key = self._key(normalized)
        if key in seen:
            return False
        name = _text(link) or link.get('aria-label') or ''
        if not name:
            return False
        if name in nodes:
            suffix = urlsplit(normalized).path.rstrip('/').rsplit('/', 1)[-1]
            name = f'{name} ({suffix})'
            counter = 2
            while name in nodes:
                name = f'{name} {counter}'
                counter += 1
        if collector.add_node(nodes, name, href) is None:
            return False
        seen.add(key)
        return True

    def add_collection_item(self, nodes, name, href, collector, seen):
        """Add a collection represented by structured menu data."""
        if not name or not href:
            return False
        parts = urlsplit(href)
        href = parts._replace(query='', fragment='').geturl()
        normalized = collector.normalize_url(href)
        if not _is_collection(normalized):
            return False
        key = self._key(normalized)
        if key in seen:
            return False
        if name in nodes:
            suffix = urlsplit(normalized).path.rstrip('/').rsplit('/', 1)[-1]
            name = f'{name} ({suffix})'
            counter = 2
            while name in nodes:
                name = f'{name} {counter}'
                counter += 1
        if collector.add_node(nodes, name, href) is None:
            return False
        seen.add(key)
        return True

    @staticmethod
    def _column_label(column):
        labels = column.xpath(
            './span[contains(concat(" ", normalize-space(@class), " "), '
            '" buff-meganav__column-label ")]'
        )
        return _text(labels[0]) if labels else ''

    def _parse_type_column(self, column, collector, seen):
        groups = {}
        details = column.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), '
            '" buff-meganav__dropdown__column-details ")]'
        )
        if not details:
            return groups
        for label in details[0].xpath('./label[span]'):
            spans = label.xpath('./span[1]')
            if not spans:
                continue
            group_name = _text(spans[0])
            children = label.getnext()
            if children is None or 'buff-meganav__dropdown__column-children' not in (
                children.get('class') or ''
            ).split():
                continue
            leaves = {}
            for link in children.xpath('.//a[@href]'):
                self.add_collection(leaves, link, collector, seen)
            if leaves:
                collector.add_node(groups, group_name, '', leaves)
        return groups

    def _parse_scent_column(self, column, collector, seen):
        groups = {}
        scripts = column.xpath('.//script[@data-scent-metaobjects]')
        if not scripts:
            return groups
        try:
            entries = json.loads(scripts[0].text or '')
        except (TypeError, ValueError):
            return groups
        grouped = {}
        for entry in entries if isinstance(entries, list) else []:
            if not isinstance(entry, dict) or not entry.get('url'):
                continue
            category = str(entry.get('category') or '').strip()
            title = str(entry.get('title') or '').strip()
            if not category or not title:
                continue
            leaves = grouped.setdefault(category, {})
            self.add_collection_item(leaves, title, entry['url'], collector, seen)
        for category, leaves in grouped.items():
            if leaves:
                collector.add_node(groups, category, '', leaves)
        return groups

    def parse_dropdown(self, dropdown, collector, seen):
        result = {}
        for column in dropdown.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), '
            '" buff-meganav__dropdown__column ")]'
        ):
            label = self._column_label(column)
            if label == 'By Type':
                groups = self._parse_type_column(column, collector, seen)
                if groups:
                    collector.add_node(result, label, '', groups)
                continue
            if label == 'By Scent':
                groups = self._parse_scent_column(column, collector, seen)
                if groups:
                    collector.add_node(result, label, '', groups)
                continue
            leaves = {}
            for link in column.xpath('.//a[@href]'):
                self.add_collection(leaves, link, collector, seen)
            if not leaves:
                continue
            if label:
                collector.add_node(result, label, '', leaves)
            else:
                # Unlabelled columns are not named artificially; promote the
                # links using their own page titles.
                for name, node in leaves.items():
                    collector.add_node(result, name, node['url'], node['child'])
        return result

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        headers = tree.xpath(self.menu_xpath)
        if not headers:
            raise RuntimeError('Buff City Soap homepage has no mega menu')
        menu = headers[0].xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), " buff-meganav__menu ")]'
        )
        if not menu:
            raise RuntimeError('Buff City Soap mega menu container is missing')

        result = {}
        seen = set()
        children = list(menu[0])
        for index, child in enumerate(children):
            classes = (child.get('class') or '').split()
            if 'buff-meganav__dropdown-link' not in classes or _text(child).lower() != 'shop':
                continue
            dropdown = next(
                (
                    candidate
                    for candidate in children[index + 1:]
                    if 'buff-meganav__dropdown' in (candidate.get('class') or '').split()
                ),
                None,
            )
            if dropdown is not None:
                result = self.parse_dropdown(dropdown, collector, seen)
            break

        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header[contains(@class, "buff-meganav")]'):
                continue
            self.add_collection(extra, link, collector, seen)
        if extra:
            collector.add_node(result, 'Other', '', extra)

        if not result:
            raise RuntimeError('Buff City Soap homepage has no collection categories')
        return result


class BuffCitySoapCatCol(ShopifyCatCol):
    parser_types = (BuffCitySoapMenuParser,)


__all__ = ['BuffCitySoapCatCol', 'BuffCitySoapMenuParser']
