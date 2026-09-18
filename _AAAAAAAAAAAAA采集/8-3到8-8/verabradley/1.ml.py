from lxml import etree

from config import base_url,Tool,zs

save_path = Tool.File.path_add_site('data/ml.json')


def f(dic,childs):
    for child in childs:
        menu_link = child.xpath('.//div[@class="menu-link"]')[0]
        panel = child.xpath('.//div[@class="panel"]')[0]



        a = menu_link.xpath('.//a')[0]
        name = a.xpath('.//text()')
        ml1_name = ''.join(name).strip()
        ml1_url = base_url + a.get('href', '')

        dic[ml1_name] = {'url': ml1_url, 'child': {}}
        print(ml1_name,ml1_url)

        next_child = panel.xpath('.//div[@class="children"]/div')
        if not next_child:
            next_child = panel.xpath('.//div[@class="flat children"]/div')
        if next_child:
            f(dic[ml1_name]['child'],next_child)
        else:
            a_ls = panel.xpath('.//a')
            for a in a_ls:
                a_name = ''.join(a.xpath('.//text()')).strip()
                a_url = a.get('href')
                dic[ml1_name]['child'][a_name] = base_url + a_url


    return dic




@zs('支持二级分类，数据结构:{ml1_name:{url:xxx,child:{ml2_name:url}}}')
def f1(url_dic):
    import re

    url = base_url
    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1_lis = html.xpath('//ul[@class="site-nav list-1"]/li')
    print(f'共找到 {len(ml1_lis)} 个一级导航项')

    for li in ml1_lis:
        # 一级：名称和链接
        ml1_a = li.xpath('./a[contains(@class,"desktop-nav-only")]')
        if not ml1_a:
            continue
        ml1_name = re.sub(r'\s+', ' ', ''.join(ml1_a[0].xpath('.//text()'))).strip()
        ml1_url = ml1_a[0].get('href', '')
        if not ml1_name:
            continue
        if ml1_url == '#':
            ml1_url = url
        full_ml1 = ml1_url if ml1_url.startswith('http') else base_url + ml1_url
        if ml1_name == 'Collaborations':
            full_ml1 = url
        print(f'一级:{ml1_name} -> {full_ml1}')

        url_dic[ml1_name] = {'url': full_ml1, 'child': {}}

        # 二级：dropdown中的column > ul > li.level-2
        ml2_lis = li.xpath('.//div[@class="dropdown-wrapper"]//li[contains(@class,"column")]/ul/li[@class="level-2"]/a[@class="nav-link"]')
        for ml2_a in ml2_lis:
            ml2_name = re.sub(r'\s+', ' ', ''.join(ml2_a.xpath('.//text()'))).strip()
            ml2_url = ml2_a.get('href', '')
            if ml2_name:
                full_ml2 = ml2_url if ml2_url.startswith('http') else base_url + ml2_url
                full_ml2 = full_ml2.split('?')[0]
                if 'collections' not in full_ml2:
                    continue
                url_dic[ml1_name]['child'][ml2_name] = full_ml2
                print(f'  二级:{ml2_name} -> {full_ml2}')

    return url_dic

def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



