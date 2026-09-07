"""目录采集的公共基础能力。

普通 Shopify 和魔改 Shopify 的具体解析器必须放在各自的包中；本模块
只提供两者都需要的生命周期、节点钩子和输出策略。
"""

from pathlib import Path
from urllib.parse import urlsplit


def clean_text(value):
    """规范化目录名称。"""
    text = ' '.join(str(value or '').split())
    for suffix in (' ->', ' >'):
        if text.endswith(suffix):
            text = text[:-len(suffix)].rstrip()
    return text


def is_collection_url(url):
    """默认只允许 collection 链接，并排除 product 链接。"""
    path = urlsplit(url or '').path.lower()
    return '/collections' in path and '/product' not in path


class CatalogParser:
    """一个目录数据格式的解析器接口。"""

    def matches(self, html):
        raise NotImplementedError

    def parse(self, html, collector):
        raise NotImplementedError


class CatalogCollectorBase:
    """普通 Shopify 与魔改 Shopify 共用的采集生命周期。"""

    parser_types = ()

    def __init__(self, tool, base_url, html_path, save_path):
        self.tool = tool
        self.base_url = base_url
        self.html_path = Path(html_path)
        self.save_path = save_path

    def fetch_html(self):
        """优先请求首页并保存原始 HTML，请求失败时使用本地快照。"""
        response = self.tool.get(self.base_url)
        if response.status_code == 200 and response.text:
            self.tool.HTML.save_raw(response.text, self.html_path)
            return response.text
        if self.html_path.exists():
            self.tool.print(f'首页请求失败（{response.status_code}），使用本地 HTML', color='yellow')
            return self.html_path.read_text(encoding='utf-8')
        raise RuntimeError(f'首页请求失败（{response.status_code}），且本地 HTML 不存在')

    def create_parsers(self):
        """返回当前包内置的解析器实例。"""
        return [item() if isinstance(item, type) else item for item in self.parser_types]

    def select_parser(self, html):
        """按当前包的解析器顺序选择第一个匹配的策略。"""
        for parser in self.create_parsers():
            if parser.matches(html):
                return parser
        raise RuntimeError('首页中未识别到支持的 Shopify 目录数据')

    def parse_html(self, html):
        return self.select_parser(html).parse(html, self)

    def normalize_name(self, value):
        return clean_text(value)

    def normalize_url(self, url):
        return self.tool.URL.add_site(url) if url else ''

    def should_keep_url(self, url):
        return is_collection_url(url)

    def should_keep_node(self, name, url, child, depth):
        return bool(name)

    def put_node(self, nodes, name, url='', child=None, depth=0):
        """写入节点，并统一执行站点可覆写的字段和过滤钩子。"""
        name = self.normalize_name(name)
        child = child or {}
        url = self.normalize_url(url)
        if url and not self.should_keep_url(url):
            url = ''
        if not self.should_keep_node(name, url, child, depth):
            return
        item = nodes.setdefault(name, {'url': '', 'child': {}})
        if url and not item['url']:
            item['url'] = url
        if child:
            item['child'].update(child)

    def after_parse(self, menu):
        return menu

    def export_catalog(self, menu):
        self.tool.to_ml_json(menu, self.save_path)

    def run(self):
        menu = self.after_parse(self.parse_html(self.fetch_html()))
        self.export_catalog(menu)
        return menu


__all__ = [
    'CatalogCollectorBase',
    'CatalogParser',
    'clean_text',
    'is_collection_url',
]
