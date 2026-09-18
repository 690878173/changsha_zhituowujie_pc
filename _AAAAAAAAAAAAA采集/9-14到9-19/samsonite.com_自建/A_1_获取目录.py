from urllib.parse import urlsplit

from lxml import etree

from config import base_url, Tool

from _ljp.mb.base.get_ml import CatCol, CatalogParser

SAVE_PATH = Tool.File.path_add_site('data/ml.json')
SNAPSHOT_PATH = Tool.File.path_add_site('ts/1/homepage.html')

class BrowserCatalog(CatCol):
    """Use the rendered page when PerimeterX blocks direct HTTP requests."""

    def fetch(self):
        response = self.tool.get(self.base_url)
        if response.status_code == 200 and response.text:
            self.tool.HTML.save_raw(response.text, self.html_path)
            return response.text

        try:
            page = self.tool.browser.get_page(
                self.base_url,
                wait_for_selector='body',
            )
            html = page.content()
        except Exception as exc:
            self.tool.print(f'浏览器首页请求失败: {exc}', color='yellow')
            html = ''

        if html:
            self.tool.HTML.save_raw(html, self.html_path)
            return html

        if self.html_path.exists():
            self.tool.print('首页请求失败，使用本地 HTML', color='yellow')
            return self.html_path.read_text(encoding='utf-8')

        raise RuntimeError(
            f'首页请求失败（HTTP {response.status_code}），且浏览器未取得页面内容'
        )

class SamsoniteCatalogParser(CatalogParser):
    """Parse Samsonite's server-rendered SFCC desktop mega-menu."""

    excluded_paths = (
        '/account',
        '/cart',
        '/contact',
        '/faqs',
        '/login',
        '/privacy',
        '/returns',
        '/service',
        '/shipping',
        '/store-locator',
        '/terms',
        '/track',
        '/warranty',
        '/wishlist',
    )

    def matches(self, res_text):
        return 'id="primary-nav"' in res_text and 'menu-level-1' in res_text

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()')).split())

    def category_url(self, anchor, collector):
        href = anchor.get('href', '')
        url = collector.normalize_url(href)
        parsed = urlsplit(url)
        path = parsed.path.lower()

        if parsed.netloc != urlsplit(collector.base_url).netloc:
            return ''
        if not path or path == '/' or path.endswith('.html'):
            return ''
        if any(path.startswith(prefix) for prefix in self.excluded_paths):
            return ''
        return url

    def add_link(self, parent, anchor, collector):
        url = self.category_url(anchor, collector)
        if not url:
            return
        if any(node.get('url') == url for node in parent.values()):
            return

        name = (
            anchor.get('data-link-label')
            or self.text(anchor)
            or anchor.get('aria-label', '')
        )
        if name.lower().startswith('go to '):
            name = name[6:]
        if '. Click here to shop now' in name:
            name = name.split('. Click here to shop now', 1)[0]
        for prefix in ('Shop the new ', 'Shop our ', 'Shop out '):
            if name.lower().startswith(prefix.lower()):
                name = name[len(prefix):]
        collector.add_node(parent, name, url)

    def parse(self, res_text, collector):
        html = etree.HTML(res_text)
        menu = {}
        top_items = html.xpath(
            '//nav[@id="primary-nav"]'
            '//ul[contains(concat(" ", normalize-space(@class), " "), " menu-level-1 ")]'
            '/li[contains(concat(" ", normalize-space(@class), " "), " nav-item ")]'
        )

        for item in top_items:
            top_link = item.xpath('./a[1][@href]')
            if not top_link:
                continue

            top_link = top_link[0]
            url = self.category_url(top_link, collector)
            if not url:
                continue

            child = collector.add_node(menu, self.text(top_link), url)
            if not isinstance(child, dict):
                continue

            standard_links = item.xpath(
                './ul[contains(concat(" ", normalize-space(@class), " "), " dropdown-menu ")]'
                '//ul[contains(concat(" ", normalize-space(@class), " "), " menu-level-2 ")]'
                '/li/a[@href]'
            )
            promoted_links = item.xpath(
                './ul[contains(concat(" ", normalize-space(@class), " "), " dropdown-menu ")]'
                '//*[@data-link-type="category"][@href]'
            )
            for link in [*standard_links, *promoted_links]:
                self.add_link(child, link, collector)

        other = {}
        other_links = html.xpath(
            '//a[@href and not(ancestor::nav[@id="primary-nav"])]'
            '[@data-link-type="category"'
            ' or contains(concat(" ", normalize-space(@class), " "), " stretched-link ")'
            ' or contains(concat(" ", normalize-space(@class), " "), " hero-background-link ")]'
        )
        for link in other_links:
            self.add_link(other, link, collector)

        if other:
            other_name = 'Other' if 'Other' not in menu else 'Other2'
            menu[other_name] = {'url': '', 'child': other}

        return menu

collector = BrowserCatalog(Tool, base_url, SAVE_PATH, SNAPSHOT_PATH)
collector.parser_types = (SamsoniteCatalogParser,)

if __name__ == '__main__':
    collector.run()
