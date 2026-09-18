from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')



@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    header_node = html.xpath('//ul[@role="menubar"]/li[@role="menuitem"]')[:-1]

    print(header_node)


    for node in header_node:

        c_a = node.xpath('./a')

        c_tx,c_url = Tool.HTML.get_a_text_and_url(c_a[0])

        c_url = c_url.split('?')[0]
        c_node = node.xpath('./div/div/ul/li')
        _name = c_tx
        _url = Tool.URL.add_site(c_url)

        url_dic[_name] = {'url':_url,'child':{}}

        childs = c_node

        print(_name)

        f2(url_dic[_name]['child'], childs)

    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:


        c_a = child.xpath('./a')
        c_tx,c_url = Tool.HTML.get_a_text_and_url(c_a[0])

        c_node = child.xpath('./ul/li')

        _name = c_tx
        _url = c_url.split('?')[0]

        _url = Tool.URL.add_site(_url)

        dic[_name] = {'url': _url, 'child': {}}

        n_childs_ls = c_node
        for n_child in n_childs_ls:
            n_node = n_child.xpath('./a')
            n_tx,n_url = Tool.HTML.get_a_text_and_url(n_node[0])
            n_name = n_tx
            n_url = n_url.split('?')[0]
            n_url = Tool.URL.add_site(n_url)
            if 'https://freshcleantees.com/products/' in n_url:
                continue
            dic[_name]['child'][n_name] = {'url': n_url, 'child': {}}

    return dic

def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



