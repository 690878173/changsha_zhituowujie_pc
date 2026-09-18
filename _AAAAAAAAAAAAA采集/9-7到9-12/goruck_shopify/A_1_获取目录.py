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

        skip_url_ls = ['/products/']
        # skip_url_ls = []
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

    ml1 = html.xpath('//nav[@class="drawer-menu-nav drawer-content scrollbar--hide"]/div')
    for node in ml1:


        _name = node.xpath('./div/div/header/span/text()')
        if not _name:
            continue
        _name = _name[0]
        _url = ''



        child_dic = Ml.add_node(dic, _name, _url)

        if isinstance(child_dic, dict):
            child = node.xpath('./div/div/div/a')

            f2(child_dic, child)

    ml1 = html.xpath('//nav[@class="drawer-menu-nav drawer-content scrollbar--hide"]/a')

    for node in ml1:
        name = node.xpath('./text()')[0]
        url = node.get('href')

        if '/products/' in url:
            continue

        url = Tool.URL.add_site(url)


        name = Ml.clean_text(name)

        dic[name] = {'url': url, 'child': {}}



    print(dic)
    return dic


def f2(dic:dict, child_ls:list):

    now_2_name = ''
    for node in child_ls:
        class_type = node.get('class')


        print(class_type)

        if class_type == 'drawer-submenu__item':
            url = node.get('href')
            # print(url)
            name = node.xpath('./text()')[0]


            Ml.add_node(dic, name, url)

            now_2_name = Ml.clean_text(name)

        elif class_type == 'drawer-subsubmenu__item':

            name = node.xpath('./text()')[0]
            url = node.get('href')

            if '/product/' in url:
                continue

            Ml.add_node(dic[now_2_name]['child'], name, url)

        else:
            print(f'未知标签')


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



