from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    data = Tool.HTML.extract_js_object(res.text)['topcategories']


    for node in data:

        _name = node['name']
        _url = node['url']
        _url = Tool.URL.add_site(_url)

        if _name in ['Gifts','About Us','Offers']:
            continue

        url_dic[_name] = {'url':_url,'child':{}}

        childs = node['subcategories']

        f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for node in childs:

        _name = node['name']
        _url = node['url']
        _url = Tool.URL.add_site(_url)

        if _name in ['Gifts', 'About Us', 'Offers']:
            continue

        dic[_name] = {'url': _url, 'child': {}}

        childs = node['subsubcategories']
        f3(dic[_name]['child'],childs)

    return dic


def f3(dic,childs):
    for node in childs:

        _name = node['name']
        _url = node['url']
        _url = Tool.URL.add_site(_url)

        if _name in ['Gifts', 'About Us', 'Offers']:
            continue

        dic[_name] = {'url': _url, 'child': {}}

        childs = node['subcategories']


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



