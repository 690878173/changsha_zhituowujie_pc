from urllib.parse import urlsplit

from config import Tool, base_url
from _ljp.mb.base.get_ml import BaseCatalogParser, CatCol


save_path = Tool.File.path_add_site('data/ml.json')


class Parser(BaseCatalogParser):
    """Preserve Conair's two-level desktop product menu."""

    EXCLUDED_PATHS = {'', '/', '/home', '/cart', '/login', '/wishlist'}

    @classmethod
    def product_url(cls, href):
        url = Tool.URL.add_site(href)
        parts = urlsplit(url)
        if parts.netloc != 'www.conair.com':
            return None
        if parts.path in cls.EXCLUDED_PATHS or parts.path.endswith('.html'):
            return None
        return url

    def f1(self, html, data):
        items = html.xpath(
            '//nav[contains(@class, "navbar")]/div/ul/'
            'li[not(contains(@class, "d-none"))]'
        )
        for item in items:
            top_links = item.xpath('./a[@href]')
            if not top_links:
                continue
            name, href = Tool.HTML.get_a_text_and_url(top_links[0])
            name = ' '.join(name.split())
            url = self.product_url(href)
            if not name or not url:
                continue

            children = self.collector.add_node(data, name, url)
            if not isinstance(children, dict):
                continue
            for child_link in item.xpath('./div//a[@href]'):
                child_name, child_href = Tool.HTML.get_a_text_and_url(child_link)
                child_name = ' '.join(child_name.split())
                child_url = self.product_url(child_href)
                # "Shop All" is the same category as its parent.
                if not child_name or not child_url or child_url == url:
                    continue
                self.collector.add_node(children, child_name, child_url)


collector = CatCol(Tool, base_url, save_path)
collector.parser_types = (Parser,)


if __name__ == '__main__':
    collector.run()



