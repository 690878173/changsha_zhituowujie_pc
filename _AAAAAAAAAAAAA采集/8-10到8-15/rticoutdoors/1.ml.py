import re
from lxml import etree

from config import base_url, Tool
from _ljp import zs

save_path = Tool.File.path_add_site('data/ml.json')

# 从JSON转义数据中提取的所有URL名称映射（已验证）
NAME_MAP = {
    '/shop/apparel': 'Apparel',
    '/shop/apparel/hats-beanies': 'Hats & Beanies',
    '/shop/apparel/hoodies': 'Hoodies',
    '/shop/apparel/sun-protection': 'R-Tech Sun Protection',
    '/shop/apparel/t-shirts': 'T-Shirts',
    '/shop/back-to-school': 'Back to School',
    '/shop/camp-and-cookout': 'Gear',
    '/shop/camp-and-cookout/camp-cookout': 'Camp & Cookout',
    '/shop/camp-and-cookout/clearance': 'Clearance Gear',
    '/shop/camp-and-cookout/sup-tubes': 'SUP & Tubes',
    '/shop/clearance-sale': 'Clearance',
    '/shop/clearance-sale/apparel': 'Apparel',
    '/shop/clearance-sale/bags': 'Bags',
    '/shop/clearance-sale/drinkware': 'Drinkware',
    '/shop/clearance-sale/gear': 'Gear',
    '/shop/clearance-sale/hard-coolers': 'Hard Coolers',
    '/shop/clearance-sale/soft-coolers': 'Soft Coolers',
    '/shop/coolers': 'Coolers',
    '/shop/coolers/hard-sided': 'Hard Coolers',
    '/shop/coolers/hard-sided/clearance': 'Clearance Hard Coolers',
    '/shop/coolers/hard-sided/hard-cooler-parts-and-accessories': 'Parts & Accessories',
    '/shop/coolers/hard-sided/original': 'Ultra-Tough Coolers',
    '/shop/coolers/hard-sided/ultra-light': 'Ultra-Light Coolers',
    '/shop/coolers/hard-sided/water-coolers': 'Water Coolers',
    '/shop/coolers/hard-sided/wheeled-coolers': 'Wheeled Coolers',
    '/shop/coolers/soft-sided': 'Soft Coolers',
    '/shop/coolers/soft-sided/accessories': 'Accessories',
    '/shop/coolers/soft-sided/backpack-coolers': 'Backpack Coolers',
    '/shop/coolers/soft-sided/clearance': 'Clearance Soft Coolers',
    '/shop/coolers/soft-sided/day-coolers': 'Day Coolers',
    '/shop/coolers/soft-sided/insulated-bags-and-totes': 'Insulated Bags & Totes',
    '/shop/coolers/soft-sided/lunch-bags-and-boxes': 'Lunch Bags & Boxes',
    '/shop/coolers/soft-sided/waterproof-coolers': 'Waterproof Coolers',
    '/shop/drinkware': 'Drinkware',
    '/shop/drinkware/accessories': 'Accessories',
    '/shop/drinkware/barware': 'Barware',
    '/shop/drinkware/bottles-jugs': 'Bottles & Jugs',
    '/shop/drinkware/can-coolers': 'Can Coolers',
    '/shop/drinkware/clearance': 'Clearance Drinkware',
    '/shop/drinkware/kid-friendly': 'Kid-Friendly',
    '/shop/drinkware/tumblers-mugs': 'Tumblers & Mugs',
    '/shop/kids': 'Kids',
    '/shop/thank-you-for-your-service': 'Thank You For Your Service',
    '/shop/totes-bags-and-duffles': 'Bags',
    '/shop/totes-bags-and-duffles/backpacks': 'Backpacks',
    '/shop/totes-bags-and-duffles/clearance': 'Clearance Bags',
    '/shop/totes-bags-and-duffles/duffles': 'Duffles',
    '/shop/totes-bags-and-duffles/insulated-bags': 'Insulated Bags',
    '/shop/totes-bags-and-duffles/totes': 'Totes',
}


def extract_all_categories(html_text):
    """从HTML的内嵌JSON中提取所有/shop/分类URL"""
    # 找到包含分类数据的最大script标签
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html_text, re.DOTALL)
    big = None
    for s in scripts:
        if len(s.strip()) > 50000 and 'hardCoolers' in s:
            big = s.strip()
            break

    if not big:
        return {}

    # 提取所有 \\"/shop/...\\" URL
    urls = re.findall(r'\\"(/shop/[^\\"]+)\\"', big)
    unique_urls = list(dict.fromkeys(urls))

    return unique_urls


def build_tree(urls):
    """根据URL路径深度构建嵌套目录树"""
    tree = {}

    for url in urls:
        name = NAME_MAP.get(url, url.split('/')[-1].replace('-', ' ').title())
        # 跳过第一个 'shop' 段，所有URL都以 /shop/ 开头
        parts = url.strip('/').split('/')
        if parts[0] == 'shop':
            parts = parts[1:]

        # 导航到正确的位置
        current = tree
        path_so_far = '/shop'
        for i, part in enumerate(parts):
            path_so_far = path_so_far + '/' + part

            if path_so_far == url:
                # 到达目标节点
                full_url = Tool.URL.add_site(url)
                current[name] = {'url': full_url, 'child': {}}
            else:
                # 中间节点：需要确保父节点存在
                parent_name = NAME_MAP.get(path_so_far, part.replace('-', ' ').title())
                if parent_name not in current:
                    parent_url = Tool.URL.add_site(path_so_far)
                    current[parent_name] = {'url': parent_url, 'child': {}}
                current = current[parent_name]['child']

    return tree


@zs('从1.html内嵌JSON提取完整目录结构,支持多级分类,数据结构:{title:{url:xxx,child:{title:url}}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url)
    Tool.HTML.save(res.text)

    # 从HTML内嵌JSON中提取全部分类URL
    all_urls = extract_all_categories(res.text)

    if not all_urls:
        Tool.print('未从HTML中提取到分类数据，回退到移动端菜单', color='yellow')
        html = etree.HTML(res.text)
        ml1 = html.xpath('//ul[contains(@class,"plum-mob-menu__menu-links")][1]/li/a')
        for a in ml1:
            text, href = Tool.HTML.get_a_text_and_url(a)
            url_dic[text] = {'url': Tool.URL.add_site(href), 'child': {}}
        print(url_dic)
        return url_dic

    # 按路径深度排序（父级在前），构建目录树
    all_urls.sort(key=lambda u: u.count('/'))
    tree = build_tree(all_urls)
    url_dic.update(tree)
    print(url_dic)
    return url_dic


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic, save_path)


if __name__ == '__main__':
    run()
