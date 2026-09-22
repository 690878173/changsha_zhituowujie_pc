from pathlib import Path

from config import Tool, base_url
from lxml import etree
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol


class FluxCatalogParser(CatalogParser):
    def matches(self, html):
        return 'id=\'SiteHeader\'' in html or 'id="SiteHeader"' in html

    def parse(self, html, collector):
        tree = etree.HTML(html)
        menu = {}
        nav_items = tree.xpath(
            '//*[@id="SiteHeader"]//ul['
            'contains(concat(" ", normalize-space(@class), " "), " site-navigation ")'
            ']/li'
        )

        for item in nav_items:
            links = item.xpath('./a[contains(@href, "/collections/")]')
            if not links:
                continue

            name, url = collector.tool.HTML.get_a_text_and_url(links[0])
            children = collector.add_node(menu, name, url)
            if children is None:
                continue

            for child_link in item.xpath(
                './/div[contains(@class, "site-nav__dropdown")]'
                '//a[contains(@href, "/collections/")]'
            ):
                child_name, child_url = collector.tool.HTML.get_a_text_and_url(child_link)
                collector.add_node(children, child_name, child_url)

        activity_cards = tree.xpath(
            '//div[contains(concat(" ", normalize-space(@class), " "), " pcard ") '
            'and not(ancestor::*[@id="SiteHeader"])]'
        )
        if activity_cards:
            other_name = 'Other' if 'Other' not in menu else 'Other2'
            other = collector.add_node(menu, other_name)
            seen_urls = set()
            for card in activity_cards:
                links = card.xpath('.//a[contains(@href, "/collections/")]')
                name = collector.normalize_name(card.xpath('./p[contains(@class, "nm")]/text()'))
                if not links or not name:
                    continue
                url = links[0].get('href', '')
                normalized_url = collector.normalize_url(url)
                if not name or normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url)
                collector.add_node(other, name, url)

        return menu


M = CatCol(
    Tool,
    base_url,
    Tool.File.path_add_site('data/ml.json'),
    Path(__file__).with_name('ts') / '1_catalog' / 'fluxfootwear_homepage.html',
)
M.parser_types = (*M.parser_types, FluxCatalogParser)


if __name__ == '__main__':
    M.run()
