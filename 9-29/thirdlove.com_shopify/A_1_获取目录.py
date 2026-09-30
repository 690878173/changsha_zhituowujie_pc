"""Collect ThirdLove's full public collection navigation."""

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class ThirdLoveMenuParser(CatalogParser):
    """Parse ThirdLove's header elements, menu cards, and catalog landing page."""

    submenu_pattern = re.compile(
        r'theme\.menuSubItems\[\s*"(?P<key>[^"]+)"\s*\]\s*=\s*'
    )
    section_pattern = re.compile(r'theme\.menuSections\s*=\s*')
    promo_pattern = re.compile(
        r'"text"\s*:\s*(?P<title>"(?:\\.|[^"\\])*")'
        r'.{0,2000}?'
        r'"announcementBarClickableUrl"\s*:\s*'
        r'(?P<url>"(?:\\.|[^"\\])*"|null)',
        re.DOTALL,
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
    def section_title(key):
        return ' '.join(key.replace('-', ' ').replace('_', ' ').split()).title()

    @staticmethod
    def is_collection(url):
        return urlsplit(url or '').path.rstrip('/').lower().startswith('/collections/')

    def collection_url(self, href, collector):
        if not href or href == '#':
            return ''
        url = collector.normalize_url(href)
        parts = urlsplit(url)
        if parts.netloc.lower() not in {'thirdlove.com', 'www.thirdlove.com'}:
            return ''
        url = collector.normalize_url(parts.path)
        return url if self.is_collection(url) else ''

    def merge_node(self, nodes, title, href, collector, child=None):
        """Add a collection/group node without discarding a same-level collision."""
        title = collector.normalize_name(self.text(title))
        child = child or {}
        url = self.collection_url(href, collector)
        if not title or (not url and not child):
            return None

        name = title
        suffix = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1] or 'group'
        number = 2
        while name in nodes:
            existing = nodes[name]
            if (existing.get('url') or '') == url:
                self.merge_nodes(existing.get('child') or {}, child, collector)
                return existing.get('child')
            label = suffix if number == 2 else f'{suffix} {number}'
            name = f'{title} ({label})'
            number += 1

        return collector.add_node(nodes, name, url, child)

    def merge_nodes(self, destination, source, collector):
        for title, node in source.items():
            self.merge_node(
                destination,
                title,
                node.get('url') or '',
                collector,
                node.get('child') or {},
            )

    def add_node(self, nodes, title, href, collector, child=None):
        return self.merge_node(nodes, title, href, collector, child)

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

    def section_data(self, html):
        match = self.section_pattern.search(html)
        if not match:
            return {}
        try:
            sections, _ = json.JSONDecoder().raw_decode(html[match.end():].lstrip())
        except json.JSONDecodeError as exc:
            raise RuntimeError('Unable to parse ThirdLove menu card payload') from exc
        if not isinstance(sections, dict):
            raise RuntimeError('ThirdLove menu card payload is not an object')
        return sections

    def build_items(self, items, collector, depth):
        nodes = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            title = self.text(item.get('title'))
            child = self.build_items(item.get('subItems') or [], collector, depth + 1)
            if depth >= 3:
                self.merge_node(nodes, title, item.get('url') or '', collector)
                self.merge_nodes(nodes, child, collector)
            else:
                self.merge_node(nodes, title, item.get('url') or '', collector, child)
        return nodes

    def section_nodes(self, cards, collector, section_key, use_section_for_repeats=False):
        entries = []
        for card in cards:
            if not isinstance(card, dict):
                continue
            card_entries = {}
            for suffix in ('', 'CA'):
                href = card.get(f'link{suffix}') or ''
                url = self.collection_url(href, collector)
                if not url:
                    continue
                title = self.text(
                    card.get(f'ctaText{suffix}') or card.get(f'heading{suffix}')
                )
                previous = card_entries.get(url)
                if previous is None or (
                    previous[0].lower() in {'', 'shop', 'shop now'}
                    and title.lower() not in {'', 'shop', 'shop now'}
                ):
                    card_entries[url] = (title, href, url)
            entries.extend(card_entries.values())

        url_counts = {}
        for _, _, url in entries:
            url_counts[url] = url_counts.get(url, 0) + 1

        nodes = {}
        generic_titles = {'', 'shop', 'shop now'}
        for title, href, url in entries:
            if title.lower() in generic_titles or (
                use_section_for_repeats and url_counts[url] > 1
            ):
                title = self.section_title(section_key)
            self.merge_node(nodes, title, href, collector)
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
            if self.merge_node(other, self.link_title(link, url), url, collector) is not None:
                other_urls.add(url)
        return other

    def promo_nodes(self, html, collector):
        nodes = {}
        for match in self.promo_pattern.finditer(html):
            try:
                title = json.loads(match.group('title'))
                href = json.loads(match.group('url')) if match.group('url') != 'null' else ''
            except json.JSONDecodeError:
                continue
            self.merge_node(nodes, title, href, collector)
        return nodes

    def merge_unseen_nodes(self, destination, source, collector, known_urls):
        for title, node in source.items():
            url = node.get('url') or ''
            if url and url in known_urls:
                continue
            self.merge_node(
                destination,
                title,
                url,
                collector,
                node.get('child') or {},
            )
            if url:
                known_urls.add(url)

    def add_collection_hub(self, menu, html, collector):
        """Add collection links rendered inside the public Collections landing page."""
        target = menu.get('Collections')
        if target is None:
            self.merge_node(
                menu,
                'Collections',
                '/collections/all-collections',
                collector,
            )
            target = menu.get('Collections')
        if target is None:
            raise RuntimeError('ThirdLove Collections root could not be added')

        tree = lxml_html.fromstring(html)
        for link in tree.xpath('//main//a[@href]'):
            if link.xpath('ancestor::nav'):
                continue
            url = self.collection_url(link.get('href') or '', collector)
            if not url or url == target.get('url'):
                continue
            self.merge_node(target['child'], self.link_title(link, url), url, collector)
        return menu

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        submenus = self.submenu_data(html)
        sections = self.section_data(html)
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
            self.merge_node(result, title, item.get('url') or '', collector, children)

        if not result:
            raise RuntimeError('ThirdLove navigation produced no collection URLs')

        root_by_key = {self.menu_key(title): node for title, node in result.items()}
        section_extras = {}
        for key, cards in sections.items():
            nodes = self.section_nodes(
                cards,
                collector,
                key,
                use_section_for_repeats=key not in root_by_key,
            )
            if key in root_by_key:
                self.merge_nodes(root_by_key[key]['child'], nodes, collector)
            else:
                self.merge_nodes(section_extras, nodes, collector)

        known_urls = self.known_urls(result)
        other = self.parse_other(tree, collector, known_urls)
        known_urls.update(self.known_urls(other))
        self.merge_unseen_nodes(other, section_extras, collector, known_urls)
        self.merge_unseen_nodes(other, self.promo_nodes(html, collector), collector, known_urls)
        if other:
            self.merge_node(
                result,
                'Other' if 'Other' not in result else 'Other2',
                '',
                collector,
                other,
            )
        return result


