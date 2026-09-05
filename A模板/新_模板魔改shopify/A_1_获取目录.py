from pathlib import Path

from config import Tool, base_url
from _ljp.mb.mg_shopify import CatalogCollector


HTML_PATH = Path(__file__).with_name('1.html')
SAVE_PATH = Tool.File.path_add_site('data/ml.json')


class SiteCatalogCollector(CatalogCollector):

    def fetch_html(self):
        return super().fetch_html()

    def create_parsers(self):
        return super().create_parsers()

    def select_parser(self, html):
        return super().select_parser(html)

    def parse_html(self, html):
        return super().parse_html(html)

    def normalize_name(self, value):
        return super().normalize_name(value)

    def normalize_url(self, url):
        return super().normalize_url(url)

    def should_keep_url(self, url):
        return super().should_keep_url(url)

    def should_keep_node(self, name, url, child, depth):
        return super().should_keep_node(name, url, child, depth)

    def put_node(self, nodes, name, url='', child=None, depth=0):
        return super().put_node(nodes, name, url, child, depth)

    def after_parse(self, menu):
        return super().after_parse(menu)

    def export_catalog(self, menu):
        return super().export_catalog(menu)


@Tool.zs('数据结构:{title:{url:xxx,child:{title:{url:xxx,child:{...}}}}}')
def f1():
    return SiteCatalogCollector(Tool, base_url, HTML_PATH, SAVE_PATH).run()


def run():
    menu = f1()
    Tool.print(f'已采集 {len(menu)} 个一级目录', color='green')


if __name__ == '__main__':
    run()
