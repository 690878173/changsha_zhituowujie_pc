"""Igloo Coolers homepage catalog parser."""

from urllib.parse import urlsplit, urlunsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


EXTRA_COLLECTIONS = (
    ('Winnie the Pooh Coolers', '/collections/winnie-the-pooh-coolers'),
    ('Winnie the Pooh Drinkware', '/collections/winnie-the-pooh-drinkware'),
)


def _text(node):
    return " ".join(
        " ".join(node.xpath('.//text()[not(ancestor::svg)]')).split()
    ).strip()


def _is_collection(url):
    """Return whether a link is a collection category, not a product/page."""
    path = urlsplit(url or '').path.lower().rstrip('/')
    return path.startswith('/collections/') and '/products/' not in path


def _url_key(url):
    """Compare links independent of scheme casing, www, and fragments."""
    parts = urlsplit(url or '')
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower().removeprefix('www.'),
            parts.path.rstrip('/'),
            '',
            '',
        )
    )


class IglooCoolersMenuParser(CatalogParser):
    """Parse Igloo's ``site-header-nav`` mega menu and collection links."""

    nav_xpath = '//nav[contains(concat(" ", normalize-space(@class), " "), " site-header-nav ")]'

    def matches(self, html):
        return 'site-header-nav__list' in html and 'site-header-nav__grandchild-link' in html

    def add_link(self, nodes, link, collector):
        name = _text(link)
        href = link.get('href') or ''
        if name and _is_collection(href):
            collector.add_node(nodes, name, self.clean_url(collector, href))

    @staticmethod
    def clean_url(collector, url):
        """Normalize collection links and discard tracking/filter queries."""
        normalized = collector.normalize_url(url)
        parts = urlsplit(normalized)
        return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip('/'), '', ''))

    def parse_column(self, column, collector, index):
        leaves = {}
        for link in column.xpath(
            './ul[contains(concat(" ", normalize-space(@class), " "), '
            '" site-header-nav__grandchild-list ")]'
            '/li/a[contains(concat(" ", normalize-space(@class), " "), '
            '" site-header-nav__grandchild-link ")]'
        ):
            self.add_link(leaves, link, collector)
        if not leaves:
            return

        headings = column.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), '
            '" site-header-nav__child-item ")]'
        )
        heading = _text(headings[0]) if headings else ''
        if heading:
            collector.add_node(self.current_children, heading, '', leaves)
        else:
            # The first mega-menu column has no heading in the source HTML.
            # Promote its titled links instead of inventing a section name.
            for name, node in leaves.items():
                collector.add_node(self.current_children, name, node['url'], node['child'])

    @staticmethod
    def _collect_urls(nodes):
        for node in nodes.values():
            if node.get('url'):
                yield node['url']
            yield from IglooCoolersMenuParser._collect_urls(node.get('child') or {})

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('Igloo homepage has no site-header-nav menu')

        result = {}
        known = set()
        root_items = navs[0].xpath(
            './ul[contains(concat(" ", normalize-space(@class), " "), '
            '" site-header-nav__list ")]/li'
        )
        for item in root_items:
            links = item.xpath(
                './a[contains(concat(" ", normalize-space(@class), " "), '
                '" site-header-nav__parent-link ")][1]'
            )
            if not links:
                continue
            root_link = links[0]
            root_name = _text(root_link)
            if not root_name:
                continue
            self.current_children = {}
            columns = item.xpath(
                './/div[contains(concat(" ", normalize-space(@class), " "), '
                '" site-header-nav__mega-menu-column ") and '
                'contains(concat(" ", normalize-space(@class), " "), '
                '" site-header-nav__child-list ")]'
            )
            for index, column in enumerate(columns, 1):
                self.parse_column(column, collector, index)
            view_all = item.xpath(
                './/a[contains(concat(" ", normalize-space(@class), " "), '
                '" site-header-nav__view-all-link ")][1]'
            )
            if view_all:
                link = view_all[0]
                # Keep the visible page title (the hidden suffix only repeats
                # the parent label for screen readers).
                title = ' '.join(' '.join(link.xpath('./text()')).split())
                href = link.get('href') or ''
                if title and _is_collection(href):
                    collector.add_node(self.current_children, title, self.clean_url(collector, href))
            root_url = root_link.get('href') or ''
            normalized_root = self.clean_url(collector, root_url) if _is_collection(root_url) else ''
            if normalized_root:
                known.add(_url_key(normalized_root))
            known.update(_url_key(url) for url in self._collect_urls(self.current_children))
            collector.add_node(result, root_name, normalized_root, self.current_children)

        # Collection cards and other links outside the navigation belong under Other.
        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav[contains(@class, "site-header-nav")]'):
                continue
            href = link.get('href') or ''
            normalized = self.clean_url(collector, href)
            if not _is_collection(normalized) or _url_key(normalized) in known:
                continue
            name = _text(link) or link.get('aria-label') or ''
            if name and collector.add_node(extra, name, normalized) is not None:
                known.add(_url_key(normalized))
        for name, href in EXTRA_COLLECTIONS:
            normalized = self.clean_url(collector, href)
            if _url_key(normalized) in known:
                continue
            if collector.add_node(extra, name, normalized) is not None:
                known.add(_url_key(normalized))
        if extra:
            collector.add_node(result, 'Other' if 'Other' not in result else 'Other2', '', extra)

        if not result:
            raise RuntimeError('Igloo homepage has no collection categories')
        return result


class IglooCoolersCatCol(ShopifyCatCol):
    parser_types = (IglooCoolersMenuParser,)


__all__ = ['IglooCoolersCatCol', 'IglooCoolersMenuParser']
