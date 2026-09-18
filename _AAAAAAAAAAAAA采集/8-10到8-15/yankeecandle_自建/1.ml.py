import json
import re

from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')
js_path = Tool.File.path_add_site('hc/js.json')


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    js_code_str = html.xpath('//script[@id="mobify-data"]//text()')[0]
    data = json.loads(js_code_str)
    # print(data)

    data = data['__PRELOADED_STATE__']["__reactQuery"]["queries"]

    Tool.File.save_json(data,js_path)
    header_node = []

    data_ls = data[-1]["state"]["data"]["rootData"]["subcategories"]

    Tool.File.save_json(data_ls, js_path)

    for data in data_ls:
        title = data['title']
        url = data['categoryURL']

        title = title.replace('🎃 ','').replace('🏷️ ','')
        print(title,url)

        url = Tool.URL.add_site(url)
        url_dic[title] = {'url':url,'child':{}}


        def _F(dic,d_ls):
            for i in range(1, 10):
                key = f'subcategoriesColumn{i}'
                dt = d_ls.get(key)
                if dt:
                    for d in dt:
                        d_url = d['categoryURL']
                        d_name = d['title']
                        d_url = Tool.URL.add_site(d_url)
                        dic[d_name] = {'url':d_url,'child':{}}
                        _F(dic[d_name]['child'],d)

            cat = d_ls.get('subcategories')
            if cat:
                print(cat)
                for ct in cat:
                    c_url = ct['categoryURL']
                    c_name = ct['title']
                    c_url = Tool.URL.add_site(c_url)
                    dic[c_name] = {'url': c_url, 'child': {}}


        _F(url_dic[title]['child'],data)

    print(url_dic)
    return url_dic


    for node in header_node:

        c_node = node.xpath('./div[@class="xxxx"]')
        _name = ''
        _url = url
        _url = Tool.URL.add_site(_url)

        url_dic[_name] = {'url':_url,'child':{}}

        childs = []

        url_dic = f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:
        c_node = child.xpath('./div[@class="xxxx"]')

        _name = ''
        _url = ''

        _url = Tool.URL.add_site(_url)
        dic[_name] = {'url': _url, 'child': {}}

        n_childs_ls = []
        for n_child in n_childs_ls:
            n_node = n_child.xpath('./div[@class="xxxx"]')

            n_name = ''
            n_url = ''
            n_url = Tool.URL.add_site(n_url)
            dic[_name]['child'][n_name] = {'url': n_url, 'child': {}}

    return dic

def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



