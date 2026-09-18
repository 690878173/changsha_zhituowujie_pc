from lxml import etree

from config import base_url,Tool as tool,zs

headers=None

Tool = tool

save_path = Tool.File.path_add_site('data/ml.json')

def f2(dic, childs):
    for child in childs:

        name = child.get('id')
        dic[name] = {'url':'https://www.hatch.co/shop-all'}

    return dic




@zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):
    global Tool

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//ul[@data-orientation="horizontal"]/li/a')[0]
    text,url = Tool.HTML.get_a_text_and_url(ml1)
    url_dic[text] = {'url':Tool.URL.add_site(url),'child':{}}
    ml1 = []

    url = Tool.URL.add_site(url)
    res = Tool.get(url)
    html = etree.HTML(res.text)
    Tool.HTML.save(res.text)

    select = html.xpath('.//section[@class="style-module__QusUDq__collections grid-container"]/div')
    print(select)



    url_dic = f2(url_dic[text]['child'], select)
    print(url_dic)
    return url_dic





def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



