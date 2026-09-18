"""阶段 1：抓取 Cirkul 的公开商品目录。"""

import json
from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class CirkulHeaderParser(CatalogParser):
    """解析首页 header React snippet 中的三级商品菜单。"""

    def matches(self, html):
        return 'data-react-snippet="header"' in html and '"menuItems"' in html

    @staticmethod
    def collection_url(url):
        if not url:
            return ''
        normalized = Tool.URL.add_site(url)
        if urlsplit(normalized).path.lower().startswith('/collections/'):
            return normalized
        return ''

    @staticmethod
    def label(value):
        return ' '.join(str(value or '').split())

    def add_node(self, nodes, name, url='', child=None):
        name = self.label(name)
        child = child or {}
        if not name or not (url or child):
            return
        node = {'url': url, 'child': child}
        if name not in nodes:
            nodes[name] = node
            return
        if nodes[name] == node:
            return
        suffix = 2
        candidate = f'{name} ({suffix})'
        while candidate in nodes:
            suffix += 1
            candidate = f'{name} ({suffix})'
        nodes[candidate] = node

    def parse_group(self, group):
        children = {}
        for link in group.get('subLinks') or []:
            self.add_node(
                children,
                link.get('label'),
                self.collection_url(link.get('link')),
            )
        return self.collection_url(group.get('link')), children

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        payload = tree.xpath(
            "string(//div[@data-react-snippet='header']"
            "//script[@type='application/json' and @data-react-snippet-data])"
        )
        menu_items = json.loads(payload).get('menuItems') or []
        result = {}

        for item in menu_items:
            children = {}
            category_groups = item.get('category_groups') or []
            if category_groups:
                for group in category_groups:
                    group_url, group_children = self.parse_group(group)
                    if group_url or group_children:
                        self.add_node(children, group.get('label'), group_url, group_children)
            else:
                for section in ('simple_links', 'featured_links'):
                    for link in item.get(section) or []:
                        self.add_node(
                            children,
                            link.get('label'),
                            self.collection_url(link.get('link')),
                        )

            item_url = self.collection_url(item.get('link'))
            if item_url or children:
                self.add_node(result, item.get('label'), item_url, children)
        return result


class CirkulCatCol(ShopifyCatCol):
    parser_types = (CirkulHeaderParser,)


if __name__ == '__main__':
    CirkulCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()
