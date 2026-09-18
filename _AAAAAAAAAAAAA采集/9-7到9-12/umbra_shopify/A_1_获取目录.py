from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')
from _ljp.mb.base.get_ml import BaseCatalogParser,CatCol

class Paraer(BaseCatalogParser):

    # f1 返回 {title:{url:str,child:{title:{title:str,child:{}}}}}
    def f1(self, html, dic):
        ml1 = html.xpath('//ul[@class="main-nav justify-center"]/li/details')
        for node in ml1:

            a_node = node.xpath('./summary/a')[0]
            _name,_url = Tool.HTML.get_a_text_and_url(a_node)

            child_dic = self.collector.add_node(dic, _name, _url)
            if isinstance(child_dic, dict):
                child = node.xpath('./div/ul/li')

                self.f2(child_dic, child)

        dic['Other'] = {'child':{}}

        lis = html.xpath('//li[@class="slider__item"]/div')
        num = 1
        for li in lis:
            div = li.xpath('./div[@class="card__info relative text-center"]/p/a')
            if div:
                _name,_url = Tool.HTML.get_a_text_and_url(div[0])
                _url = Tool.URL.add_site(_url)
                if num <9:

                    dic['Other']['child'][_name] = {'url':_url}

                    num +=1

    def f2(self, dic: dict, child_ls: list):
        for node in child_ls:

            a_node = node.xpath('./a')
            if not a_node:
                continue
            _name,_url = Tool.HTML.get_a_text_and_url(a_node[0])
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



