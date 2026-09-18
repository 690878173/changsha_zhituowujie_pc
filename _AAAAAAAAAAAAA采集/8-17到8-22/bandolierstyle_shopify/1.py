import re

from lxml import etree

from config import base_url, Tool

save_path = Tool.File.path_add_site('data/ml.json')


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):
    res = Tool.get(base_url)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)
    parse_menu(html, url_dic)
    return url_dic


def parse_menu(html, url_dic):
    menus = html.xpath(
        '//nav[contains(concat(" ", normalize-space(@class), " "), " navx-drawer ")]'
    )
    if not menus:
        return url_dic

    for section in menus[0].xpath('./div[contains(concat(" ", normalize-space(@class), " "), " navx-drawer__section ")]'):
        names = section.xpath(
            './button//*[contains(concat(" ", normalize-space(@class), " "), " navx-drawer__label ")]/text()'
        )
        name = ''.join(names).strip()
        if not name:
            continue

        url_dic[name] = {'url': '', 'child': {}}
        rows = section.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), " navx-drawer__panel ")]'
            '/div[contains(concat(" ", normalize-space(@class), " "), " navx-acc__panel-inner ")]'
            '/*[contains(concat(" ", normalize-space(@class), " "), " navx-drawer__row ")]'
        )
        add_collection_nodes(url_dic[name]['child'], rows)

    return url_dic


def add_collection_nodes(dic, rows):
    stack = {}
    row_levels = [get_level(row) for row in rows]

    for index, row in enumerate(rows):
        level = row_levels[index]
        name = get_name(row)
        if not level or not name:
            continue

        for stack_level in tuple(stack):
            if stack_level >= level:
                del stack[stack_level]

        url = row.get('href', '').strip()
        has_children = has_descendants(row_levels, index, level)

        if is_collection_url(url):
            node = {'url': Tool.URL.add_site(url), 'child': {}}
        elif not url and has_children:
            node = {'url': '', 'child': {}}
        else:
            continue

        parent = dic
        parent_levels = [stack_level for stack_level in stack if stack_level < level]
        if parent_levels:
            parent = stack[max(parent_levels)]['child']
        parent[name] = node
        stack[level] = node


def get_level(row):
    match = re.search(r'navx-drawer__row--l(\d+)', row.get('class', ''))
    return int(match.group(1)) if match else None


def has_descendants(row_levels, index, level):
    for next_level in row_levels[index + 1:]:
        if not next_level:
            continue
        if next_level <= level:
            return False
        return True
    return False


def get_name(row):
    names = row.xpath(
        './/*[contains(concat(" ", normalize-space(@class), " "), " navx-drawer__label ")]/text()'
    )
    return ''.join(names).strip()


def is_collection_url(url):
    normalized_url = url.lower()
    return '/collections' in normalized_url and '/product' not in normalized_url


def run():
    url_dic = {}
    f1(url_dic)
    Tool.to_ml_json(url_dic, save_path)


if __name__ == '__main__':
    run()
