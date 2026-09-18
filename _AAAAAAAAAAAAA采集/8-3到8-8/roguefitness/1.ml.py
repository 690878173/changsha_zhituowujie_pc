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
        menu_link = child.xpath('.//div[@class="menu-link"]')[0]
        panel = child.xpath('.//div[@class="panel"]')[0]



        a = menu_link.xpath('.//a')[0]
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

    ml1 = html.xpath('//div[@class="mega-content"]//div[@class="menu-item top-level"]')




    url_dic = f(url_dic,ml1)
    print(url_dic)
    return url_dic

    for ml in ml1:
        a = ml.xpath('.//div[@class="menu-link"]/a')[0]
        name = a.xpath('.//text()')
        ml1_name = ''.join(name).strip()
        ml1_url = base_url + a.get('href', '')
        url_dic[ml1_name] = {'url': ml1_url, 'child': {}}

        print(ml1_name,ml1_url)

        cd = ml.xpath('.//div[@class="panel"]//div[@class="children"]/div')
        if not cd:
            cd = ml.xpath('.//div[@class="panel"]//div[@class="flat children"]/div')
        for c in cd:
            html_str = etree.tostring(c, encoding="utf-8", pretty_print=True).decode("utf-8")
            print(html_str)
            a = c.xpath('.//div[@class="menu-link"]//a')[0]
            name = a.xpath('.//text()')
            ml2_name = ''.join(name).strip()
            ml2_url = base_url + a.get('href', '')
            url_dic[ml1_name]['child'][ml2_name] = {'url': ml2_url, 'child': {}}

            print(ml2_name,ml2_url)






    print(url_dic)
    exit()

    res = Tool.get(url,headers=headers)
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



