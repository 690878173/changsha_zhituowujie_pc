"""阶段 1：抓取 Rhode 的公开商品目录。"""

from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class RhodeMenuParser(CatalogParser):
    """解析 Rhode 首页 ``SHOP`` mega menu 及页面中的额外 collection 链接。"""

    nav_xpath = '//header[contains(concat(" ", normalize-space(@class), " "), " Header ")]'
    category_xpath = (
        './/*[@data-category and contains(concat(" ", normalize-space(@class), " "), '
        '" Navigation-menu-products ")]'
    )

    def matches(self, html):
        return 'Navigation-menu-products' in html and 'data-mega-menu="SHOP"' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @classmethod
    def link_text(cls, link):
        button_text = link.xpath(
            './/span[contains(concat(" ", normalize-space(@class), " "), '
            '" Button-base-text ")]/text()'
        )
        return ' '.join(' '.join(button_text).split()) or cls.text(link)

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower().rstrip('/')
        return path.startswith('/collections/') and path != '/collections'

    def add_collection(self, nodes, name, href, collector):
        url = collector.normalize_url(href)
        if not name or not self.is_collection(url):
            return None
        if name in nodes:
            suffix = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            name = f'{name} ({suffix})'
            counter = 2
            while name in nodes:
                name = f'{name} {counter}'
                counter += 1
        return collector.add_node(nodes, name, href)

    def collection_cta(self, category):
        links = category.xpath('.//a[@href]')
        return next(
            (
                link for link in links
                if self.is_collection(link.get('href') or '')
            ),
            None,
        )

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('Rhode homepage has no primary header')

        nav = navs[0]
        shop_links = nav.xpath('.//a[@data-mega-menu="SHOP" and @href]')
        if not shop_links:
            raise RuntimeError('Rhode homepage has no SHOP menu link')

        shop_link = shop_links[0]
        shop_children = {}
        for category in nav.xpath(self.category_xpath):
            name = (category.get('data-category') or '').strip()
            cta = self.collection_cta(category)
            if cta is not None:
                self.add_collection(shop_children, name, cta.get('href') or '', collector)

        result = {}
        collector.add_node(
            result,
            self.text(shop_link) or 'SHOP',
            shop_link.get('href') or '',
            shop_children,
        )

        # Preserve public collection links that live outside the site navigation.
        other = {}
        seen_urls = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header[contains(@class, "Header")]'):
                continue
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            if not self.is_collection(url) or url in seen_urls:
                continue
            name = self.link_text(link) or link.get('aria-label') or ''
            if not name or 'shipping' in name.lower():
                continue
            if self.add_collection(other, name, href, collector) is not None:
                seen_urls.add(url)

        if other:
            other_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, other_name, '', other)
        if not shop_children:
            raise RuntimeError('Rhode SHOP menu has no collection categories')
        return result


class RhodeCatCol(ShopifyCatCol):
    parser_types = (RhodeMenuParser,)


if __name__ == '__main__':
    RhodeCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()
