from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol


class ClevrBlendsCatalogParser(CatalogParser):
    """解析 Clevr Blends 的 ``g-header`` 桌面 megamenu。"""

    trigger_xpath = '//*[@data-megamenu-trigger]'
    page_group_name = 'Other'

    def matches(self, page_html):
        return (
            'g-header__megamenu__nav__link' in page_html
            and 'data-megamenu-trigger' in page_html
        )

    @staticmethod
    def text(node):
        return ' '.join(node.xpath('.//text()[not(ancestor::svg)]'))

    @staticmethod
    def is_collection_url(url):
        return '/collections/' in urlsplit(url).path.rstrip('/') + '/'

    def add_page_links(self, tree, collector, known):
        """将导航之外、尚未出现的首页 collection 链接归入 Other。"""
        other = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::*[@id="shopify-section-g-header"]'):
                continue
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            if not self.is_collection_url(url) or url in known:
                continue
            if urlsplit(url).path.rstrip('/').endswith('/collections'):
                continue
            name = collector.normalize_name(link.get('aria-label') or self.text(link))
            if collector.add_node(other, name, href) is not None:
                known.add(url)
        return other

    def parse(self, page_html, collector):
        tree = lxml_html.fromstring(page_html)
        catalog = {}
        known = set()

        for trigger in tree.xpath(self.trigger_xpath):
            target = trigger.get('data-megamenu-trigger')
            if not target:
                continue
            panels = tree.xpath(f'//*[@data-megamenu-target={target!r}]')
            if not panels:
                continue
            children = {}
            for link in panels[0].xpath(
                './/a[contains(concat(" ", normalize-space(@class), " "), '
                '" g-header__megamenu__nav__link ")][@href]'
            ):
                href = link.get('href') or ''
                url = collector.normalize_url(href)
                if not self.is_collection_url(url):
                    continue
                if collector.add_node(children, self.text(link), href) is not None:
                    known.add(url)
            if children:
                collector.add_node(catalog, self.text(trigger), '', child=children)

        if not catalog:
            raise RuntimeError('g-header megamenu 中没有可用 collection 目录')

        other = self.add_page_links(tree, collector, known)
        if other:
            collector.add_node(catalog, self.page_group_name, '', child=other)

        catalog['Shop The Sale,Shop The Sale Accessories'] = 'https://clevrblends.com/collections/accessories'
        catalog['Shop The Sale,Shop The Sale Energy'] = 'https://clevrblends.com/collections/energy'
        catalog['Shop The Sale,Shop The Sale Focus'] = 'https://clevrblends.com/collections/focus'
        catalog['Shop The Sale,Shop The Sale Sleep'] = 'https://clevrblends.com/collections/sleep'
        catalog['Shop The Sale,Shop The Sale Hydration'] = 'https://clevrblends.com/collections/hydration'
        return catalog


if __name__ == '__main__':
    collector = CatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
    )
    collector.parser_types = (ClevrBlendsCatalogParser, *collector.parser_types)
    collector.run()
