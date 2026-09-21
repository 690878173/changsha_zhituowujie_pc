from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class QuipMenuParser(CatalogParser):
    """Parse Quip's header mega menu and collection links in page content."""

    def matches(self, html):
        return 'data-header-block-menu-item' in html and 'menu-item__submenu' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower().rstrip('/')
        return path.startswith('/collections/') and '/products/' not in path

    def add_collection(self, nodes, name, href, collector):
        url = collector.normalize_url(href)
        if not name or not self.is_collection(url):
            return None
        return collector.add_node(nodes, name, url)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        result = {}
        known_urls = set()

        menu_items = tree.xpath(
            '//header-block//li[@data-header-block-menu-item and contains(@class, "menu-item")]'
        )
        for item in menu_items:
            top_link = item.xpath(
                './a[contains(@class, "menu-item__link")][@href]'
                ' | ./div[contains(@class, "menu-item__toggler")]/a[@href]'
            )
            if not top_link:
                continue

            top_name_node = top_link[0].xpath('./span[1]')
            top_name = self.text(top_name_node[0]) if top_name_node else self.text(top_link[0])
            top_url = collector.normalize_url(top_link[0].get('href') or '')
            top_children = {}

            for category_link in item.xpath(
                './div[contains(@class, "menu-item__submenu")]'
                '//div[contains(@class, "menu-item__categories")]/a[@href]'
            ):
                if self.add_collection(
                    top_children,
                    self.text(category_link),
                    category_link.get('href') or '',
                    collector,
                ) is not None:
                    known_urls.add(collector.normalize_url(category_link.get('href') or ''))

            for subitem in item.xpath(
                './div[contains(@class, "menu-item__submenu")]'
                '//li[contains(concat(" ", normalize-space(@class), " "), " menu-item__subitem ")]'
            ):
                leaf_link = subitem.xpath('./a[@href][1]')
                if leaf_link:
                    if self.add_collection(
                        top_children,
                        self.text(leaf_link[0]),
                        leaf_link[0].get('href') or '',
                        collector,
                    ) is not None:
                        known_urls.add(collector.normalize_url(leaf_link[0].get('href') or ''))
                    continue

                group_link = subitem.xpath('./div/a[@href][1]')
                if not group_link:
                    continue

                group_name = self.text(group_link[0])
                group_url = collector.normalize_url(group_link[0].get('href') or '')
                group_children = {}
                for child_link in subitem.xpath('./ul/li/a[@href]'):
                    if self.add_collection(
                        group_children,
                        self.text(child_link),
                        child_link.get('href') or '',
                        collector,
                    ) is not None:
                        known_urls.add(collector.normalize_url(child_link.get('href') or ''))

                if self.is_collection(group_url):
                    collector.add_node(top_children, group_name, group_url, group_children)
                    known_urls.add(group_url)
                elif group_children:
                    collector.add_node(top_children, group_name, '', group_children)

            if self.is_collection(top_url):
                collector.add_node(result, top_name, top_url, top_children)
                known_urls.add(top_url)
            elif top_children:
                collector.add_node(result, top_name, '', top_children)

        other = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header-block | ancestor::header | ancestor::nav | ancestor::footer'):
                continue
            href = link.get('href') or ''
            url = collector.normalize_url(href)
            if url in known_urls or not self.is_collection(url):
                continue
            name = self.text(link) or urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            if self.add_collection(other, name, href, collector) is not None:
                known_urls.add(url)

        if other:
            collector.add_node(result, 'Other' if 'Other' not in result else 'Other2', '', other)
        if not result:
            raise RuntimeError('Quip navigation did not yield collection links')
        return result


class QuipCatCol(ShopifyCatCol):
    parser_types = (QuipMenuParser,)


if __name__ == '__main__':
    QuipCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()



