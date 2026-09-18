from lxml import etree

from config import base_url,Tool,zs

save_path = Tool.File.path_add_site('data/ml.json')



@zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    header__menu = html.xpath('//nav[@class="header__inline-menu"]/ul/li')[1]

    details = header__menu.xpath('.//details')[0]

    name = ''.join(details.xpath('./summary//text()')).strip()
    url = url

    url_dic[name] = {'url': url,'child':{}}
    m12 = details.xpath('./ul/li')

    url_dic = f2(url_dic[name]['child'], m12)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:
        a_ls = child.xpath('.//a')
        for a in a_ls:
            _text,url = Tool.HTML.get_a_text_and_url(a)

            url = Tool.URL.add_site(url)
            dic[_text] = {'url':url}

    return dic



def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



