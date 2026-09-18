from lxml import etree

from config import base_url,Tool,zs

save_path = Tool.File.path_add_site('data/ml.json')



@zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    header__menu = html.xpath('//div[@class="header__menu"]//div')[0]
    all_name = header__menu.xpath('./div/button//text()')[0].strip()
    shopify_blocks = header__menu.xpath('.//div[@class="header-dropdown-group"]//div[@class="shopify-block"]')
    url_dic[all_name] = {'url':url,'child':{}}

    url_dic = f2(url_dic[all_name]['child'], shopify_blocks)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:
        a = child.xpath('./a')[0]
        _url = a.get('href')
        text = a.xpath('.//strong/text()')[0].strip()
        _url = Tool.URL.add_site(_url)
        dic[text] = {'url':_url}

    return dic



def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



