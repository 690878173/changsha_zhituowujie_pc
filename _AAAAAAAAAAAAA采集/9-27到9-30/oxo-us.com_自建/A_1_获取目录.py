"""Collect OXO's public WooCommerce product-category navigation."""

from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser, CatCol


SAVE_PATH = Tool.File.path_add_site("data/ml.json")
SNAPSHOT_PATH = Path(__file__).parent / "ts" / "01-catalog" / "homepage.html"


class OxoWooCommerceParser(CatalogParser):
    """Parse the server-rendered desktop menu and visible category links."""

    top_segments = {
        "kitchen-dining",
        "baby",
        "home",
        "outdoor-living-garden",
        "household-essentials",
    }

    def matches(self, html):
        return (
            "header-nav-main" in html
            and "menu-item-object-product_cat" in html
            and "woocommerce" in html
        )

    @staticmethod
    def text(node):
        values = node.xpath(".//text()[not(ancestor::svg)]")
        return " ".join(" ".join(values).split())

    def category_url(self, href, collector):
        if not href or href.startswith(("#", "javascript:")):
            return ""
        url = collector.normalize_url(href)
        parsed = urlsplit(url)
        if parsed.netloc != urlsplit(collector.base_url).netloc:
            return ""
        parts = [part for part in parsed.path.split("/") if part]
        if not parts or parts[0].lower() not in self.top_segments:
            return ""
        return url

    def add_category(self, nodes, name, href, collector, child=None):
        url = self.category_url(href, collector)
        if not name or (not url and not child):
            return None
        return collector.add_node(nodes, name, url, child)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        nav = tree.xpath(
            '//ul[contains(concat(" ", normalize-space(@class), " "), " header-nav-main ")]'
        )
        if not nav:
            raise RuntimeError("OXO desktop product-category menu was not found")

        result = {}
        known_urls = set()
        menu = nav[0]
        for item in menu.xpath('./li[contains(@class, "menu-item-object-product_cat")]'):
            link = item.xpath('./a[@href][1]')
            if not link:
                continue
            link = link[0]
            top_name = self.text(link)
            children = {}
            for child in item.xpath(
                './ul[contains(concat(" ", normalize-space(@class), " "), " sub-menu ")]'
                '/li[contains(@class, "menu-item-object-product_cat")]/a[@href]'
            ):
                child_url = self.category_url(child.get("href") or "", collector)
                if not child_url:
                    continue
                self.add_category(children, self.text(child), child.get("href") or "", collector)
                known_urls.add(child_url)
            top_url = self.category_url(link.get("href") or "", collector)
            self.add_category(result, top_name, link.get("href") or "", collector, children)
            if top_url:
                known_urls.add(top_url)

        other = {}
        for link in tree.xpath('//a[@href and not(ancestor::header)]'):
            url = self.category_url(link.get("href") or "", collector)
            if not url or url in known_urls:
                continue
            name = self.text(link)
            if name:
                self.add_category(other, name, link.get("href") or "", collector)
                known_urls.add(url)
        if other:
            self.add_category(result, "Other" if "Other" not in result else "Other2", "", collector, other)

        if not result or not known_urls:
            raise RuntimeError("OXO navigation produced no product-category URLs")
        return result


class OxoCatalog(CatCol):
    parser_types = (OxoWooCommerceParser,)


if __name__ == "__main__":
    try:
        OxoCatalog(Tool, base_url, SAVE_PATH, SNAPSHOT_PATH).run()
    finally:
        Tool.close()

