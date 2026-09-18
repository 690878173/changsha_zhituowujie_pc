from pathlib import Path

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.mg_shopify import CatalogCollector


HTML_PATH = Path(__file__).with_name('1.html')
SAVE_PATH = Tool.File.path_add_site('data/ml.json')


class SiteCatalogCollector(CatalogCollector):
    """解析该站点由 Next.js 客户端渲染的导航菜单。"""

    top_menu_names = ('Women', 'Men', 'Categories', 'Conditions')

    def parse_menu_panel(self, panel, menu):
        grids = panel.xpath('.//div[contains(@class, "grid") and contains(@class, "text-black")]')
        if not grids:
            return
        for column in grids[0].xpath('./div'):
            headings = column.xpath(
                './/div[contains(@class, "font-semibold") and contains(@class, "border-b")]'
                ' | .//h3[contains(@class, "font-semibold") and contains(@class, "border-b")]'
            )
            if not headings:
                continue
            group_name = self.normalize_name(' '.join(headings[0].xpath('.//text()')))
            group = {}
            for link in column.xpath('.//a[contains(@href, "/collections/")]'):
                name = self.normalize_name(' '.join(link.xpath('.//p[1]//text()')))
                if not name:
                    name = self.normalize_name(' '.join(link.xpath('.//text()[not(ancestor::svg)]')))
                if name:
                    self.put_node(group, name, link.get('href') or '', depth=2)
            if group_name and group:
                self.put_node(menu, group_name, child=group, depth=1)

    def parse_browser_menu(self):
        # 此站点的下拉菜单由客户端生成，普通 HTTP 首页响应不包含完整目录。
        self.tool.browser.config.enabled = True
        self.tool.browser.config.backend = 'playwright'
        self.tool.browser.config.headless = True
        self.tool.browser.config.fingerprint_enabled = False
        self.tool.browser.config.block_images = True

        page = self.tool.browser.get_page(self.base_url)
        page.wait_for_timeout(1000)
        tree = lxml_html.fromstring(page.content())
        panels = tree.xpath(
            '//div[contains(@class, "absolute") and contains(@class, "top-full")'
            ' and contains(@class, "left-0") and contains(@class, "right-0")'
            ' and contains(@class, "bg-white") and contains(@class, "z-50")]'
        )
        if len(panels) < len(self.top_menu_names):
            raise RuntimeError(f'未找到完整导航菜单，仅识别到 {len(panels)} 个下拉面板')

        result = {}
        for name, panel in zip(self.top_menu_names, panels):
            child = {}
            self.parse_menu_panel(panel, child)
            if child:
                self.put_node(result, name, child=child)
        if len(result) != len(self.top_menu_names):
            raise RuntimeError(f'导航目录不完整，仅采集到：{", ".join(result)}')
        return result

    def run(self):
        menu = self.parse_browser_menu()
        self.export_catalog(menu)
        return menu

    def export_catalog(self, menu):
        """按真实层级导出，供后续 Step2 直接读取。"""
        flat_menu = {}

        def walk(path, node):
            url = node.get('url') or ''
            if url:
                flat_menu[','.join(path)] = url
            for name, child in (node.get('child') or {}).items():
                walk([*path, name], child)

        for name, node in menu.items():
            walk([name], node)
        return self.tool.File.save_json(flat_menu, self.save_path)

    def fetch_html(self):
        return super().fetch_html()

    def create_parsers(self):
        return super().create_parsers()

    def select_parser(self, html):
        return super().select_parser(html)

    def parse_html(self, html):
        return super().parse_html(html)

    def normalize_name(self, value):
        return super().normalize_name(value)

    def normalize_url(self, url):
        return super().normalize_url(url)

    def should_keep_url(self, url):
        return super().should_keep_url(url)

    def should_keep_node(self, name, url, child, depth):
        return super().should_keep_node(name, url, child, depth)

    def put_node(self, nodes, name, url='', child=None, depth=0):
        return super().put_node(nodes, name, url, child, depth)

    def after_parse(self, menu):
        return super().after_parse(menu)


@Tool.zs('数据结构:{title:{url:xxx,child:{title:{url:xxx,child:{...}}}}}')
def f1():
    return SiteCatalogCollector(Tool, base_url, HTML_PATH, SAVE_PATH).run()


def run():
    menu = f1()
    Tool.print(f'已采集 {len(menu)} 个一级目录', color='green')


if __name__ == '__main__':
    try:
        run()
    finally:
        Tool.close()
