from pathlib import Path

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.mg_shopify import CatalogCollector
from _ljp.mb.mg_shopify.catalog import load_stream_data


HTML_DIR = Path(__file__).with_name('html')
HTML_PATH = HTML_DIR / 'home.html'
SAVE_PATH = Tool.File.path_add_site('data/ml.json')


class SiteCatalogCollector(CatalogCollector):
    """Parse Varley's full collection tree embedded in the home RSC stream."""

    @staticmethod
    def resolve(data, value):
        if isinstance(value, int) and 0 <= value < len(data):
            return data[value]
        return value

    def fetch_html(self):
        # Static HTML is the primary source. Preserve it for offline diagnosis.
        HTML_DIR.mkdir(parents=True, exist_ok=True)
        return super().fetch_html()

    def stream_link(self, data, value):
        node = self.resolve(data, value)
        if not isinstance(node, dict):
            return None
        name = self.resolve(data, node.get('_106'))
        url = self.resolve(data, node.get('_108'))
        if not isinstance(name, str) or not isinstance(url, str):
            return None
        return self.normalize_name(name), url

    def shop_all_groups(self, data):
        for node in data:
            if not isinstance(node, dict):
                continue
            collection = self.resolve(data, node.get('_101'))
            if not isinstance(collection, dict):
                continue
            title = self.resolve(data, collection.get('_106'))
            groups = self.resolve(data, node.get('_36'))
            if title == 'Shop All' and isinstance(groups, list):
                return groups
        raise RuntimeError('首页静态 React stream 中未找到 Shop All 目录树')

    def parse_shop_all(self, data):
        children = {}
        for group_ref in self.shop_all_groups(data):
            group = self.resolve(data, group_ref)
            if not isinstance(group, dict):
                continue
            group_name = self.resolve(data, group.get('_168'))
            link_refs = self.resolve(data, group.get('_44'))
            if not isinstance(group_name, str) or not isinstance(link_refs, list):
                continue

            group_url = ''
            group_children = {}
            for link_ref in link_refs:
                link = self.stream_link(data, link_ref)
                if not link:
                    continue
                name, url = link
                if name == group_name:
                    group_url = url
                else:
                    self.put_node(group_children, name, url, depth=2)
            if group_children or group_url:
                self.put_node(children, group_name, group_url, group_children, depth=1)
        if not children:
            raise RuntimeError('首页静态 React stream 中未解析到 Shop All 子目录')
        return children

    def parse_html(self, html):
        """Use direct header links plus the home page's embedded Shop All RSC menu."""
        tree = lxml_html.fromstring(html)
        menu = {}
        for link in tree.xpath('//header//nav//a[contains(@href, "/collections/")]'):
            name = self.normalize_name(' '.join(link.xpath('.//text()')))
            if name and name.casefold() != 'shop all':
                self.put_node(menu, name, link.get('href') or '', depth=0)

        menu['Shop All'] = {
            'url': self.normalize_url('/collections/all'),
            'child': self.parse_shop_all(load_stream_data(html)),
        }
        return menu


@Tool.zs('数据结构:{title:{url:xxx,child:{title:{url:xxx,child:{...}}}}}')
def f1():
    return SiteCatalogCollector(Tool, base_url, HTML_PATH, SAVE_PATH).run()


def run():
    menu = f1()
    Tool.print(f'已采集 {len(menu)} 个一级目录', color='green')


if __name__ == '__main__':
    try:
        run()
    finally:
        Tool.close()
