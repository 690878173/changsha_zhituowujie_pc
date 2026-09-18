from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')



@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//ul[@id="menu1"]//li')
    header_node = ['1']


    for node in header_node:

        # c_node = node.xpath('./div[@class="xxxx"]')
        _name = 'SHOP'
        _url = url

        url_dic[_name] = {'url':_url,'child':{}}

        childs = html.xpath('//ul[@id="menu1"]//li')

        url_dic = f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:
        # print(Tool.HTML.to_str(child))
        c_node = child.xpath('.//a')
        # exit()
        if not c_node:
            continue
        c_node = c_node[0]
        _url = c_node.get('href')
        if 'collections' not in _url:
            continue
        _url = Tool.URL.add_site(_url)
        _name = c_node.xpath('./p/text()')
        if not _name:
            _name = c_node.text
        else:
            _name = _name[0]

        dic[_name] = {'url': _url, 'child': {}}
        print(_name)
        n_childs_ls = []
        for n_child in n_childs_ls:
            n_node = n_child.xpath('./div[@class="xxxx"]')

            n_name = ''
            n_url = ''

            dic[_name]['child'][n_name] = {'url': n_url, 'child': {}}

    return dic

def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



