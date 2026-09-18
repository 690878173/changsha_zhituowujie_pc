"""阶段 1：抓取 Morphe 的公开商品目录。"""

import re
from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class MorpheMainMenuParser(CatalogParser):
    """解析 Morphe 的 ``Main menu`` 下拉导航及主体 collection 链接。"""

    nav_xpath = '//nav[@aria-label="Main menu"]'

    def matches(self, html):
        return 'aria-label="Main menu"' in html and 'js-header-dropdown' in html

    @staticmethod
    def text(node):
        return ' '.join(
            ' '.join(node.xpath('.//text()[not(ancestor::svg) and not(ancestor::script)]')).split()
        )

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower().rstrip('/')
        return path.startswith('/collections/') and path != '/collections'

    @classmethod
    def add_collection(cls, nodes, name, href, collector, child=None):
        normalized = collector.normalize_url(href)
        if not name or not cls.is_collection(normalized):
            return None
        candidate = name
        suffix = 2
        while candidate in nodes:
            candidate = f'{name} ({suffix})'
            suffix += 1
        return collector.add_node(nodes, candidate, href, child)

    def page_link_name(self, link):
        name = self.text(link) or (link.get('aria-label') or '').strip()
        if name.lower() not in {'shop all', 'shop now'}:
            return name
        for ancestor in link.xpath('ancestor::*[self::section or self::div]'):
            headings = ancestor.xpath('.//h1 | .//h2 | .//h3')
            if headings:
                heading = self.text(headings[0])
                if heading:
                    return heading
        return name

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('Morphe 首页没有 Main menu 导航')

        result = {}
        for item in navs[0].xpath('./ul/li'):
            details = item.xpath('./details[1]')
            if not details:
                links = item.xpath('./a[@href][1]')
                if links:
                    self.add_collection(
                        result,
                        self.text(links[0]),
                        links[0].get('href') or '',
                        collector,
                    )
                continue

            detail = details[0]
            names = detail.xpath('./summary[1]')
            shop_all = detail.xpath(
                './/*[contains(@class, "Dropdown__button--shop-all")]//a[@href][1]'
            )
            menu_links = detail.xpath(
                './/*[contains(@class, "Dropdown__menuWrapper")][1]'
                '//ul[contains(@class, "Dropdown__menu")][1]/li/a[@href]'
            )
            if not shop_all:
                # The Lips menu uses its first regular item as the Shop All link.
                shop_all = menu_links[:1]
            children = {}
            for link in menu_links:
                self.add_collection(
                    children,
                    self.text(link),
                    link.get('href') or '',
                    collector,
                )
            if names and shop_all:
                self.add_collection(
                    result,
                    self.text(names[0]),
                    shop_all[0].get('href') or '',
                    collector,
                    children,
                )

        if not result:
            raise RuntimeError('Morphe Main menu 没有可用目录')

        # Header duplicates the desktop menu for responsive layouts; only
        # collection links from the page body belong in the required Other group.
        other = {}
        seen_contexts = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header'):
                continue
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            section = link.xpath('ancestor::section[1]')
            context = section[0].getroottree().getpath(section[0]) if section else ''
            if not self.is_collection(url) or (context, url) in seen_contexts:
                continue
            name = re.sub(
                r'\s+shop now$',
                '',
                self.page_link_name(link),
                flags=re.IGNORECASE,
            )
            if self.add_collection(other, name, href, collector) is not None:
                seen_contexts.add((context, url))
        if other:
            other_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, other_name, '', other)

        return result


class MorpheCatCol(ShopifyCatCol):
    parser_types = (MorpheMainMenuParser,)


if __name__ == '__main__':
    MorpheCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()
