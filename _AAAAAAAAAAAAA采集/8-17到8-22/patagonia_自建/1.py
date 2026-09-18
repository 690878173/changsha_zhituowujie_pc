from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')


skip_url_ls = ['https://www.patagonia.com/shop/favorites/capilene-cool-tech-tees',
               'https://www.patagonia.com/shop/new-arrivals',
               'https://www.patagonia.com/search/?cgid=root',
               'https://www.patagonia.com/shop/gear/waders']


def is_skip(url):
    flsk = False
    for _url in skip_url_ls:
        if _url in url:
            flsk = True
            break
    return flsk


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//div[@class="js-primary-ssr-markup d-none"]/nav/ul/li')
    header_node = ml1


    for node in header_node:

        a_node = node.xpath('./a')
        if a_node:
            _name,_url = Tool.HTML.get_a_text_and_url(a_node[0])
            _url = Tool.URL.add_site(_url)

            if 'https://www.patagonia.com/shop/new-arrivals' in _url:
                continue
            url_dic[_name] = {'url': _url, 'child': {}}
        else:
            _name = node.xpath('./div/text()')[0].strip()
            _url = ''
            url_dic[_name] = {'child':{}}

        childs = node.xpath('./ul/li')

        f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for node in childs:
        a_node = node.xpath('./a')
        if a_node:
            _name, _url = Tool.HTML.get_a_text_and_url(a_node[0])
            _url = Tool.URL.add_site(_url)
            if '/shop/' not in _url:
                continue
            if is_skip(_url):
                continue
            dic[_name] = {'url': _url, 'child': {}}
        else:
            _name = node.xpath('./div/text()')
            if _name:
                _name = _name[0].strip()
            else:
                continue
            dic[_name] = {'child': {}}

        childs = node.xpath('./ul/li')
        f3(dic[_name]['child'],childs)

    return dic


def f3(dic,childs):
    for child in childs:
        c_a = child.xpath('./a')

        c_tx, c_url = Tool.HTML.get_a_text_and_url(c_a[0])
        _name = c_tx
        _url = c_url
        _url = Tool.URL.add_site(_url)
        if is_skip(_url):
            continue
        if '/shop/' not in _url:
            continue

        dic[_name] = {'url': _url, 'child': {}}


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



