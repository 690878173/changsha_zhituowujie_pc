import json
from pathlib import Path

import requests
from lxml import etree
import urllib3

headers=None


from config import base_url,Tool as tool

Tool = tool

save_path = Tool.File.path_add_site('data/ml.json')

def f(dic,childs):
    for i,child in enumerate(childs):
        divs = child.xpath('./div')
        if len(divs) == 3:
            lis = divs[0].xpath('.//li')
            ml_name = dic['j__ljp__p'][i]
            dic[ml_name] = {'url': Tool.base_url+lis[0].xpath('./a/@href')[0], 'child': {}}
            for li in lis:
                a = li.xpath('.//a')[0]
                a_name = a.xpath('.//text()')
                name = ''.join(a_name).strip()
                a_url = a.get('href')
                dic[ml_name]['child'][name] = {'url':base_url + a_url}
            pass
        elif len(divs) == 2:
            a = divs[0].xpath('./div')[-1].xpath('.//a')[0]
            ml_name = dic['j__ljp__p'][i]
            url = a.get('href')
            print(url)
            dic[ml_name] = {'url': Tool.base_url + url, 'child': {}}

        else:
            print('qit')


    return dic


def f1(url_dic):
    global Tool

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//menu-block[@class="mega-menu-level-two-three grid grid-cols-12 gap-x-2 pt-6 pb-10 aria-hidden:hidden"]')
    name_l = html.xpath('//ul[@class="linklist gap-7 flex gap-y-0"]//li/button/text()')
    url_dic['j__ljp__p'] = [i.strip() for i in name_l]
    url_dic = f(url_dic,ml1)
    print(url_dic)
    return url_dic




def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



