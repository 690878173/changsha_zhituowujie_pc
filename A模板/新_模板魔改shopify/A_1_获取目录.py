from config import Tool, base_url
from _ljp.mb.base.get_ml import BaseCatalogParser, CatCol


save_path = Tool.File.path_add_site('data/ml.json')

class Paraer(BaseCatalogParser):

    # f1 返回 {title:{url:str,child:{title:{title:str,child:{}}}}}
    def f1(self, html, dic):
        ml1 = html.xpath('//nav[@class="header__inline-menu"]/ul/li/header-menu/details')
        for node in ml1:

            names = node.xpath('./summary/span/text()')
            if not names:
                continue
            _name = names[0]
            _url = ''

            child_dic = self.collector.add_node(dic, _name, _url)
            if isinstance(child_dic, dict):
                child = node.xpath('./div/ul/li')

                self.f2(child_dic, child)

    def f2(self, dic: dict, child_ls: list):
        for node in child_ls:

            names = node.xpath('./span/text()')
            if not names:
                continue
            _name = names[0]
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

            if '/pages/' in _url:
                continue
            elif '/blogs/' in _url:
                continue
            else:
                _url = self.collector.tool.URL.add_site(_url)

            dic[_name] = {'url': _url, 'child': {}}


class MgShopifyCatCol(CatCol):
    parser_types = (*CatCol.parser_types,Paraer,)


if __name__ == '__main__':
    MgShopifyCatCol(Tool, base_url, save_path).run()
