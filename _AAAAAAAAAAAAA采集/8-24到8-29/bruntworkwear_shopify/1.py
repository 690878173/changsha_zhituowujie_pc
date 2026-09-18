from lxml import etree
import re
from config import base_url, Tool

save_path = Tool.File.path_add_site('data/ml.json')

def clean_text(text):
    """清理文本：去除多余空白、换行、以及残留的图标占位符"""
    if not text:
        return ''
    # 去除换行和多余空格
    text = ' '.join(text.split())
    # 移除类似 'icon-arrow-right@3x' 这样的残留
    text = re.sub(r'icon-arrow-right@3x', '', text)
    # 移除其他可能出现的 SVG 占位字符串
    text = re.sub(r'<[^>]+>', '', text)  # 安全措施
    return text.strip()

@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):
    url = base_url
    res = Tool.get(url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    # 定位所有一级条目（直接位于 sidebarMenu__subNavWrapper 下的 shopify-block）
    # 注意：外层 wrapper 可能不唯一，这里取第一个（或根据实际情况调整）
    wrapper = html.xpath('//div[contains(@class, "sidebarMenu__subNavWrapper")]')[0]
    top_blocks = wrapper.xpath('./div[contains(@class, "shopify-block") and contains(@class, "sidebarMenu__subNav")]')

    for block in top_blocks:
        # 检查是否有子菜单（即包含 navOption）
        nav_option = block.xpath('./div[contains(@class, "sidebarMenu__navOption")]')
        if not nav_option:
            # 没有子菜单，是直接链接
            a_node = block.xpath('./a[contains(@class, "sidebarMenu__navLink")]')
            if a_node:
                name, link = Tool.HTML.get_a_text_and_url(a_node[0])
                name = clean_text(name)
                if 'collections' not in link:
                    continue
                link = Tool.URL.add_site(link)
                url_dic[name] = {'url': link, 'child': {}}
        else:
            # 有子菜单，进入处理
            sub_menu = nav_option[0].xpath('./div[contains(@class, "sidebarMenu__subMenu")]')
            if sub_menu:
                # 提取一级名称（通常是按钮上的文本）
                trigger_btn = block.xpath('.//button[contains(@class, "js-subNavTrigger")]')
                if trigger_btn:
                    parent_name = clean_text(trigger_btn[0].xpath('string(.)'))
                else:
                    parent_name = 'Unknown'
                # 先创建一个临时字典，用于存放该一级下的所有子项
                child_dict = {}
                # 处理子菜单内部
                process_sub_menu(sub_menu[0], child_dict)
                # 将一级节点加入主字典
                url_dic[parent_name] = {'url': None, 'child': child_dict}

    print(url_dic)
    return url_dic

def process_sub_menu(sub_menu_node, parent_dict):
    """
    递归处理子菜单节点，提取二级、三级链接，并填充到 parent_dict 中。
    parent_dict 的格式与主字典一致。
    """
    # 1. 处理 "Shop All XXX" 链接
    shop_all = sub_menu_node.xpath('.//a[contains(@class, "sidebarMenu__shopAll")]')
    for a in shop_all:
        name, link = Tool.HTML.get_a_text_and_url(a)
        name = clean_text(name)
        # 可能同时存在多个，但通常只有一个
        if name and link:
            if '/products/' in link:
                continue
            link = Tool.URL.add_site(link)
            parent_dict[name] = {'url': link, 'child': {}}

    # 2. 处理其他直接链接（例如 Apparel 下的 Pants & Shorts 等）
    # 这些链接在 sub_menu 下的 sidebarMenu__subNavWrapper 内，且是直接的 <a>（不包含在折叠面板中）
    sub_wrapper = sub_menu_node.xpath('.//div[contains(@class, "sidebarMenu__subNavWrapper")]')
    if sub_wrapper:
        wrapper_node = sub_wrapper[0]
        # 获取所有直接子 <a> 标签（排除已经在 shopAll 中处理过的）
        direct_links = wrapper_node.xpath('./a[not(contains(@class, "sidebarMenu__shopAll"))]')
        for a in direct_links:
            name, link = Tool.HTML.get_a_text_and_url(a)
            name = clean_text(name)
            if name and link:
                if '/products/' in link:
                    continue
                link = Tool.URL.add_site(link)
                parent_dict[name] = {'url': link, 'child': {}}

        # 3. 处理折叠面板 (accordion)
        accordion_buttons = wrapper_node.xpath('./button[contains(@class, "subMenu__menuAccordion")]')
        for btn in accordion_buttons:
            # 提取二级标题（即按钮文本）
            sec_name = clean_text(btn.xpath('string(.)'))
            # 对应的展开区域
            accordion_id = btn.get('data-sub-nav')
            # 查找紧随其后的 div.subMenu__navAccordion（注意：可能按兄弟关系，或通过 data-sub-nav 关联）
            # 但更可靠的是：获取下一个兄弟元素（在HTML中，按钮和展开div是相邻的）
            next_sibling = btn.getnext()
            if next_sibling is not None and 'subMenu__navAccordion' in next_sibling.get('class', ''):
                accordion_content = next_sibling
            else:
                # 备用：通过 data-sub-nav 查找
                accordion_content = wrapper_node.xpath(f'.//div[@data-sub-nav="{accordion_id}"]')
                accordion_content = accordion_content[0] if accordion_content else None

            if accordion_content is not None:
                # 三级链接列表
                third_level_links = accordion_content.xpath('.//a')
                child_of_sec = {}
                for a in third_level_links:
                    # 提取链接文本和 href
                    name, link = Tool.HTML.get_a_text_and_url(a)
                    name = clean_text(name)
                    if name and link:
                        if '/products/' in link:
                            continue
                        link = Tool.URL.add_site(link)
                        child_of_sec[name] = {'url': link, 'child': {}}
                # 将二级标题作为节点，其 child 包含三级链接
                parent_dict[sec_name] = {'url': None, 'child': child_of_sec}

        # 4. 处理特殊区域：如 "Shop Women's Boots"（位于 sidebarMenu__womenLinkOut）
        women_links = wrapper_node.xpath('.//div[contains(@class, "sidebarMenu__womenLinkOut")]//a')
        for a in women_links:
            name, link = Tool.HTML.get_a_text_and_url(a)
            name = clean_text(name)
            if name and link:
                if '/products/' in link:
                    continue
                link = Tool.URL.add_site(link)
                parent_dict[name] = {'url': link, 'child': {}}

def run():
    url_dic = {}
    f1(url_dic)
    Tool.to_ml_json(url_dic, save_path)

if __name__ == '__main__':
    run()