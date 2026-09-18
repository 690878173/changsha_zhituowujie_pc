from lxml import etree

from config import base_url,Tool,zs

save_path = Tool.File.path_add_site('data/ml.json')


def f(dic,childs):
    cs = childs.xpath('./div')
    n1 = cs[0].xpath('./div')
    n2 = cs[1].xpath('./div')



    for child in n1:
        a = child.xpath('./a')[0]
        data_tab = a.get('data-tab-target')
        m2_name,m2_url = Tool.HTML.get_a_text_and_url(a)
        m2_url = Tool.URL.add_site(m2_url)
        if m2_url in ['https://www.maono.com/collections/app-download']:
            continue

        dic[m2_name] = {'url':m2_url,'child':{}}
        for n in n2:
            if n.get('data-tab-panel').strip() == data_tab.strip():
                n_divs = n.xpath('./div[1]/div')

                for n_div in n_divs:
                    a = n_div.xpath('.//div[@class="mt-4"]/a')[0]
                    m3_name,m3_url = Tool.HTML.get_a_text_and_url(a)

                    m3_url = Tool.URL.add_site(m3_url)
                    if 'collections' not in m3_url:
                        continue

                    dic[m2_name]['child'][m3_name] = {'url':m3_url}



    return dic




@zs('支持二级分类，三级未实现,数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)
    url_dic['Product'] = {'url':base_url,'child':{}}

    ml1 = html.xpath('//vertical-tabs[@class="flex gap-x-4 py-8"]')[0]

    url_dic = f(url_dic['Product']['child'],ml1)
    print(url_dic)
    return url_dic

def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



