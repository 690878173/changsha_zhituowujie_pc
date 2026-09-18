import json
from pathlib import Path

import requests
from lxml import etree
import urllib3

headers=None


from config import base_url,Tool as tool,zs

Tool = tool

save_path = Tool.File.path_add_site('data/ml.json')

def f(dic,childs):
    for child in childs:
        panel = child.xpath('.//div[@class="panel"]')[0]



        a = child.xpath('./a')[0]
        name = a.xpath('.//text()')
        
        ml1_name = ''.join(name).strip()
        ml1_url = base_url + a.get('href', '')

        dic[ml1_name] = {'url': ml1_url, 'child': {}}
        print(ml1_name,ml1_url)

        next_child = panel.xpath('.//div[@class="children"]/div')
        if not next_child:
            next_child = panel.xpath('.//div[@class="flat children"]/div')
        if next_child:
            f(dic[ml1_name]['child'],next_child)
        else:
            a_ls = panel.xpath('.//a')
            for a in a_ls:
                a_name = ''.join(a.xpath('.//text()')).strip()
                a_url = a.get('href')
                dic[ml1_name]['child'][a_name] = {'url':base_url + a_url}


    return dic




@zs('支持二级分类，三级未实现,数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):
    global Tool

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//li[@class="site-header__list-item"]')
    url_dic = f(url_dic,ml1)
    print(url_dic)
    return url_dic




def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



