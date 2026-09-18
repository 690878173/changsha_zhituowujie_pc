from lxml import etree

from config import base_url,Tool,zs

save_path = Tool.File.path_add_site('data/ml.json')


def f(dic,childs):
    for child in childs:
        _a = child.xpath('./a')[0]
        text,url = Tool.HTML.get_a_text_and_url(_a)
        dic[text] = {'url':Tool.URL.add_site(url),'child':{}}
        if len(child.xpath('./ul')) > 0:
            f(dic[text]['child'],child.xpath('./ul/li'))


    return dic




@zs('支持二级分类，三级未实现,数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url
    print(url)

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)


    ml1 = html.xpath('//*[@id="mobileOffCanvasWrapper"]/div/ul/li[2]')[0]

    a = ml1.xpath('./a')[0]
    text,url = Tool.HTML.get_a_text_and_url(a)

    url_dic[text] = {'url':Tool.URL.add_site(url), 'child':{} }


    lis = ml1.xpath('./div/ul/li')
    print(lis)



    url_dic = f(url_dic[text]['child'],lis)
    print(url_dic)
    return url_dic

def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



