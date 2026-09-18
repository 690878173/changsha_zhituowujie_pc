from pathlib import Path

from lxml import etree

from config import base_url, Tool


HTML_PATH = Path(__file__).with_name('1.html')
SAVE_PATH = Tool.File.path_add_site('data/ml.json')


def clean_text(values):
    return ' '.join(' '.join(values).split())


def link_name(link):
    card_name = clean_text(link.xpath('.//span[contains(@class, "pd-nav__card-label")]//text()'))
    return card_name or clean_text(link.xpath('./text()[normalize-space()]'))


def is_category_url(url):
    url = (url or '').lower()
    return (
        '/en-us/' in url
        and '/products/' not in url
        and '/blogs/' not in url
        and '/search' not in url
        and '/account' not in url
        and '/cart' not in url
    )


def add_node(nodes, name, url='', children=None):
    name = clean_text([name])
    if not name or name in nodes:
        return

    children = children or {}
    url = Tool.URL.add_site(url) if is_category_url(url) else ''
    if url or children:
        nodes[name] = {'url': url, 'child': children}


def add_links(nodes, container):
    for link in container.xpath('.//a[contains(@class, "pd-nav__l1-link") or contains(@class, "pd-nav__l3-link") or contains(@class, "pd-nav__card")]'):
        add_node(nodes, link_name(link), link.get('href', ''))


def group_children(container):
    children = {}
    for group in container.xpath('./div[contains(@class, "pd-nav__group")]'):
        heading = clean_text(group.xpath('./h3[contains(@class, "pd-nav__group-heading")]//text()'))
        links = {}
        add_links(links, group)
        if heading:
            add_node(children, heading, '', links)
        else:
            for name, node in links.items():
                add_node(children, name, node['url'], node['child'])
    return children


def bundle_children(bundle):
    detail = bundle.xpath('./div[contains(@class, "pd-nav__l2-detail")]')
    if not detail:
        return {}

    detail = detail[0]
    children = {}

    # Card slots represent a third-level category and its product-category cards.
    for slot in detail.xpath('.//div[contains(@class, "pd-nav__l3CardSlot")]'):
        heading = slot.xpath('./div[contains(@class, "pd-nav__l3-content-heading")]//a[@href]')
        slot_children = {}
        add_links(slot_children, slot)
        if heading:
            heading = heading[0]
            add_node(children, link_name(heading), heading.get('href', ''), slot_children)
        else:
            for name, node in slot_children.items():
                add_node(children, name, node['url'], node['child'])

    groups = detail.xpath('.//div[contains(@class, "pd-nav__groups")]')
    for group_container in groups:
        for name, node in group_children(group_container).items():
            add_node(children, name, node['url'], node['child'])

    # Some bundles expose cards directly rather than in a third-level card slot.
    direct_links = {}
    add_links(direct_links, detail)
    for name, node in direct_links.items():
        add_node(children, name, node['url'], node['child'])

    return children


def panel_children(panel):
    children = {}
    bundles = panel.xpath('.//div[contains(@class, "pd-nav__l2-bundle")]')
    for bundle in bundles:
        link = bundle.xpath('./div[contains(@class, "pd-nav__l2-item")]//a[@href]')
        name = clean_text(bundle.xpath('./div[contains(@class, "pd-nav__l2-item")]//text()'))
        url = link[0].get('href', '') if link else ''
        if not url:
            heading = bundle.xpath('./div[contains(@class, "pd-nav__l2-detail")]//p[contains(@class, "pd-nav__l3-content-heading")]/a[@href]')
            url = heading[0].get('href', '') if heading else ''
        add_node(children, name, url, bundle_children(bundle))

    if bundles:
        return children

    for group_container in panel.xpath('.//div[contains(@class, "pd-nav__groups")]'):
        for name, node in group_children(group_container).items():
            add_node(children, name, node['url'], node['child'])

    direct_links = {}
    add_links(direct_links, panel)
    for name, node in direct_links.items():
        add_node(children, name, node['url'], node['child'])
    return children


def load_html():
    response = Tool.get(base_url)
    if response.status_code == 200 and response.text:
        Tool.HTML.save(response.text, HTML_PATH)
        return response.text

    if HTML_PATH.exists():
        Tool.print(f'首页请求失败（{response.status_code}），使用本地 HTML', color='yellow')
        return HTML_PATH.read_text(encoding='utf-8')

    raise RuntimeError(f'首页请求失败（{response.status_code}），且本地 HTML 不存在')


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1():
    html = etree.HTML(load_html())
    menu = {}
    top_items = html.xpath(
        '//nav[contains(@class, "nav-main__menu-group")]'
        '//div[contains(@class, "experience-primaryMenu")]/div[contains(@class, "experience-component")]'
        '/*[contains(@class, "pd-nav__item")]'
    )
    for item in top_items:
        link = item.xpath('./a[contains(@class, "pd-nav__l1-link")][@href]')
        name = clean_text(
            item.xpath('./a[contains(@class, "pd-nav__l1-link")]/text()')
            or item.xpath('./button[contains(@class, "pd-nav__l1-link")]//text()')
        )
        if name not in {'Shop', 'Sale'}:
            continue
        panel = item.xpath('./div[contains(@class, "pd-nav__panel")]')
        children = panel_children(panel[0]) if panel else {}
        url = link[0].get('href', '') if link else ''
        add_node(menu, name, url, children)
    return menu


def run():
    menu = f1()
    Tool.to_ml_json(menu, SAVE_PATH)
    Tool.print(f'已采集 {len(menu)} 个一级目录', color='green')


if __name__ == '__main__':
    run()
