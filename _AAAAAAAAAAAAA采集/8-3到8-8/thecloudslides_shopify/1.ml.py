from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')



@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//div[@class="Collapsible__Content"]//div')
    header_node = ['1']


    for node in header_node:

        c_node = html.xpath('//div[@class="Collapsible__Content"]//div')
        _name = 'All Collections'
        _url = Tool.URL.add_site('/collections/products')

        url_dic[_name] = {'url':_url,'child':{}}

        childs = c_node

        url_dic = f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:
        c_node = child.xpath('./a')[0]

        _name,_url = Tool.HTML.get_a_text_and_url(c_node)
        _url = Tool.URL.add_site(_url)
        dic[_name] = {'url': _url, 'child': {}}

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



