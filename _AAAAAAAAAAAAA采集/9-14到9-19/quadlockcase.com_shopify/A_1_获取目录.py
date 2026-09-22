"""阶段 1：抓取 Quad Lock 的公开 Shopify 商品目录。"""

from pathlib import Path
import sys
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


class QuadLockMobileMenuParser(CatalogParser):
    """解析 Quad Lock 服务端输出的三级移动商品菜单和首页 collection 卡片。"""

    nav_xpath = '//nav[@aria-label="Main Navigation - Mobile"]'

    def matches(self, page_html):
        return (
            'Main Navigation - Mobile' in page_html
            and 'nav__mobile--l2-sub' in page_html
            and 'nav__mobile--l3-sub' in page_html
        )

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.rstrip('/').lower()
        return (
            path.startswith('/collections/')
            and path != '/collections'
            and '/products/' not in path
        )

    @staticmethod
    def handle_name(url):
        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
        return handle.replace('-', ' ').title()

    def collection_url(self, href, collector):
        url = collector.normalize_url(href)
        if not self.is_collection(url):
            return ''
        return collector.tool.URL.del_par(url)

    def unique_name(self, nodes, name, url):
        if name not in nodes:
            return name
        if nodes[name].get('url') == url:
            return ''
        handle = self.handle_name(url) or 'collection'
        candidate = f'{name} ({handle})'
        suffix = 2
        while candidate in nodes:
            candidate = f'{name} ({handle} {suffix})'
            suffix += 1
        return candidate

    def add_node(self, nodes, name, url, child, collector):
        name = ' '.join((name or '').split())
        if not name or not (url or child):
            return False
        name = self.unique_name(nodes, name, url)
        if not name:
            return False
        return collector.add_node(nodes, name, url, child) is not None

    def parse_items(self, items, collector):
        result = {}
        for item in items:
            child = self.parse_items(item.xpath('./ul[1]/li'), collector)
            buttons = item.xpath('./button[1]')
            links = item.xpath('./a[@href][1]')
            label_node = buttons[0] if buttons else (links[0] if links else None)
            name = self.text(label_node) if label_node is not None else ''
            url = self.collection_url(links[0].get('href') or '', collector) if links else ''

            if name:
                self.add_node(result, name, url, child, collector)
            else:
                for child_name, child_node in child.items():
                    self.add_node(
                        result,
                        child_name,
                        child_node.get('url') or '',
                        child_node.get('child') or {},
                        collector,
                    )
        return result

    def page_link_name(self, link, url):
        headings = link.xpath('.//*[self::h1 or self::h2 or self::h3][1]')
        name = self.text(headings[0]) if headings else self.text(link)
        if name.lower().endswith(' explore'):
            name = name[:-8].strip()
        if not name or name.lower() in {'explore', 'shop now', 'learn more'}:
            name = (link.get('aria-label') or link.get('title') or '').strip()
        if not name:
            images = link.xpath('.//img[@alt][1]')
            name = (images[0].get('alt') or '').strip() if images else ''
        return name or self.handle_name(url)

    def parse_page_links(self, tree, collector):
        result = {}
        seen = set()
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::nav'):
                continue
            url = self.collection_url(link.get('href') or '', collector)
            if not url:
                continue
            name = self.page_link_name(link, url)
            identity = (name, url)
            if identity in seen:
                continue
            if self.add_node(result, name, url, {}, collector):
                seen.add(identity)
        return result

    def parse(self, page_html, collector):
        tree = lxml_html.fromstring(page_html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('Quad Lock 首页中未找到移动商品导航')
        menu_lists = navs[0].xpath('.//ul[@role="menubar"][1]')
        if not menu_lists:
            raise RuntimeError('Quad Lock 首页中未找到移动导航菜单项')

        result = self.parse_items(menu_lists[0].xpath('./li'), collector)
        if not result:
            raise RuntimeError('Quad Lock 商品导航中没有 collection 链接')

        other = self.parse_page_links(tree, collector)
        if other:
            other_name = 'Other' if 'Other' not in result else 'Other2'
            self.add_node(result, other_name, '', other, collector)
        return result


class QuadLockCatCol(ShopifyCatCol):
    parser_types = (QuadLockMobileMenuParser,)


if __name__ == '__main__':
    try:
        QuadLockCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).parent / 'ts' / '1' / 'homepage.html',
        ).run()
    finally:
        Tool.close()
