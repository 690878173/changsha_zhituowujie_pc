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
    for li in childs:
        div = li.xpath('./div')[0]
        name, url = Tool.HTML.find_child_a_text_and_url(div)
        url = Tool.base_url+url
        dic[name] = {'url':url}



    return dic




@zs('支持二级分类，三级未实现,数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):
    global Tool

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)
    z = html.xpath('//ul[@class="header__desktop-nav-list"]/li')[0]
    divs = z.xpath('./div')
    name,url = Tool.HTML.find_child_a_text_and_url(divs[0])
    url = Tool.base_url+url
    ml1 = divs[1].xpath('.//ul[@class="flyout-1__subnav-list"]/li')[:-1]



    url_dic[name] = {'url':url,'child':{}}
    url_dic = f(url_dic[name]['child'],ml1)
    print(url_dic)
    return url_dic




def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



