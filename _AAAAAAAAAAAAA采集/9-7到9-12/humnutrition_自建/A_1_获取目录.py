from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')
from _ljp.mb.base.get_ml import BaseCatalogParser,CatCol

class Paraer(BaseCatalogParser):

    # f1 返回 {title:{url:str,child:{title:{title:str,child:{}}}}}
    def f1(self, html, dic):
        ml1 = html.xpath('//nav[@id="shop-navigation"]/ul/li/astro-island/div/astro-slot/div/astro-island/div/div')

        cd = ml1[1].xpath('./div/div/astro-slot/ul')
        ml = ml1[0].xpath('./div/ul/li/a')
        for index,node in enumerate(ml):

            a_node = node
            if a_node:
                _name, _url = Tool.HTML.get_a_text_and_url(a_node)
            else:
                _name = ''
                _url = ''
            if _url[-1] == '/':
                _url = _url[:-1]
            child_dic = self.collector.add_node(dic, _name, _url)
            print(child_dic)
            if isinstance(child_dic, dict):
                try:
                    child = cd[index].xpath('./li')
                except IndexError:
                    child = []

                self.f2(child_dic, child)



        dic['Shop Ingredients'] = dic['Curated Stacks']
        url = dic['Shop Ingredients'].pop(
            'url'
        )

        dic['Curated Stacks'] = {'url': url, 'child': {}}

    def f2(self, dic: dict, child_ls: list):
        return self.f3(dic, child_ls)
        for node in child_ls:

            _name = node.xpath('./span/text()')[0]
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
                _name, _url = Tool.HTML.get_a_text_and_url(a_node[0])
            else:
                _name = ''
                _url = ''

            if '/pages/' in _url:
                continue
            elif '/blogs/' in _url:
                continue
            else:
                _url = Tool.URL.add_site(_url)

            if _url[-1] == '/':
                _url = _url[:-1]

            tpy,_url = self.collector.check_url(_url)

            if _url:

                dic[_name] = {'url': _url, 'child': {}}


M = CatCol(Tool,base_url,save_path)

M.parser_types = (Paraer,)


if __name__ == '__main__':
    M.run()



