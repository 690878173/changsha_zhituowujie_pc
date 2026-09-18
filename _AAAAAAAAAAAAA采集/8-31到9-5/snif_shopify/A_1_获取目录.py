from pathlib import Path

from lxml import etree

from config import Tool


HTML_PATH = Path(__file__).with_name('1.html')
SAVE_PATH = Tool.File.path_add_site('data/ml.json')


def text_of(node):
    """Return the menu label, preferring a card's explicit title."""
    return ' '.join((node.get('title') or ' '.join(node.xpath('.//text()'))).split())


def is_collection_url(url):
    url = url.lower()
    return '/collections' in url and '/product' not in url


def add_node(nodes, name, url, children):
    """Add a visible menu item while keeping the dictionary output schema."""
    if not name:
        return

    if name not in nodes:
        nodes[name] = {'url': url, 'child': children}


def drawer_children(drawer_id, drawers, visited):
    if drawer_id in visited:
        return {}

    drawer = drawers.get(drawer_id)
    if drawer is None:
        return {}

    visited = visited | {drawer_id}
    children = {}
    # The selected elements are returned in document order, preserving the menu order.
    entries = drawer.xpath(
        './/popup-toggle[@data-action="open"] | .//a[@href]'
    )
    for entry in entries:
        if entry.tag == 'popup-toggle':
            target = entry.get('data-target', '')
            name = text_of(entry)
            nested_children = drawer_children(target, drawers, visited)
            if nested_children:
                add_node(children, name, '', nested_children)
            continue

        url = entry.get('href', '')
        if is_collection_url(url):
            add_node(children, text_of(entry), Tool.URL.add_site(url), {})

    return children


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1():

    res = Tool.get(Tool.config.base_url)
    html = etree.HTML(res.text)
    # html = etree.HTML(HTML_PATH.read_text(encoding='utf-8'))
    drawers = {
        drawer.get('data-id'): drawer
        for drawer in html.xpath('//custom-drawer[@data-id]')
    }

    menu = {}
    for toggle in html.xpath('//div[@data-navigation]//popup-toggle[@data-action="open"]'):
        target = toggle.get('data-target', '')
        children = drawer_children(target, drawers, set())
        if children:
            add_node(menu, text_of(toggle), '', children)


    menu = menu['shop']['child']

    return menu


def run():
    menu = f1()
    Tool.to_ml_json(menu, SAVE_PATH)
    Tool.print(f'已采集 {len(menu)} 个一级目录', color='green')


if __name__ == '__main__':
    run()
