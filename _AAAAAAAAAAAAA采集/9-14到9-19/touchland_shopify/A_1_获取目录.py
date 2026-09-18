from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')
from _ljp.mb.base.get_ml import BaseCatalogParser,CatCol

class Paraer(BaseCatalogParser):

    # f1 返回 {title:{url:str,child:{title:{title:str,child:{}}}}}
    def f1(self, html, dic):


        dic['Shop'] = {'url':'https://touchland.com/collections/shop-all','child':{}}



        ml1 = html.xpath('//div[@class="custom-nav__secondary gradient"]/subnav-slider/div/ul/li')
        for node in ml1:

            _name,_url = Tool.HTML.get_a_text_and_url(node.xpath('./a')[0])

            child_dic = self.collector.add_node(dic['Shop']['child'], _name, _url)
            print(child_dic)
            if isinstance(child_dic, dict):
                child = node.xpath('./div/ul/li')

                self.f2(child_dic, child)


        dic['Other'] = {'child':{}}


        ls = {'Accessories':'https://touchland.com/collections/accessories-2'}


        for k,v in ls.items():
            dic['Other']['child'][k] = {'url':v}

    def f2(self, dic: dict, child_ls: list):
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

            dic[_name] = {'url': _url, 'child': {}}


M = CatCol(Tool,base_url,save_path)

M.parser_types = (*M.parser_types,Paraer,)


if __name__ == '__main__':
    M.run()



