"""阶段 1：抓取 Woxer 的 Shopify 公开商品目录。"""

from pathlib import Path
from urllib.parse import urlsplit

from config import Tool, base_url
from lxml import html as lxml_html
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol


def _text(node):
    return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())


def _is_collection(url):
    path = urlsplit(url or '').path.rstrip('/').lower()
    return path.startswith('/collections/') and '/products/' not in path


class WoxerMenuParser(CatalogParser):
    """Parse Woxer's current desktop mega menu and homepage collection links."""

    nav_xpath = (
        '//ul[contains(concat(" ", normalize-space(@class), " "), " main-navigation ") '
        'and contains(concat(" ", normalize-space(@class), " "), " jul-normal-menu ")]'
    )

    def matches(self, page_html):
        return 'jul-normal-menu' in page_html and 'nav-item dropdown megamenu' in page_html

    @staticmethod
    def _name(link, url):
        name = _text(link) or link.get('aria-label') or link.get('title') or ''
        normalized_name = name.lower().rstrip()
        if (
            normalized_name in {'shop now', 'learn more', 'view all'}
            or normalized_name.endswith('shop now')
            or len(name.split()) > 12
            or not name
        ):
            name = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1].replace('-', ' ').title()
        return name

    @staticmethod
    def _unique_name(nodes, name, url):
        if name not in nodes or nodes[name].get('url') == url:
            return name

        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1].replace('-', ' ').title()
        candidate = f'{name} ({handle})'
        suffix = 2
        while candidate in nodes and nodes[candidate].get('url') != url:
            candidate = f'{name} ({handle} {suffix})'
            suffix += 1
        return candidate

    def add_collection(self, nodes, link, collector):
        href = link.get('href') or ''
        url = collector.tool.URL.del_par(collector.normalize_url(href))
        if not _is_collection(url):
            return False

        name = self._unique_name(nodes, self._name(link, url), url)
        return collector.add_node(nodes, name, url) is not None

    def parse(self, page_html, collector):
        tree = lxml_html.fromstring(page_html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('Woxer homepage has no desktop main navigation')

        result = {}
        menu_items = navs[0].xpath(
            './li[contains(concat(" ", normalize-space(@class), " "), " megamenu ")]'
        )
        for item in menu_items:
            root_links = item.xpath(
                './a[contains(concat(" ", normalize-space(@class), " "), " main-nav-link ")][1]'
            )
            if not root_links:
                continue

            root_link = root_links[0]
            root_href = root_link.get('href') or ''
            root_url = collector.tool.URL.del_par(collector.normalize_url(root_href))
            root_name = self._unique_name(result, self._name(root_link, root_url), root_url)
            children = collector.add_node(
                result,
                root_name,
                root_url if _is_collection(root_url) else '',
            )
            if children is None:
                continue

            for group in item.xpath(
                './/a[contains(concat(" ", normalize-space(@class), " "), " level-2-link ")]'
            ):
                group_url = collector.tool.URL.del_par(
                    collector.normalize_url(group.get('href') or '')
                )
                group_name = self._unique_name(
                    children,
                    self._name(group, group_url),
                    group_url,
                )
                group_children = collector.add_node(
                    children,
                    group_name,
                    group_url if _is_collection(group_url) else '',
                )
                if group_children is None:
                    continue

                for leaf in group.xpath(
                    './following-sibling::div['
                    'contains(concat(" ", normalize-space(@class), " "), " sub-child-links ")'
                    ']//a[@href]'
                ):
                    self.add_collection(group_children, leaf, collector)
                if not group_children:
                    children.pop(group_name, None)

            for leaf in item.xpath(
                './/a[.//span[contains(concat(" ", normalize-space(@class), " "), '
                '" desktop-nav-main-child-link ")]]'
            ):
                self.add_collection(children, leaf, collector)
            if not children and not _is_collection(root_url):
                result.pop(root_name, None)

        other = {}
        for link in tree.xpath(
            '//a[@href and not(ancestor::ul['
            'contains(concat(" ", normalize-space(@class), " "), " main-navigation ")'
            ']) and not(ancestor::*['
            'contains(concat(" ", normalize-space(@class), " "), " navbar-mobile ")'
            ']) and not(ancestor::*['
            'contains(concat(" ", normalize-space(@class), " "), " mobile-nav ")'
            '])]'
        ):
            self.add_collection(other, link, collector)

        if other:
            other_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, other_name, '', other)
        if not result:
            raise RuntimeError('Woxer homepage has no collection categories')
        return result


if __name__ == '__main__':
    try:
        catalog = CatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '1' / 'homepage.html',
        )
        catalog.parser_types = (WoxerMenuParser, *catalog.parser_types)
        catalog.run()
    finally:
        Tool.close()