class ThirdLoveCatCol(ShopifyCatCol):
    parser_types = (ThirdLoveMenuParser,)

    def __init__(self, *args, hub_snapshot_path, **kwargs):
        super().__init__(*args, **kwargs)
        self.hub_snapshot_path = Path(hub_snapshot_path)

    def fetch_collection_hub(self):
        url = self.tool.URL.add_site('/collections/all-collections')
        response = self.tool.get(url)
        if response.status_code == 200 and response.text:
            self.tool.HTML.save_raw(response.text, self.hub_snapshot_path)
            return response.text
        if self.hub_snapshot_path.exists():
            self.tool.print(
                f'Collections 页面请求失败（{response.status_code}），使用本地 HTML',
                color='yellow',
            )
            return self.hub_snapshot_path.read_text(encoding='utf-8')
        raise RuntimeError(
            f'Collections 页面请求失败（{response.status_code}），且本地 HTML 不存在'
        )

    def after_parse(self, menu):
        menu = super().after_parse(menu)
        parser = self.create_parsers()[0]
        return parser.add_collection_hub(menu, self.fetch_collection_hub(), self)


if __name__ == '__main__':
    try:
        ThirdLoveCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
            hub_snapshot_path=Path(__file__).parent / 'ts' / '01-catalog' / 'all-collections.html',
        ).run()
    finally:
        Tool.close()
