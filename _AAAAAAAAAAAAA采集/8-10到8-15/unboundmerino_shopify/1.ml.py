from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')



@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//ul[@class="list-menu"]/li/div')
    header_node = ml1


    for node in header_node:

        c_a = node.xpath('./a')

        c_tx,c_url = Tool.HTML.get_a_text_and_url(c_a[0])

        c_node = node.xpath('./div/ul/li')
        _name = c_tx.replace('\n','').replace(' ','')
        _url = c_url
        _url = Tool.URL.add_site(_url)
        if _name == 'About':
            continue

        url_dic[_name] = {'url':_url,'child':{}}

        childs = c_node

        f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:

        c_a = child.xpath('./a')



        c_node = child.xpath('./ul/li')
        if c_a:
            c_tx, c_url = Tool.HTML.get_a_text_and_url(c_a[0])

            _name = c_tx.replace('\n  \n    NEW','')
            _url = c_url
            _url = Tool.URL.add_site(_url)


            dic[_name] = {'url': _url, 'child': {}}

            f3(dic[_name]['child'], c_node)

        else:
            f3(dic,c_node)


    return dic


def f3(dic,childs):
    for child in childs:

        c_a = child.xpath('./a')

        c_tx, c_url = Tool.HTML.get_a_text_and_url(c_a[0])
        _name = c_tx.replace('\n  \n    NEW','')
        _url = c_url
        _url = Tool.URL.add_site(_url)

        dic[_name] = {'url': _url, 'child': {}}


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



