from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from lxml import etree

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser, CatCol


class SonosCatalogParser(CatalogParser):
    """Parse Sonos' server-rendered header, category footer, and category cards."""

    def matches(self, res_text):
        return 'id="center"' in res_text and 'data-testid="category-column"' in res_text

    def parse(self, res_text, collector):
        document = etree.HTML(res_text)
        if document is None:
            raise RuntimeError('Sonos homepage HTML could not be parsed')

        menu = {}
        shop_child = None
        shop_url = ''

        for anchor in document.xpath('//nav[@id="center"]//a[@href]'):
            name, raw_url = collector.tool.HTML.get_a_text_and_url(anchor)
            url = self._shop_url(raw_url, collector)
            if not url:
                continue

            child = collector.add_node(menu, name, url)
            if self._is_shop_root(url):
                shop_child = child
                shop_url = url

        if not isinstance(shop_child, dict):
            raise RuntimeError('Sonos header does not contain a usable Shop link')

        seen_shop_urls = {shop_url}
        for name, url in self._category_links(document, collector):
            if url in seen_shop_urls:
                continue

            seen_shop_urls.add(url)
            collector.add_node(shop_child, name, url)

        for title, links in self._offer_groups(document, collector).items():
            group_child = collector.add_node(menu, self._group_name(menu, title), '')
            if not isinstance(group_child, dict):
                continue

            seen_offer_urls = set()
            for name, url in links:
                if url in seen_offer_urls:
                    continue

                seen_offer_urls.add(url)
                collector.add_node(group_child, name, url)

        return menu

    def _shop_url(self, raw_url, collector):
        url = collector.normalize_url(raw_url)
        parsed = urlsplit(url)
        base_host = urlsplit(collector.base_url).netloc.lower()
        path_parts = [part for part in parsed.path.split('/') if part]

        if parsed.netloc.lower() != base_host or 'shop' not in path_parts:
            return ''

        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), '', ''))

    @staticmethod
    def _is_shop_root(url):
        return urlsplit(url).path.rstrip('/').endswith('/shop')

    def _category_links(self, document, collector):
        links = []
        category_anchors = document.xpath(
            '//*[@data-testid="category-column"]//a[@href]'
            ' | //*[@data-testid="category-link-item"]//a[@href]'
        )

        for anchor in category_anchors:
            name, raw_url = collector.tool.HTML.get_a_text_and_url(anchor)
            url = self._shop_url(raw_url, collector)
            if not name or not url:
                continue

            links.append((name, url))

        return links

    def _offer_groups(self, document, collector):
        groups = {}

        for column in document.xpath('//*[@data-testid="offers-column"]'):
            title = collector.normalize_name(column.xpath('../h4[1]//text()')) or 'Offers'
            links = groups.setdefault(title, [])

            for anchor in column.xpath('.//a[@href]'):
                name, raw_url = collector.tool.HTML.get_a_text_and_url(anchor)
                url = self._shop_url(raw_url, collector)
                if name and url:
                    links.append((name, url))

        return {title: links for title, links in groups.items() if links}

    @staticmethod
    def _group_name(menu, preferred):
        candidate = preferred
        suffix = 2
        while candidate in menu:
            candidate = f'{preferred}{suffix}'
            suffix += 1
        return candidate


snapshot_path = Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html'
catalog = CatCol(Tool, base_url, Tool.File.path_add_site('data/ml.json'), snapshot_path)
catalog.parser_types = (SonosCatalogParser,)


if __name__ == '__main__':
    catalog.run()



