"""Collect CASETiFY's public desktop navigation into product-category tasks."""

from pathlib import Path
from urllib.parse import urlsplit

from lxml import etree

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser, CatCol


SAVE_PATH = Tool.File.path_add_site('data/ml.json')
SNAPSHOT_PATH = Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html'


class CasetifyNavigationParser(CatalogParser):
    """Parse the server-rendered mega menu while omitting its layout-only columns."""

    excluded_prefixes = (
        '/about-us', '/chase-card-by-casetify', '/customer-service', '/gift-card',
        '/my/', '/product/', '/setting/', '/visit-us',
    )

    def matches(self, html):
        return 'id="casetify-menu"' in html and 'layer-1-wrapper' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split()).replace('‑', '-')

    @staticmethod
    def class_xpath(name):
        return f'.//*[contains(concat(" ", normalize-space(@class), " "), " {name} ")]'

    def category_url(self, anchor, collector):
        href = (anchor.get('href') or '').strip()
        if not href or href.startswith(('javascript:', '#')):
            return ''
        url = collector.normalize_url(href)
        parsed = urlsplit(url)
        if parsed.netloc != urlsplit(collector.base_url).netloc:
            return ''
        if parsed.path in {'', '/'} or parsed.path.startswith(self.excluded_prefixes):
            return ''
        return url

    def add_leaf(self, parent, name, url, collector):
        name = collector.normalize_name(name)
        if not name or not url or name in parent:
            return
        collector.add_node(parent, name, url)

    def ensure_branch(self, parent, name, collector):
        name = collector.normalize_name(name)
        if not name:
            return None
        existing = parent.get(name)
        if existing:
            return existing.get('child')
        return collector.add_node(parent, name, '')

    def layer_title(self, layer):
        title = layer.xpath('./div[contains(@class, "nav-header")]//div[contains(@class, "layer-title")]')
        return self.text(title[0]) if title else ''

    def group_title(self, layer4):
        title = layer4.xpath('./span[contains(@class, "menu-item-title")]')
        return self.text(title[0]) if title else ''

    def layer5_title(self, layer5):
        title = layer5.xpath(
            './div[contains(@class, "nav-d-inline-block")]'
            '//div[contains(@class, "text-container")]'
        )
        return self.text(title[0]) if title else ''

    def parse_layer(self, layer, menu, collector):
        top_name = self.layer_title(layer)
        if not top_name or top_name == 'Gift Card':
            return
        top = self.ensure_branch(menu, top_name, collector)
        if not isinstance(top, dict):
            return

        for layer4 in layer.xpath(self.class_xpath('layer-4-wrapper')):
            section_name = self.group_title(layer4)
            for anchor in layer4.xpath('.//a[@href]'):
                url = self.category_url(anchor, collector)
                if not url:
                    continue
                name = self.text(anchor)
                if not name:
                    continue

                layer6 = anchor.xpath('ancestor::div[contains(@class, "layer-6-wrapper")][1]')
                if layer6:
                    layer5 = anchor.xpath('ancestor::div[contains(@class, "layer-5-wrapper")][1]')
                    parent_name = self.layer5_title(layer5[0]) if layer5 else ''
                    if parent_name:
                        parent = self.ensure_branch(top, parent_name, collector)
                        if isinstance(parent, dict):
                            self.add_leaf(parent, name, url, collector)
                        continue

                if section_name and section_name not in {'Device', 'Image Banner', top_name}:
                    parent = self.ensure_branch(top, section_name, collector)
                    if isinstance(parent, dict):
                        self.add_leaf(parent, name, url, collector)
                else:
                    self.add_leaf(top, name, url, collector)

    def add_direct_navigation_links(self, tree, menu, collector):
        """Keep product links represented as direct navigation chips."""
        other = {}
        for anchor in tree.xpath('//div[@id="casetify-menu"]//div[contains(@class, "nav-tab-wrapper")]//a[@href]'):
            url = self.category_url(anchor, collector)
            if url:
                self.add_leaf(other, self.text(anchor), url, collector)
        if other:
            self.ensure_branch(menu, 'Other' if 'Other' not in menu else 'Other2', collector).update(other)

    def add_homepage_links(self, tree, menu, collector):
        """Homepage collection cards are public category entries outside the menu."""
        other = {}
        for anchor in tree.xpath('//a[@href][not(ancestor::div[@id="casetify-menu"])]'):
            url = self.category_url(anchor, collector)
            name = self.text(anchor)
            if not url or not name or len(name) > 80:
                continue
            if name.casefold() in {'learn more', 'shop now', 'view all'}:
                continue
            if name.casefold().startswith('your browser does not support'):
                continue
            self.add_leaf(other, name, url, collector)
        if other:
            self.ensure_branch(menu, 'Other' if 'Other' not in menu else 'Other2', collector).update(other)

    def parse(self, html, collector):
        tree = etree.HTML(html)
        desktop = tree.xpath(
            '//div[@id="casetify-menu"]'
            '//div[contains(@class, "nav-d-xs-none") and contains(@class, "layer-0-wrapper")][1]'
        )
        if not desktop:
            raise RuntimeError('CASETiFY desktop mega menu was not found')

        menu = {}
        for layer in desktop[0].xpath('./descendant::div[contains(@class, "layer-1-wrapper")]'):
            self.parse_layer(layer, menu, collector)
        self.add_direct_navigation_links(tree, menu, collector)
        self.add_homepage_links(tree, menu, collector)
        if not menu:
            raise RuntimeError('CASETiFY navigation produced no product categories')
        return menu


class CasetifyCatalog(CatCol):
    """Avoid printing the full Unicode menu tree to legacy Windows terminals."""

    def run(self):
        menu = self.after_parse(self.parse(self.fetch()))
        self.export_catalog(menu)
        print(f'Collected {len(menu)} top-level CASETiFY categories.')
        return menu


collector = CasetifyCatalog(Tool, base_url, SAVE_PATH, SNAPSHOT_PATH)
collector.parser_types = (CasetifyNavigationParser,)


if __name__ == '__main__':
    try:
        collector.run()
    finally:
        Tool.close()
