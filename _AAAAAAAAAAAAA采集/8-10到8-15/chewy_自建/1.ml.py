import json

from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')



@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    with open('./hc/2jscode.json','r',encoding='utf-8') as f:
        data = json.load(f)


    # data = Tool.File.load_json('./hc/2jscode.json')
    print(data)
    _d = data['Shop']['child']

    _d['Pharmacy'] = data['Pharmacy']


    def _c(dic):
        for k, v in dic.items():
            v['url'] = Tool.URL.add_site(v['url'])
            _c(v['child'])


    url_dic.update(_d)

    _c(url_dic)
    return url_dic

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//nav[@class="desktop-header__navigation"]/div/div')[:1]
    header_node = ml1


    for node in header_node:

        c_node = node.xpath('./div')[0]

        name_code = c_node.xpath('./div[1]/div/button/spam[1]//text()')
        _name = ''.join(name_code)


        ls = []
        url_code = c_node.xpath('./div[2]//div[@class="pet-navigation__featured"]')
        for url_c in url_code:
            links = url_c.xpath('./div[@class="link-section"]')
            ls.extend(links)

        _url = ''

        url_dic[_name] = {'url':_url,'child':{}}

        childs = ls
        print(ls)

        url_dic = f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:

        a_node = child.xpath('./a')[0]
        _name,_url = Tool.HTML.get_a_text_and_url(a_node)

        c_node = child.xpath('.//div[@class="link-section__links__item no-wrap"]')
        _name = _name.strip()

        _url = Tool.URL.add_site(_url)
        dic[_name] = {'url': _url, 'child': {}}

        n_childs_ls = c_node
        for n_child in n_childs_ls:
            n_node = n_child.xpath('./a')[0]
            n_name,n_url = Tool.HTML.get_a_text_and_url(n_node)

            n_name = n_name.strip()
            n_url = n_url
            n_url = Tool.URL.add_site(n_url)
            print(n_name,n_url)
            dic[_name]['child'][n_name] = {'url': n_url, 'child': {}}

    return dic

def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



