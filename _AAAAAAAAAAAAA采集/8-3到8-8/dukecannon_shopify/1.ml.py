from lxml import etree

from config import base_url,Tool,zs

save_path = Tool.File.path_add_site('data/ml.json')



@zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    header = html.xpath('//div[@class="header-item header-item--navigation"]/ul/li')[0]

    name = ''.join(header.xpath('./button//text()')).strip()

    url_dic[name] = {'url':url,'child':{}}


    lis = header.xpath('.//ul[@class="grid"]/li')

    url_dic = f2(url_dic[name]['child'], lis)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:
        divs = child.xpath('./div')

        _name,_url = Tool.HTML.get_a_text_and_url(divs[0].xpath('./a')[0])
        print(_url)
        _url = Tool.URL.add_site(_url)

        dic[_name] = {'url':_url,'child':{}}
        print(_url)

        for _c in divs[1:]:
            _c_name, _c_url = Tool.HTML.get_a_text_and_url(_c.xpath('./a')[0])
            if 'collections' not in _c_url:
                continue
            _c_url = Tool.URL.add_site(_c_url)

            dic[_name]['child'][_c_name] = {'url':_c_url,'child':{}}

    return dic



def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



