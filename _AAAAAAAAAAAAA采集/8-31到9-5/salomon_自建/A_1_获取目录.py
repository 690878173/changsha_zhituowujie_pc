from pathlib import Path
from urllib.parse import urlsplit

from lxml import etree

from config import base_url, Tool


HTML_PATH = Path(__file__).with_name('1.html')
SAVE_PATH = Tool.File.path_add_site('data/ml.json')


def clean_text(values):
    return ' '.join(' '.join(values).split())


def load_html():
    response = Tool.get(base_url)
    if response.status_code == 200 and response.text:
        Tool.HTML.save(response.text, HTML_PATH)
        return response.text

    if HTML_PATH.exists():
        Tool.print(f'首页请求失败（{response.status_code}），使用本地 HTML', color='yellow')
        return HTML_PATH.read_text(encoding='utf-8')

    raise RuntimeError(f'首页请求失败（{response.status_code}），且本地 HTML 不存在')


def category_parts(url):
    parts = [part for part in urlsplit(url).path.strip('/').split('/') if part]
    if parts and parts[0].lower() == 'en-us':
        parts = parts[1:]
    if parts and parts[0].lower() == 'c':
        parts = parts[1:]
    return tuple(parts)


def is_category_url(url):
    normalized = (url or '').lower()
    return (
        '/en-us/' in normalized
        and '/products/' not in normalized
        and '/sg' not in normalized
        and category_parts(url)
    )


def put_node(nodes, name, url=''):
    if name not in nodes:
        nodes[name] = {'url': url, 'child': {}}
    elif url and not nodes[name]['url']:
        nodes[name]['url'] = url
    return nodes[name]


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1():
    html = etree.HTML(load_html())
    links = []

    # The accessible menu is flat, so collect labels first and rebuild its URL hierarchy.
    for anchor in html.xpath('//nav[@aria-label="Main menu"]//a[@href]'):
        name, url = Tool.HTML.get_a_text_and_url(anchor)
        name = clean_text([name])
        url = Tool.URL.add_site(url)
        parts = category_parts(url)
        if not name or not is_category_url(url):
            continue
        links.append((name, url, parts))

    menu = {}
    nodes_by_path = {}
    # Build parents before children, while retaining the source order within each level.
    for _, (name, url, parts) in sorted(
        enumerate(links), key=lambda item: (len(item[1][2]), item[0])
    ):
        if parts in nodes_by_path:
            continue

        parent = menu
        for index in range(len(parts) - 1, 0, -1):
            ancestor = nodes_by_path.get(parts[:index])
            if ancestor is not None:
                parent = ancestor['child']
                break

        node = put_node(parent, name, url)
        nodes_by_path[parts] = node

    return menu


def run():
    menu = f1()
    Tool.to_ml_json(menu, SAVE_PATH)
    Tool.print(f'已采集 {len(menu)} 个一级目录', color='green')


if __name__ == '__main__':
    run()
