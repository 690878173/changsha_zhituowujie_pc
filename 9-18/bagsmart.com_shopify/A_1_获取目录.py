"""阶段 1：抓取 Bagsmart 的公开 Shopify 商品目录。"""

from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class BagsmartV3MenuParser(CatalogParser):
    """解析 Bagsmart ``header-v3`` 的桌面商品导航与首页 collection 卡片。"""

    def matches(self, page_html):
        return 'header-v3-nav' in page_html and 'data-top-link' in page_html

    @staticmethod
    def text(node):
        return ' '.join(
            ' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split()
        )

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.rstrip('/').lower()
        return path.startswith('/collections/') and path != '/collections'

    @staticmethod
    def handle_name(url):
        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
        return handle.replace('-', ' ').title()

    def collection_url(self, href, collector):
        url = collector.normalize_url(href)
        if not self.is_collection(url):
            return ''
        return collector.tool.URL.del_par(url)

    def add_node(self, nodes, name, url, child, collector):
        name = self.text(name) if not isinstance(name, str) else ' '.join(name.split())
        if not name or not (url or child):
            return False
        if name in nodes:
            if nodes[name].get('url') == url:
                return False
            base_name = name
            name = f'{base_name} ({self.handle_name(url)})' if url else base_name
            suffix = 2
            while name in nodes:
                name = f'{base_name} ({self.handle_name(url)} {suffix})'
                suffix += 1
        return collector.add_node(nodes, name, url, child) is not None

    def parse_group(self, group, collector):
        child = {}
        for link in group.xpath('.//a[@href]'):
            url = self.collection_url(link.get('href') or '', collector)
            if url:
                self.add_node(child, self.text(link), url, {}, collector)
        return child

    def parse_dropdown(self, dropdown, collector):
        child = {}
        for group in dropdown.xpath(
            './/div[contains(concat(" ", normalize-space(@class), " "), " dropdown__family ")]'
        ):
            headings = group.xpath(
                './div[contains(concat(" ", normalize-space(@class), " "), " navlink--child ")][1]'
            )
            group_child = self.parse_group(group, collector)
            if headings and group_child:
                self.add_node(child, self.text(headings[0]), '', group_child, collector)

        for link in dropdown.xpath(
            './/a[contains(concat(" ", normalize-space(@class), " "), " header-v3-nav__visual-card ")][@href]'
        ):
            url = self.collection_url(link.get('href') or '', collector)
            if url:
                self.add_node(child, self.text(link), url, {}, collector)
        return child

    def page_link_name(self, link, url):
        name = self.text(link)
        if not name:
            name = (link.get('aria-label') or link.get('title') or '').strip()
        if not name:
            images = link.xpath('.//img[@alt][1]')
            name = (images[0].get('alt') or '').strip() if images else ''
        return name or self.handle_name(url)

    def parse_other(self, tree, collector):
        other = {}
        seen = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav or ancestor::header-drawer'):
                continue
            url = self.collection_url(link.get('href') or '', collector)
            name = self.page_link_name(link, url)
            if not url or (name, url) in seen:
                continue
            if self.add_node(other, name, url, {}, collector):
                seen.add((name, url))
        return other

    def parse(self, page_html, collector):
        tree = lxml_html.fromstring(page_html)
        menus = tree.xpath(
            '//nav[contains(concat(" ", normalize-space(@class), " "), " header__menu ")]'
        )
        if not menus:
            raise RuntimeError('Bagsmart 首页中未找到 header-v3 商品导航')

        result = {}
        for item in menus[0].xpath(
            './/*[contains(concat(" ", normalize-space(@class), " "), " menu__item ") '
            'and contains(concat(" ", normalize-space(@class), " "), " grandparent ")]'
        ):
            top_links = item.xpath('./a[@data-top-link][1]')
            if not top_links:
                continue
            top_link = top_links[0]
            dropdowns = item.xpath('./div[@data-hover-disclosure][1]')
            child = self.parse_dropdown(dropdowns[0], collector) if dropdowns else {}
            url = self.collection_url(top_link.get('href') or '', collector)
            self.add_node(result, self.text(top_link), url, child, collector)

        if not result:
            raise RuntimeError('Bagsmart 商品导航中没有 collection 链接')
        other = self.parse_other(tree, collector)
        if other:
            other_name = 'Other' if 'Other' not in result else 'Other2'
            self.add_node(result, other_name, '', other, collector)
        return result


class BagsmartCatCol(ShopifyCatCol):
    """通过浏览器取得受 Cloudflare 保护的首页，再复用 Shopify 目录解析器。"""

    parser_types = (BagsmartV3MenuParser,)

    def fetch(self):
        for attempt in range(2):
            page = self.tool.browser.get_page(self.base_url, wait_for_selector='body')
            page.wait_for_timeout(7000)
            page_html = page.content()
            if 'Verifying your connection' not in page_html:
                self.tool.HTML.save_raw(page_html, self.html_path)
                return page_html
            if attempt == 0:
                self.tool.browser.restart_context(relaunch_browser=True)

        if self.html_path.exists():
            self.tool.print('首页仍在验证，使用本地 HTML 快照', color='yellow')
            return self.html_path.read_text(encoding='utf-8')
        raise RuntimeError('Cloudflare 验证未通过，未获得可解析的 Bagsmart 首页')


if __name__ == '__main__':
    try:
        BagsmartCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '1' / 'homepage.html',
        ).run()
    finally:
        Tool.close()

