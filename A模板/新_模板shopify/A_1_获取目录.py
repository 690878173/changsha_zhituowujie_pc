from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')

def clean_text(values):
    if isinstance(values, str):
        values = [values]

    return ' '.join(' '.join(values).split())


def check_url(url):
    # 由具体站点覆盖,默认原路返回
    for i in []:
        if i in url:
            return 'skip',None
    if url in [Tool.URL.base_url]:
        return 'no_url',None

    for i in ['/pages/','/blogs/','/products/']:
        if i in url:
            return 'no_url',None
    return 'ok',url


def add_node(nodes, name, url='') ->dict|None:
    name = clean_text(name)
    if not name or name in nodes:
        print('skip',name)
        return None
        return

    children = {}
    url = Tool.URL.add_site(url)
    typ,url = check_url(url)

    if url or typ != 'skip':

        nodes[name] = {'url': url, 'child': children}

        return nodes[name]['child']

    else:

        return None



@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//div[@class="mega-content"]//div[@class="menu-item top-level"]')
    header_node = []


    for node in header_node:

        c_node = node.xpath('./div[@class="xxxx"]')
        _name = ''
        _url = url

        dic_child = add_node(url_dic, _name, _url)



        if not (dic_child is None):
            childs = node.xpath('./ul/li')
            if not childs:
                childs = node.xpath('./div/div/ul/li')

            f2(dic_child, childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:
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



