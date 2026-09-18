from pathlib import Path

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.shopify import CatalogCollector


HTML_PATH = Path(__file__).with_name('1.html')
SAVE_PATH = Tool.File.path_add_site('data/ml.json')


class WarmiesCatalogCollector(CatalogCollector):
    """解析 Warmies 主题的 ``mega-menu`` 多级导航。"""

    primary_nav_xpath = '//nav[@aria-label="Primary navigation"]'

    @staticmethod
    def link_text(link):
        return ' '.join(link.xpath('.//text()[not(ancestor::svg)]')).strip()

    def add_link(self, nodes, link, *, child=None, depth=0):
        self.put_node(
            nodes,
            self.link_text(link),
            link.get('href') or link.get('data-follow-link') or '',
            child=child,
            depth=depth,
        )

    def parse_mega_menu(self, mega_menu):
        result = {}
        groups = mega_menu.xpath(
            './ul[contains(concat(" ", normalize-space(@class), " "), " mega-menu__linklist ")]/li'
        )
        for group in groups:
            heading = group.xpath('./a[@href][1]')
            if not heading:
                continue
            child = {}
            for link in group.xpath('./ul/li/a[@href]'):
                self.add_link(child, link, depth=2)
            self.add_link(result, heading[0], child=child, depth=1)

        # 无文字分组的卡片目录也属于当前一级菜单。
        promo_links = mega_menu.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), " mega-menu__promo ")]//a[@href]'
        )
        for link in promo_links:
            self.add_link(result, link, depth=1)
        return result

    def parse_html(self, html):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.primary_nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 Primary navigation 菜单')

        result = {}
        for item in navs[0].xpath('./ul/li[contains(@class, "header__primary-nav-item")]'):
            links = item.xpath('./a[@href][1] | ./mega-menu-disclosure/details/summary[1]')
            if not links:
                continue
            child = {}
            mega_menus = item.xpath('.//div[contains(concat(" ", normalize-space(@class), " "), " mega-menu ")]')
            if mega_menus:
                child = self.parse_mega_menu(mega_menus[0])
            self.add_link(result, links[0], child=child)
        if not result:
            raise RuntimeError('Primary navigation 中没有可用目录')
        return result

    def export_catalog(self, menu):
        """导出清晰的一级、二级、三级路径，供 Step2 直接读取。"""
        flat_menu = {}

        def walk(path, node):
            if node.get('url'):
                flat_menu[','.join(path)] = node['url']
            for name, child in (node.get('child') or {}).items():
                walk([*path, name], child)

        for name, node in menu.items():
            walk([name], node)
        return self.tool.File.save_json(flat_menu, self.save_path)


@Tool.zs('数据结构:{一级目录:{url:xxx,child:{二级目录:{url:xxx,child:{三级目录: url}}}}}')
def run():
    return WarmiesCatalogCollector(Tool, base_url, HTML_PATH, SAVE_PATH).run()


if __name__ == '__main__':
    try:
        menu = run()
        Tool.print(f'已采集 {len(menu)} 个一级目录', color='green')
    finally:
        Tool.close()
