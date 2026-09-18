import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lxml import etree

from config import base_url, Tool as tool, zs

headers = None

Tool = tool

save_path = Tool.File.path_add_site('data/ml.json')


def get_a_text(a):
    """从 <a> 标签中提取纯净的文本名称
    优先取 h3 > span > 全部文本，去掉多余描述
    """
    # 尝试取 h3
    h3 = a.xpath('.//h3')
    if h3:
        return ''.join(h3[0].xpath('.//text()')).strip()

    # 尝试取第一个有文本的 span
    spans = a.xpath('.//span')
    for sp in spans:
        cls = sp.get('class', '')
        txt = ''.join(sp.xpath('.//text()')).strip()
        if txt and 'sr-only' not in cls:
            return txt

    return ''.join(a.xpath('.//text()')).strip()


def f(dic, lis):
    """解析 nav 下的 li 列表，提取导航菜单"""
    for li in lis:
        divs = li.xpath('./div')
        if not divs:
            continue

        menu_div = divs[0]

        # 情况1: div[0] 包含 <a> 标签 (简单链接)
        a_tag = menu_div.xpath('.//a')
        if a_tag:
            a = a_tag[0]
            ml1_name = ''.join(a.xpath('.//text()')).strip()
            ml1_url = Tool.URL.add_site(a.get('href', ''))
            # dic[ml1_name] = {'url': ml1_url, 'child': {}}
            print(ml1_name, ml1_url)
            continue

        # 情况2: div[0] 包含 <button> 标签 (下拉菜单)
        btn_tag = menu_div.xpath('.//button')
        if btn_tag:
            ml1_name = ''.join(btn_tag[0].xpath('.//text()')).strip()
            print(ml1_name)

            dic[ml1_name] = {'url': '', 'child': {}}

            if len(divs) > 1:
                dropdown = divs[1]
                a_ls = dropdown.xpath('.//a')
                for idx, sub_a in enumerate(a_ls):
                    a_name = get_a_text(sub_a)
                    a_url = sub_a.get('href', '')
                    if a_name and a_url:
                        full_url = a_url if a_url.startswith('http') else Tool.URL.add_site(a_url)
                        dic[ml1_name]['child'][a_name] = full_url
                        if idx == 0:
                            dic[ml1_name]['url'] = full_url
            continue

    return dic


@zs('lumedeodorant 导航，一级用 button/a 区分是否有下拉')
def f1(url_dic):
    global Tool

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    nav = html.xpath('//nav')
    if not nav:
        print('未找到nav元素')
        return url_dic

    ml1 = nav[0].xpath('./ul/li')
    print(f'找到 {len(ml1)} 个一级菜单项')

    url_dic = f(url_dic, ml1)
    print(url_dic)
    return url_dic


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic, save_path)


if __name__ == '__main__':
    run()
