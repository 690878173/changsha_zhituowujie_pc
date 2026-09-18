from pathlib import Path
from urllib.parse import urlsplit

from lxml import etree

from config import Tool, base_url
from request_credentials import cookies, headers
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol


class CredentialCatalog(CatCol):
    """Fetch Carve Designs with the supplied anti-bot session."""

    def fetch(self):
        response = None
        for _ in range(3):
            response = self.tool.get(self.base_url, headers=headers, cookies=cookies)
            if response.status_code == 200 and response.text:
                self.tool.HTML.save_raw(response.text, self.html_path)
                return response.text
        if self.html_path.exists():
            self.tool.print(
                f'首页请求失败（{response.status_code}），使用本地 HTML',
                color='yellow',
            )
            return self.html_path.read_text(encoding='utf-8')
        raise RuntimeError(f'首页请求失败（{response.status_code}），且本地 HTML 不存在')


class CarveDesignsMenuParser(CatalogParser):
    """Parse the site's three-level mobile menu without flattening it."""

    def matches(self, res_text):
        return 'hamburger-menu' in res_text and 'main-hamburger-link' in res_text

    @staticmethod
    def text(node):
        return ' '.join(Tool.HTML.get_text(node).split())

    @staticmethod
    def is_menu_item(node):
        return 'main-hamburger-link' in (node.get('class') or '')

    def collection_url(self, collector, href):
        if not href:
            return None
        url = collector.normalize_url(href)
        path = urlsplit(url).path.rstrip('/')
        return url if path.startswith('/collections/') else None

    def add_leaf(self, collector, target, link):
        name = self.text(link)
        href = link.get('href') or ''
        if name and self.collection_url(collector, href):
            collector.add_node(target, name, href)

    def parse(self, res_text, collector):
        tree = etree.HTML(res_text)
        menus = tree.xpath('//div[contains(@class, "hamburger-menu")]/ul[1]')
        if not menus:
            raise RuntimeError('页面中未找到 hamburger-menu 分类导航')

        result = {}
        menu = menus[0]
        children = list(menu)
        for index, item in enumerate(children):
            if item.tag != 'li' or not self.is_menu_item(item):
                continue
            links = item.xpath('./a[1]')
            if not links:
                continue
            link = links[0]
            name = self.text(link)
            href = link.get('href') or ''
            if self.collection_url(collector, href):
                collector.add_node(result, name, href)
                continue

            submenu = children[index + 1] if index + 1 < len(children) else None
            if submenu is None or submenu.tag != 'ul' or 'child' not in (submenu.get('class') or ''):
                continue
            groups = collector.add_node(result, name, '')
            if not isinstance(groups, dict):
                continue
            for group in submenu.xpath('./li'):
                group_links = group.xpath('./a[1]')
                if not group_links:
                    continue
                group_link = group_links[0]
                group_name = self.text(group_link)
                group_href = group_link.get('href') or ''
                leaves = group.xpath('./ul[contains(@class, "grandchild")]/li/a[@href]')
                if self.collection_url(collector, group_href):
                    group_target = collector.add_node(groups, group_name, group_href)
                elif leaves:
                    group_target = collector.add_node(groups, group_name, '')
                else:
                    group_target = None
                if not isinstance(group_target, dict):
                    continue
                for leaf in leaves:
                    self.add_leaf(collector, group_target, leaf)

        known_urls = {
            url
            for group in result.values()
            for url in self.collect_urls(group)
        }
        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::div[contains(@class, "hamburger-menu")]'):
                continue
            href = link.get('href') or ''
            url = self.collection_url(collector, href)
            name = self.text(link)
            if not url or url in known_urls or not name:
                continue
            if collector.add_node(extra, name, href) is not None:
                known_urls.add(url)
        if extra:
            other_name = 'Other'
            suffix = 2
            while other_name in result:
                other_name = f'Other{suffix}'
                suffix += 1
            collector.add_node(result, other_name, '', extra)
        if not result:
            raise RuntimeError('分类导航中未找到 collection 链接')
        return result

    @staticmethod
    def collect_urls(node):
        url = node.get('url')
        if url:
            yield url
        for child in node.get('child', {}).values():
            yield from CarveDesignsMenuParser.collect_urls(child)


if __name__ == '__main__':
    try:
        catalog = CredentialCatalog(
            Tool,
            base_url,
            Tool.File.path_add_site('data/ml.json'),
            Path(__file__).with_name('1.html'),
        )
        catalog.parser_types = (CarveDesignsMenuParser,)
        catalog.run()
    finally:
        Tool.close()
