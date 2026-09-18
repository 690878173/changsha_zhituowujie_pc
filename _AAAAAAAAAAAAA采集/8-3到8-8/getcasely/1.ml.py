from lxml import etree

from config import base_url,Tool,zs

save_path = Tool.File.path_add_site('data/ml.json')

no_url_list  =['https://www.getcasely.com/discount/BUNDLE30']

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




@zs('支持二级分类，三级已实现,数据结构:{title:{url:xxx,child:{title:url或{url:xxx,child:{}}}}}')
def f1(url_dic):
    import re

    url = base_url
    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    no_ml_ls = ['Join the Club']
    ul = html.xpath('.//ul[@class="Header__desktop no-list-style"]/li[@class="Nav__item__main"]')

    for li in ul:
        ml1_name = ''.join(li.xpath('./*[@class="label-1 text-nounderline blk-txt" or @class="text-nounderline blk-txt label-1"]//text()')).strip()
        if not ml1_name:
            ml1_name = 'Cases'
        if ml1_name in no_ml_ls:
            continue

        # 一级链接
        ml1_a = li.xpath('.//a[contains(@class,"label-1") or contains(@class,"blk-txt")]')
        ml1_url = base_url + ml1_a[0].get('href', '') if ml1_a else base_url
        ml1_url = Tool.URL.del_par(ml1_url)
        print(f'一级:{ml1_name} -> {ml1_url}')

        url_dic[ml1_name] = {'url': ml1_url, 'child': {}}

        megamenu_div = li.xpath('./div[@class="Nav__megamenu no-js" or @class="Nav__list"]')
        if not megamenu_div:
            continue

        if 'Nav__list' in (megamenu_div[0].get('class') or ''):
            # Cases风格：Nav__list__child -> Nav__grandchild__list（含三级）
            opts = megamenu_div[0].xpath('./ul/li[contains(@class,"Nav__list__child")]')
            for opt in opts:
                gc_lis = opt.xpath('./ul[@class="Nav__list__grandchild no-list-style"]/li[@class="Nav__grandchild__list"]')
                for gc_li in gc_lis:
                    a_tag = gc_li.xpath('./a')
                    if not a_tag:
                        continue
                    ml2_name = re.sub(r'\s+', ' ', ''.join(a_tag[0].xpath('.//text()'))).strip()
                    ml2_url = a_tag[0].get('href', '')
                    if not ml2_name:
                        continue
                    full_ml2 = ml2_url if ml2_url.startswith('http') else base_url + ml2_url


                    full_ml2 = Tool.URL.del_par(full_ml2)
                    if full_ml2 in no_url_list:
                        continue

                    # 检查是否有三级 Nav__grandchild__items
                    ml3_as = gc_li.xpath('.//ul[@class="Nav__grandchild__items no-list-style"]//li[contains(@class,"Nav__grandchild__item") and not(contains(@class,"all-link"))]/a')
                    if ml3_as:
                        url_dic[ml1_name]['child'][ml2_name] = {'url': full_ml2, 'child': {}}
                        for ml3_a in ml3_as:
                            ml3_name = re.sub(r'\s+', ' ', ''.join(ml3_a.xpath('.//text()'))).strip()
                            ml3_url = ml3_a.get('href', '')
                            if ml3_name:
                                full_ml3 = ml3_url if ml3_url.startswith('http') else base_url + ml3_url
                                full_ml3 = Tool.URL.del_par(full_ml3)
                                url_dic[ml1_name]['child'][ml2_name]['child'][ml3_name] = full_ml3
                        print(f'  二级(含三级):{ml2_name} -> {full_ml2} (三级{len(ml3_as)}项)')
                    else:
                        url_dic[ml1_name]['child'][ml2_name] = full_ml2
                        print(f'  二级:{ml2_name} -> {full_ml2}')
        else:
            # 普通风格(Shop/MagSafe/Accessories/Collabs)：只取opt0分类链接
            opts = megamenu_div[0].xpath('./ul/li')
            if not opts:
                continue
            _lis = opts[0].xpath('./ul/li')
            for _li in _lis:
                if _li.xpath('./li'):
                    continue
                a_tag = _li.xpath('.//a')
                if a_tag:
                    ml2_name = re.sub(r'\s+', ' ', ''.join(a_tag[0].xpath('.//text()'))).strip()
                    ml2_url = a_tag[0].get('href', '')
                    if ml2_name:
                        full_url = ml2_url if ml2_url.startswith('http') else base_url + ml2_url
                        full_url = Tool.URL.del_par(full_url)
                        if full_url in no_url_list:
                            continue
                        url_dic[ml1_name]['child'][ml2_name] = full_url


                        print(f'  二级:{ml2_name} -> {full_url}')

    return url_dic

def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



