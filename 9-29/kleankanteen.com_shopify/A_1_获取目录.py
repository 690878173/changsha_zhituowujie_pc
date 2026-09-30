from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol


class KleanKanteenNavigationParser(CatalogParser):
    """Parse Klean Kanteen's desktop mega menu without flattening it."""

    nav_xpath = (
        '//nav[contains(concat(" ", normalize-space(@class), " "), '
        '" header__primary-nav ")]'
    )

    def matches(self, res_text):
        return "header__primary-nav" in res_text and "header__menu-disclosure" in res_text

    @staticmethod
    def text(node):
        return " ".join(node.xpath('.//text()[not(ancestor::svg)]')).strip()

    @staticmethod
    def is_collection_url(collector, href):
        if not href:
            return False
        url = collector.normalize_url(href)
        return "/collections/" in urlsplit(url).path

    def add_collection_node(self, nodes, name, href, collector, child=None):
        if not name:
            return None
        collection_href = href if self.is_collection_url(collector, href) else ""
        if not collection_href and not child:
            return None
        return collector.add_node(nodes, name, collection_href, child)

    def navigation_urls(self, tree, collector):
        urls = set()
        navigation_nodes = tree.xpath(
            self.nav_xpath
            + ' | //header-sidebar[@id="sidebar-menu"]'
        )
        for node in navigation_nodes:
            for element in node.xpath('.//*[@href or @data-follow-link]'):
                for href in (element.get("href"), element.get("data-follow-link")):
                    if self.is_collection_url(collector, href):
                        urls.add(collector.normalize_url(href))
        return urls

    def add_other_collections(self, tree, result, collector, navigation_urls):
        other = {}
        other_urls = set()
        for link in tree.xpath("//a[@href]"):
            if link.xpath(
                'ancestor::nav[contains(concat(" ", normalize-space(@class), " "), '
                '" header__primary-nav ")] '
                '| ancestor::header-sidebar[@id="sidebar-menu"]'
            ):
                continue
            href = link.get("href") or ""
            url = collector.normalize_url(href)
            if (
                not self.is_collection_url(collector, href)
                or url in navigation_urls
                or url in other_urls
            ):
                continue
            name = self.text(link)
            if not name:
                continue
            base_name = name
            handle = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]
            number = 2
            while name in other:
                name = f"{base_name} ({handle})"
                if name not in other:
                    break
                name = f"{base_name} ({handle} {number})"
                number += 1
            if self.add_collection_node(other, name, href, collector) is not None:
                other_urls.add(url)

        if not other:
            return
        group_name = "Other"
        number = 2
        while group_name in result:
            group_name = f"Other{number}"
            number += 1
        collector.add_node(result, group_name, "", other)

    def parse(self, res_text, collector):
        tree = lxml_html.fromstring(res_text)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError("页面中未找到 Klean Kanteen 主导航")

        result = {}
        for disclosure in navs[0].xpath(
            './/details[contains(concat(" ", normalize-space(@class), " "), '
            '" header__menu-disclosure ")]'
        ):
            summaries = disclosure.xpath("./summary[1]")
            if not summaries:
                continue
            summary = summaries[0]
            top_name = summary.get("data-title") or self.text(summary)
            children = {}
            menu_items = disclosure.xpath(
                './div[contains(concat(" ", normalize-space(@class), " "), '
                '" mega-menu ")]/ul[contains(concat(" ", normalize-space(@class), " "), '
                '" mega-menu__linklist ")]/li '
                '| ./ul[contains(concat(" ", normalize-space(@class), " "), '
                '" header__dropdown-menu ")]/li'
            )
            for item in menu_items:
                headings = item.xpath("./a[@href][1]")
                if not headings:
                    continue
                heading = headings[0]
                leaves = {}
                for leaf in item.xpath("./ul/li/a[@href]"):
                    self.add_collection_node(
                        leaves,
                        self.text(leaf),
                        leaf.get("href") or "",
                        collector,
                    )
                self.add_collection_node(
                    children,
                    self.text(heading),
                    heading.get("href") or "",
                    collector,
                    leaves,
                )

            for promo in disclosure.xpath(
                './div[contains(concat(" ", normalize-space(@class), " "), '
                '" mega-menu ")]//div[contains(concat(" ", normalize-space(@class), " "), '
                '" mega-menu__promo ")]/a[@href]'
            ):
                self.add_collection_node(
                    children,
                    self.text(promo),
                    promo.get("href") or "",
                    collector,
                )

            self.add_collection_node(
                result,
                top_name,
                summary.get("data-follow-link") or "",
                collector,
                children,
            )

        if not result:
            raise RuntimeError("Klean Kanteen 主导航没有可用 collection")
        self.add_other_collections(
            tree,
            result,
            collector,
            self.navigation_urls(tree, collector),
        )
        return result


if __name__ == "__main__":
    crawler = CatCol(
        Tool,
        base_url,
        Tool.File.path_add_site("data/ml.json"),
        Path(__file__).parent / "ts" / "01-catalog" / "homepage.html",
    )
    crawler.parser_types = (KleanKanteenNavigationParser, *crawler.parser_types)
    crawler.run()
