from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')


class Ml:

    @staticmethod
    def clean_text(values):
        if isinstance(values, str):
            values = [values.strip()]
        return ' '.join(' '.join(values).split())

    @staticmethod
    def check_url(url):

        skip_url_ls = ['/product/']
        skip_url_ls = []
        for i in skip_url_ls:
            if i in url:
                return 'skip',None

        if url in [Tool.URL.base_url,'']:
            return 'no_url',None


        no_url_ls = []
        for i in no_url_ls:
            if i in url:
                return 'no_url', None



        return 'ok',url

    @staticmethod
    def add_node(dic, name, url='') -> dict|None:
        name = Ml.clean_text(name)
        if not name or name in dic:
            print('skip',name)
            return None

        url = Tool.URL.add_site(url)
        typ, url = Ml.check_url(url)

        if url or typ != 'skip':

            dic[name] = {'url': url, 'child': {}}

            return dic[name]['child']
        else:
            return None


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//div[@class="mega-content"]//div[@class="menu-item top-level"]')
    for node in ml1:

        a_node = node.xpath('./div[@class="xxxx"]/a')
        if a_node:
            _name,_url = Tool.URL.get_a_text_and_url(a_node[0])

        else:
            _name = ''
            _url = ''



        child_dic = Ml.add_node(dic, _name, _url)

        if isinstance(child_dic, dict):
            child = node.xpath('./ul/li')

            f2(child_dic, child)

    print(dic)
    return dic


def f2(dic:dict, child_ls:list):
    for node in child_ls:
        a_node = node.xpath('./div[@class="xxxx"]')
        if a_node:
            _name,_url = Tool.URL.get_a_text_and_url(a_node[0])
        else:
            _name = ''
            _url = ''
        # if 'collections' not in _url:
        #     continue

        child_dic = Ml.add_node(dic, _name, _url)

        if isinstance(child_dic, dict):
            child = node.xpath('./ul/li')
            f3(child_dic, child)

    return dic


def f3(dic:dict,child_ls:list):

    for node in child_ls:
        a_node = node.xpath('./a')

        if a_node:
            _name, _url = Tool.URL.get_a_text_and_url(a_node[0])
        else:
            _name = ''
            _url = ''

        dic[_name] = {'url': _url, 'child': {}}


def run():
    dic = {}
    f1(dic)

    Tool.to_ml_json(dic,save_path)


if __name__ == '__main__':
    run()



