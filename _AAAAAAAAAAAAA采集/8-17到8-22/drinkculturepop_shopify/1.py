from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//div[@class="nav main-nav "]/ul/li')
    header_node = ml1


    for node in header_node:

        c_node = node.xpath('./a')[0]
        _name,_url = Tool.HTML.get_a_text_and_url(c_node)
        _url = _url
        _url = Tool.URL.add_site(_url)

        if 'pages/' in _url:
            continue

        url_dic[_name] = {'url':_url,'child':{}}

        childs = node.xpath('./ul/li')

        f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    f3(dic, childs)
    return dic
    for child in childs:

        continue
        c_node = child.xpath('./div[@class="xxxx"]')

        _name = ''
        _url = ''
        if 'collections' not in _url:
            continue
        _url = Tool.URL.add_site(_url)
        dic[_name] = {'url': _url, 'child': {}}

        n_childs_ls = []
        f3(dic[_name]['child'],n_childs_ls)

    return dic


def f3(dic,childs):
    for child in childs:
        c_a = child.xpath('./a')

        c_tx, c_url = Tool.HTML.get_a_text_and_url(c_a[0])
        _name = c_tx
        _url = c_url
        _url = Tool.URL.add_site(_url)

        dic[_name] = {'url': _url, 'child': {}}


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



