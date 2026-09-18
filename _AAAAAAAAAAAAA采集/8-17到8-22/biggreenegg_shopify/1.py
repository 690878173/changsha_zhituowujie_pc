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
        '//nav[contains(concat(" ", normalize-space(@class), " "), " header__menu ")]'
        '[not(contains(concat(" ", normalize-space(@class), " "), " secondary-header "))]'
    )
    if not menus:
        return url_dic

    for item in menus[0].xpath('./li'):
        top_link = item.xpath('./a[@data-top-link][1]')
        if not top_link:
            continue

        name = get_name(top_link[0])
        if not name:
            continue

        url = top_link[0].get('href', '').strip()
        node = {
            'url': Tool.URL.add_site(url) if is_collection_url(url) else '',
            'child': {},
        }
        add_top_children(item, node['child'])

        if node['url'] or node['child']:
            url_dic[name] = node

    return url_dic


def add_top_children(item, dic):
    dropdown = item.xpath(
        './div[contains(concat(" ", normalize-space(@class), " "), " header__dropdown ")]'
    )
    if not dropdown:
        return

    children = dropdown[0].xpath(
        './/a[@data-stagger-first or @data-stagger]'
    )
    grandchildren = {
        div.get('data-id'): div
        for div in dropdown[0].xpath(
            './/div[contains(concat(" ", normalize-space(@class), " "), " grandchildren-nav ")]'
        )
        if div.get('data-id')
    }

    for child in children:
        name = get_name(child)
        if not name:
            continue

        url = child.get('href', '').strip()
        if is_collection_url(url):
            node = {'url': Tool.URL.add_site(url), 'child': {}}
        elif url == '#':
            node = {'url': '', 'child': {}}
            add_grandchildren(grandchildren.get(name), node['child'])
        else:
            continue

        dic[name] = node


def add_grandchildren(container, dic):
    if container is None:
        return

    for link in container.xpath('./a[@href]'):
        url = link.get('href', '').strip()
        if not is_collection_url(url):
            continue
        name = get_name(link)
        if name:
            dic[name] = {
                'url': Tool.URL.add_site(url),
                'child': {},
            }


def get_name(node):
    label = node.get('aria-label')
    if label:
        return ' '.join(label.split())

    texts = node.xpath(
        './/*[contains(concat(" ", normalize-space(@class), " "), " navtext ")]/text()'
    )
    return ' '.join(' '.join(texts).split())


def is_collection_url(url):
    normalized_url = url.lower()
    return '/collections' in normalized_url and '/product' not in normalized_url


def run():
    url_dic = {}
    f1(url_dic)
    Tool.to_ml_json(url_dic, save_path)


if __name__ == '__main__':
    run()
