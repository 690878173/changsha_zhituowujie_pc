"""阶段 1：抓取 Chubbies 的 React-stream 商品目录。"""

from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.mg_shopify.catalog import CatalogParser, CatCol, load_stream_data


class ChubbiesMenuParser(CatalogParser):
    """解析 Chubbies ``headerNavMenu`` 的 Shopify React stream 数据。"""

    menu_key = 'headerNavMenu'

    def matches(self, html):
        return self.menu_key in html and 'streamController.enqueue(' in html

    @staticmethod
    def resolve(data, value):
        if isinstance(value, int) and 0 <= value < len(data):
            return data[value]
        return value

    @classmethod
    def node_value(cls, data, node, key, default=''):
        if not isinstance(node, dict):
            return default
        return cls.resolve(data, node.get(key, default))

    @staticmethod
    def clean_name(value):
        name = str(value or '').split('$', 1)[0].split('|', 1)[0]
        return ' '.join(name.split())

    @staticmethod
    def collection_path(value):
        parts = urlsplit(str(value or ''))
        path = parts.path or ''
        if not path.startswith('/collections/'):
            return ''
        return path + (f'?{parts.query}' if parts.query else '')

    def add_item(self, data, item_ref, nodes, collector):
        item = self.resolve(data, item_ref)
        if not isinstance(item, dict):
            return None

        name = self.clean_name(self.node_value(data, item, '_32'))
        children = {}
        child_refs = self.node_value(data, item, '_2861', [])
        if isinstance(child_refs, list):
            for child_ref in child_refs:
                self.add_item(data, child_ref, children, collector)

        href = self.collection_path(self.node_value(data, item, '_164'))
        if not name or (not href and not children):
            return None
        return collector.add_node(nodes, name, href, children)

    def parse(self, html, collector):
        data = load_stream_data(html)
        try:
            menu_index = data.index(self.menu_key)
        except ValueError as exc:
            raise RuntimeError('Chubbies 首页缺少 headerNavMenu 数据') from exc

        menu_ref = self.resolve(data, data[menu_index + 1])
        menu_items = self.node_value(data, menu_ref, '_2861', [])
        if not isinstance(menu_items, list):
            raise RuntimeError('Chubbies headerNavMenu 不是菜单列表')

        result = {}
        for item_ref in menu_items:
            self.add_item(data, item_ref, result, collector)

        # 首页上不属于主导航的公开 collection 链接保留为 Other 二级目录。
        tree = lxml_html.fromstring(html)
        other = {}
        seen_urls = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header'):
                continue
            href = self.collection_path(link.get('href') or '')
            url = collector.normalize_url(href) if href else ''
            if not href or not url or url in seen_urls:
                continue
            name = self.clean_name(' '.join(link.xpath('.//text()[not(ancestor::svg)]')))
            name = name or self.clean_name(link.get('aria-label'))
            if not name:
                continue
            if collector.add_node(other, name, href) is not None:
                seen_urls.add(url)

        if other:
            other_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, other_name, '', other)
        if not result:
            raise RuntimeError('Chubbies headerNavMenu 没有 collection 目录')
        return result


if __name__ == '__main__':
    collector = CatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    )
    collector.parser_types = (ChubbiesMenuParser,)
    collector.run()
    Tool.close()
