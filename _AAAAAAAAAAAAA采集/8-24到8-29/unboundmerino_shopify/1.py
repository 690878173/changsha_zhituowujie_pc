from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//nav[@class="header__desktop-menu"]/ul/li/div')[:2]
    header_node = ml1

    for node in header_node:

        c_node = node.xpath('./a')
        _name,_url = Tool.HTML.get_a_text_and_url(c_node[0])

        _url = Tool.URL.add_site(_url)

        url_dic[_name] = {'url':_url,'child':{}}

        childs = node.xpath('./div[@class="mega-menu__content"]/ul/li[@class="mega-menu__menu-wrapper"]')

        f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for i in childs:
        
    for child in childs:

        n_childs_ls = child.xpath('./ul/li')

        c_node = child.xpath('./a')
        if c_node:

            _name,_url = Tool.HTML.get_a_text_and_url(c_node[0])

        elif child.xpath('./div/a'):
            a = child.xpath('./div/a')[0]
            _url = a.get('href')
            _name = a.xpath('./div[@class="mega-menu__item-title"]/p/text()')[0]
        else:
            f3(dic,n_childs_ls)
            continue
        if 'collections' not in _url:
            continue

        _name = _name.strip().replace('\n  \n    NEW','')
        _url = Tool.URL.add_site(_url)
        dic[_name] = {'url': _url, 'child': {}}


        f3(dic[_name]['child'],n_childs_ls)

    return dic


def f3(dic,childs):
    for child in childs:
        c_a = child.xpath('./a')

        c_tx, c_url = Tool.HTML.get_a_text_and_url(c_a[0])
        _name = c_tx.strip().replace('\n  \n    NEW','')
        _url = c_url
        _url = Tool.URL.add_site(_url)
        if 'collections' not in _url:
            continue

        dic[_name] = {'url': _url, 'child': {}}


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



