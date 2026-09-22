from pathlib import Path

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class CarpeMenuParser(CatalogParser):
    """Preserve Carpe's mobile navigation with collection replacements."""

    GROUP_COLLECTIONS = {
        'bundles': 'bundles',
        'best sellers': 'best-sellers',
        'new products': '',
        'underarm': 'underarm',
        'feminine care': 'feminine-care-deo',
        'cosmetics': 'cosmetics',
        'face': 'face',
        'hands feet': 'hand-foot',
        'body': 'other-body-parts',
        'scalp hair': 'individual-scalp',
        'accessories merch': 'accessories',
        'clinical strength': 'clinical-grade',
    }

    LEAF_COLLECTIONS = {
        'best selling starter pack': 'bundle-save',
        'all day matte collection': 'bundle-builder-cosmetic',
        'head to toe': 'sweat-control-for-all-over',
        'feminine care deodorant starter pack': 'feminine-care-deo',
        'build your own bundle': 'newbundlebuilder',
        'underarm stick': 'underarm-collection',
        'feminine care deodorant': 'feminine-care-deo',
        'face primer w spf': 'face-collection',
        'clinical grade underarm regimen': 'clinical-grade',
        'underarm skincare': 'all-underarm',
        'sweat resistant sunscreen': 'face-collection',
        'underarm wipes': 'on-the-go-wipes',
        'build your own underarm bundle': 'build-your-own-underarm-bundle-copy',
        'clinical grade exfoliating underarm wash': 'underarm-excluding-regimen',
        'womens groin powder': 'groin-powders',
        'breast': 'breast',
        'instant matte setting mist': 'individual-setting-mist',
        'setting powder': 'sweat-absorbing-makeup-products',
        'face': 'face',
        'face wipes': 'face-the-sweat',
        'hand': 'hand',
        'foot': 'foot',
        'mens groin powder': 'sweat-absorbing-powders-for-groin-sweat',
        'scalp regimen': 'individual-scalp',
        'scalp powder': 'individual-scalp',
        'scalp serum': 'individual-scalp',
        'accessories': 'accessories',
        'carpe merch': 'carpe-merch',
        'clinical grade underarm pm wipes': 'on-the-go-wipes',
        'clinical grade underarm am stick': 'antiperspirant',
    }

    OTHER_COLLECTIONS = (
        ('Shop All', 'all'),
        ('Antiperspirants', 'antiperspirant'),
        ('Sweat Absorbing', 'sweat-absorbing'),
        ('On The Go', 'on-the-go'),
        ('Thigh', 'thigh'),
        ('Individual Products', 'individual'),
        ('Other Quantities', 'other-quantities'),
        ('Underarm Scents', 'underarm-scents'),
        ('Hyperhidrosis', 'hyperhidrosis'),
        ('Intertrigo', 'intertrigo'),
        ('Womens Essentials', 'womens-essentials'),
        ('Mens Essentials', 'mens-essentials'),
        ('Hand and Foot Bundle', 'build-your-own-hand-and-foot-bundle'),
    )

    def matches(self, html):
        return 'navdrawer-main__item' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def menu_key(value):
        normalized = []
        for char in value.lower():
            if char.isalnum():
                normalized.append(char)
            elif char == "'" or ord(char) == 0x2019:
                continue
            else:
                normalized.append(' ')
        return ' '.join(''.join(normalized).split())

    def add_collection(self, nodes, name, handle, collector, child=None):
        if not name or (not handle and not child):
            return None
        url = collector.normalize_url(f'/collections/{handle}') if handle else ''
        return collector.add_node(nodes, name, url, child)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        result = {}
        menu_items = tree.cssselect('.navdrawer-main__item')
        if not menu_items:
            raise RuntimeError('Carpe mobile navigation was not found')

        for item in menu_items:
            title_nodes = item.cssselect('.navdrawer-main__button-title')
            if not title_nodes:
                continue
            title = self.text(title_nodes[0])
            child = {}
            for link in item.cssselect('.navdrawer-main__submenu-item > a'):
                name = self.text(link)
                handle = self.LEAF_COLLECTIONS.get(self.menu_key(name), '')
                self.add_collection(child, name, handle, collector)

            handle = self.GROUP_COLLECTIONS.get(self.menu_key(title), '')
            self.add_collection(result, title, handle, collector, child)

        result = {"SHOP":{'child':{**result}}}
        other = {}
        for name, handle in self.OTHER_COLLECTIONS:
            self.add_collection(other, name, handle, collector)
        self.add_collection(result, 'Other' if 'Other' not in result else 'Other2', '', collector, other)
        if not result:
            raise RuntimeError('Carpe navigation did not yield collection links')

        return result


class CarpeCatCol(ShopifyCatCol):
    parser_types = (CarpeMenuParser,)


if __name__ == '__main__':
    CarpeCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()



