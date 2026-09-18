import json
from pathlib import Path

import requests
from lxml import etree
import urllib3


from base_f import base_url,Tool as tool

Tool = tool


def f1(url_dic):
    global Tool

    url = 'https://javvycoffee.com/collections/all'

    res = Tool.get(url)

    html = etree.HTML(res.text)

    ml1 = html.xpath('//a[@class="navbar-link min-w-fit"]')[0]
    ml1_name = ml1.xpath('./text()')[0].strip()
    ml1_url = base_url+ml1.get('href').strip()


    url_dic[ml1_name] = {'url': ml1_url,'child':{}}


    res = Tool.get(url)
    html = etree.HTML(res.text)

    ls = html.xpath('//div[@class="collection-heading"]/a')
    for i in ls:
        n = i.xpath('./div/p/text()')[0]
        u = base_url+i.get('href')
        url_dic[ml1_name]['child'][n] = u





def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic)


if __name__ == '__main__':
    run()



