
from pathlib import Path
import sys
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol


if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


class PatternMenuParser(CatalogParser):
    """解析 Pattern 当前主题的桌面 mega menu 和首页 collection 卡片。"""

    nav_xpath = (
        '//nav[contains(concat(" ", normalize-space(@class), " "), '
        '" header__inline-menu ")]'
    )

    def matches(self, page_html):
        return 'header__inline-menu' in page_html and 'custom-mega-menu' in page_html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower().rstrip('/')
        return path.startswith('/collections/') and path != '/collections'

    @staticmethod
    def handle_name(url):
        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
        return handle.replace('-', ' ').title()

    def unique_name(self, nodes, name, url):
        name = name or self.handle_name(url)
        if name not in nodes:
            return name

        candidate = f'{name} ({self.handle_name(url)})'
        counter = 2
        while candidate in nodes:
            candidate = f'{name} ({self.handle_name(url)} {counter})'
            counter += 1
        return candidate

    def add_collection(self, nodes, name, href, collector):
        url = collector.normalize_url(href)
        if not self.is_collection(url):
            return None
        return collector.add_node(nodes, self.unique_name(nodes, name, url), url)

    def link_name(self, link, url):
        headings = link.xpath('.//h1[1] | .//h2[1] | .//h3[1] | .//h4[1]')
        if headings:
            name = self.text(headings[0])
            if name:
                return name

        name = (link.get('aria-label') or '').strip() or self.text(link)
        if name.lower() in {'shop now', 'learn more'}:
            return self.handle_name(url)
        return name or self.handle_name(url)

    def parse_menu(self, nav, collector):
        result = {}
        for item in nav.xpath('./ul/li'):
            direct_link = item.xpath('./a[@href][1]')
            if direct_link:
                link = direct_link[0]
                self.add_collection(
                    result,
                    self.text(link),
                    link.get('href') or '',
                    collector,
                )
                continue

            details = item.xpath('./header-menu/details[1]')
            if not details:
                continue
            details = details[0]
            menu_name = self.text(details.xpath('./summary[1]')[0])
            if not menu_name:
                continue

            children = {}
            groups = details.xpath(
                './div//ul[contains(concat(" ", normalize-space(@class), " "), '
                '" mega-menu__list ")]/li'
            )
            for group in groups:
                group_link = group.xpath('./a[@href][1]')
                group_name = self.text(group_link[0]) if group_link else ''
                leaves = {}
                for link in group.xpath(
                    './ul[contains(concat(" ", normalize-space(@class), " "), '
                    '" mega-menu-child-links ")]/li/a[@href]'
                ):
                    self.add_collection(
                        leaves,
                        self.text(link),
                        link.get('href') or '',
                        collector,
                    )

                if leaves:
                    collector.add_node(children, group_name, '', leaves)
                elif group_link:
                    self.add_collection(
                        children,
                        group_name,
                        group_link[0].get('href') or '',
                        collector,
                    )

            if children:
                collector.add_node(result, menu_name, '', children)
        return result

    def parse_page_links(self, tree, collector):
        other = {}
        seen_urls = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath(
                'ancestor::header | ancestor::header-drawer | ancestor::nav | '
                'ancestor::*[contains(concat(" ", normalize-space(@class), " "), '
                '" bottomMobileMenu ")]'
            ):
                continue
            url = collector.normalize_url(link.get('href') or '')
            if not self.is_collection(url) or url in seen_urls:
                continue
            name = self.link_name(link, url)
            if name.lower() == 'continue shopping':
                continue
            if self.add_collection(other, name, url, collector) is not None:
                seen_urls.add(url)
        return other

    def parse(self, page_html, collector):
        tree = lxml_html.fromstring(page_html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('Pattern homepage has no desktop navigation')

        result = self.parse_menu(navs[0], collector)
        if not result:
            raise RuntimeError('Pattern desktop navigation has no collection links')

        other = self.parse_page_links(tree, collector)
        if other:
            other_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, other_name, '', other)
        return result


if __name__ == '__main__':
    try:
        catalog = CatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '1' / 'homepage.html',
        )
        catalog.parser_types = (PatternMenuParser, *catalog.parser_types)
        catalog.run()
    finally:
        Tool.close()
