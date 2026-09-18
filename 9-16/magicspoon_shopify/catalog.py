"""Magic Spoon homepage catalog parser."""

from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


# The root links in the source menu are filtered ``shop-all`` URLs.  These are
# the actual collection pages represented by the visible navigation labels.
ROOT_COLLECTIONS = {
    'Cereal': '/collections/cereal',
    'Oatmeal': '/collections/oatmeal-dropdown',
    'Treats': '/collections/treats',
    'Granola': '/collections/granola',
    'Pastries': '/collections/byob-pastries-collection',
}

# These links are supplied by the storefront but have no reliable navigation
# parent in the captured menu, so they deliberately remain under Other.
OTHER_COLLECTIONS = (
    ('Product Dropdown', '/collections/product-dropdown'),
    ('All', '/collections/all'),
    ('Home Front', '/collections/homefront'),
    ('Merch', '/collections/merch'),
    ('GWP Eligible', '/collections/gwp-eligible'),
    ('Find Your Flavor', '/collections/find-your-flavor'),
    ('All - YJ', '/collections/all-yj'),
    ('MS114 - Cereal Options', '/collections/product-dropdown-copy'),
    ('Treats Drop Down', '/collections/bar-dropdown'),
    ('MS114 - Treats Options', '/collections/treats-drop-down-copy'),
    ('ALL products with tag: GWP-gift', '/collections/gwp-gift'),
    ('Marshmallow Cereal Dropdown', '/collections/marshmallow-cereal-dropdown'),
    ('Granola Dropdown', '/collections/granola-dropdown'),
    ('Core Fiber Dropdown', '/collections/core-fiber'),
    ('MS114 - Granola Options', '/collections/granola-dropdown-copy'),
    ('Pastries Dropdown', '/collections/pastries-dropdown'),
    ('Pastries - Klaviyo', '/collections/pastries-klaviyo'),
    ('MS114 - Pastries Options', '/collections/ms114-pastries-options'),
    ('MS114 - Oatmeal Options', '/collections/ms114-oatmeal-options'),
    ('BYOB Oatmeal Collection', '/collections/byob-oatmeal-collection-1'),
    ('BYOB Classic Cereal Collection', '/collections/byob-classic-cereal-collection'),
    ('BYOB Fiber Cereal Collection', '/collections/byob-fiber-cereal-collection'),
    ('BYOB Marshmallow Cereal Collection', '/collections/byob-marshmallow-cereal-collection'),
    ('Shop All', '/collections/shop-all-copy'),
    ("Don't sell without minimum $ in cart", '/collections/dont-sell-without-minimum-4-pack-in-cart'),
)


ROOT_COLLECTIONS = {
    'Cereal': '/collections/cereal',
    'Oatmeal': '/collections/oatmeal-dropdown',
    'Treats': '/collections/treats',
    'Granola': '/collections/granola',
    'Pastries': '/collections/byob-pastries-collection',
}


def _text(node):
    return " ".join(
        " ".join(node.xpath('.//text()[not(ancestor::svg)]')).split()
    ).strip()


def _is_collection(url):
    path = urlsplit(url or "").path.lower().rstrip("/")
    return path.startswith("/collections/") and "/products/" not in path


class MagicSpoonMenuParser(CatalogParser):
    """Parse Magic Spoon's ``ms21-header`` menu and page collection links."""

    nav_xpath = '//nav[contains(concat(" ", normalize-space(@class), " "), " ms21-header ")]'

    def matches(self, html):
        return 'class="ms21-header' in html and 'ms21-link-trigger' in html

    @staticmethod
    def _key(url):
        parts = urlsplit(url)
        host = parts.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host, parts.path.rstrip("/")

    @staticmethod
    def _clean_url(collector, url):
        normalized = collector.normalize_url(url)
        if not normalized:
            return ''
        parts = urlsplit(normalized)
        return f'{parts.scheme}://{parts.netloc}{parts.path.rstrip("/")}'

    def add_collection(self, nodes, link, collector, seen):
        href = link.get("href") or ""
        normalized = self._clean_url(collector, href)
        if not _is_collection(normalized):
            return False
        key = self._key(normalized)
        if key in seen:
            return False
        name = _text(link) or link.get("aria-label") or ""
        if not name:
            return False
        if collector.add_node(nodes, name, normalized) is None:
            return False
        seen.add(key)
        return True

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError("Magic Spoon homepage has no ms21 navigation")

        result = {}
        seen = set()
        shop_all_url = self._clean_url(collector, '/collections/shop-all')
        collector.add_node(result, 'Shop All', shop_all_url)
        shop_all_children = result['Shop All']['child']
        seen.add(self._key(shop_all_url))
        menu = navs[0].xpath(
            './/div[contains(concat(" ", normalize-space(@class), " "), " ms21-links ")]'
            '/ul[1]/li'
        )
        for item in menu:
            root_links = item.xpath(
                './/a[contains(concat(" ", normalize-space(@class), " "), " ms21-link-trigger ")][1]'
            )
            if not root_links:
                continue
            root_link = root_links[0]
            root_name = _text(root_link)
            root_href = root_link.get("href") or ""
            children = {}
            for link in item.xpath(
                './/div[contains(concat(" ", normalize-space(@class), " "), " ms21-dropdown ")]//a[@href]'
            ):
                self.add_collection(children, link, collector, seen)
            normalized_root = self._clean_url(
                collector,
                ROOT_COLLECTIONS.get(root_name, root_href),
            )
            if root_name and normalized_root:
                category = collector.add_node(
                    shop_all_children,
                    root_name,
                    normalized_root,
                    children,
                )
                if category is not None and _is_collection(normalized_root):
                    seen.add(self._key(normalized_root))

        extra = {}
        for name, href in OTHER_COLLECTIONS:
            self.add_named_collection(extra, name, href, collector, seen)

        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav[contains(concat(" ", normalize-space(@class), " "), " ms21-header ")]'):
                continue
            self.add_collection(extra, link, collector, seen)
        if extra:
            collector.add_node(shop_all_children, 'Other', '', extra)
        if not result:
            raise RuntimeError("Magic Spoon homepage has no collection categories")
        return result

    def add_named_collection(self, nodes, name, href, collector, seen):
        normalized = self._clean_url(collector, href)
        if not _is_collection(normalized) or self._key(normalized) in seen:
            return False
        if collector.add_node(nodes, name, normalized) is None:
            return False
        seen.add(self._key(normalized))
        return True


class MagicSpoonCatCol(ShopifyCatCol):
    parser_types = (MagicSpoonMenuParser,)


__all__ = ["MagicSpoonCatCol", "MagicSpoonMenuParser"]
