import json
from pathlib import Path

import requests
from lxml import etree
import urllib3


from base_f import base_url,Tool as tool,zs
Tool = tool



save_path = Tool.File.path_add_site('data/ml.json')








@zs('支持二级分类，三级未实现,数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):
    global Tool

    url = base_url

    res = Tool.get(url)

    html = etree.HTML(res.text)

    ml1 = html.xpath('//summary')[0]
    ml1_name = ''.join(ml1.xpath('.//text()')).strip()
    ml1_url = base_url+ml1.get('data-url')


    url_dic[ml1_name] = {'url': ml1_url,'child':{}}


    res = Tool.get(url)
    html = etree.HTML(res.text)

    # 分类二级链接
    ls = html.xpath('(//div[@class="hdt-sub-menu hdt-absolute hdt-dropdown-menu"])[1]/ul//li')
    for li in ls:
        n = ''.join(li.xpath('./a//text()')).strip().replace('\n', '')
        u = base_url+li.xpath('./a/@href')[0].strip()
        url_dic[ml1_name]['child'][n] = u





def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



