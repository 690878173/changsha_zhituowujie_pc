from pathlib import Path
from typing import TYPE_CHECKING
from lxml import etree

if TYPE_CHECKING:
    from ...base_tool import Base_tool

class CatalogParser:
    """一个目录数据格式的解析器接口。"""

    def matches(self, res_text):
        #检查是否是这个格式
        raise NotImplementedError

    def parse(self, res_text, collector:"CatCol"):
        raise NotImplementedError

class BaseCatalogParser(CatalogParser):

    def matches(self, res_text):
        # 基础默认返回真
        return True


    def parse(self, res_text, collector):
        dic = {}
        self.collector = collector
        html = etree.HTML(res_text)
        self.f1(html,dic)

        return dic

    # f1 返回 {title:{url:str,child:{title:{title:str,child:{}}}}}
    def f1(self, html, dic):
        ml1 = html.xpath('//div[@class="mega-content"]//div[@class="menu-item top-level"]')
        for node in ml1:

            a_node = node.xpath('./div[@class="xxxx"]/a')
            if a_node:
                _name, _url = self.collector.tool.HTML.get_a_text_and_url(a_node[0])

            else:
                _name = ''
                _url = ''

            child_dic = self.collector.add_node(dic, _name, _url)

            if isinstance(child_dic, dict):
                child = node.xpath('./ul/li')

                self.f2(child_dic, child)

    def f2(self, dic: dict, child_ls: list):
        for node in child_ls:
            a_node = node.xpath('./div[@class="xxxx"]')
            if a_node:
                _name, _url = self.collector.tool.HTML.get_a_text_and_url(a_node[0])
            else:
                _name = ''
                _url = ''
            # if 'collections' not in _url:
            #     continue

            child_dic = self.collector.add_node(dic, _name, _url)

            if isinstance(child_dic, dict):
                child = node.xpath('./ul/li')
                self.f3(child_dic, child)

        return dic

    def f3(self, dic: dict, child_ls: list):
        for node in child_ls:
            a_node = node.xpath('./a')

            if a_node:
                _name, _url = self.collector.tool.HTML.get_a_text_and_url(a_node[0])
            else:
                _name = ''
                _url = ''

            dic[_name] = {'url': _url, 'child': {}}

class CatCol:
    parser_types = ()

    skip_url_ls = []
    no_url_ls = []

    def __init__(self, tool, base_url, save_path,html_path='1.html'):
        self.tool = tool
        self.base_url = base_url
        self.save_path = save_path
        self.html_path = Path(html_path)

    def fetch(self):
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

    def select_parser(self, res_text):
        """按当前包的解析器顺序选择第一个匹配的策略。"""
        for parser in self.create_parsers():
            if parser.matches(res_text):
                return parser
        raise RuntimeError('首页中未识别到支持的 目录数据')

    def parse(self, res_text):
        return self.select_parser(res_text).parse(res_text, self)

    @staticmethod
    def normalize_name(values):
        if values is None:
            return ''
        if isinstance(values, str):
            values = [values.strip()]
        text =  ' '.join(' '.join(values).split())

        for suffix in (' ->', ' >'):
            if text.endswith(suffix):
                text = text[:-len(suffix)].rstrip()


        text = text.replace(', ', ' ').replace(',', ' ')


        return text

    def normalize_url(self, url):
        return self.tool.URL.add_site(url) if url else ''

    def check_url(self, url):

        for i in self.skip_url_ls:
            if i in url:
                return 'skip', None

        if url in [self.tool.URL.base_url, '']:
            return 'no_url', None

        for i in self.no_url_ls:
            if i in url:
                return 'no_url', None

        return 'ok', url

    def add_node(self,dic,name,url='',child=None):
        name = self.normalize_name(name)
        if not name or name in dic:
            print('skip', name)
            return None

        url = self.tool.URL.add_site(url)
        typ, url = self.check_url(url)

        if url or typ != 'skip':

            dic[name] = {'url': url, 'child': child or {}}

            return dic[name]['child']
        else:
            return None

    def after_parse(self, menu):
        return menu

    def export_catalog(self, menu):
        self.tool.to_ml_json(menu, self.save_path)

    def run(self):
        menu = self.after_parse(self.parse(self.fetch()))
        self.export_catalog(menu)
        print(menu)
        return menu





