"""Collect Huda Beauty's public Shopify collection navigation."""

import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class HudaBeautyNavigationParser(CatalogParser):
    """Parse Huda Beauty's server-rendered desktop and mobile category menu."""

    generic_link_labels = {"SHOP", "SHOP NOW", "VIEW ALL"}

    def matches(self, html):
        return (
            "header-navigation__primary-nav" in html
            and "header-navigation__desktop-subnav" in html
        )

    @staticmethod
    def text(node):
        values = node.xpath(
            ".//text()[not(ancestor::svg)][not(ancestor::script)]"
            "[not(ancestor::style)]"
        )
        return " ".join(" ".join(values).split())

    @staticmethod
    def comparable_name(name):
        return "".join(character for character in (name or "").lower() if character.isalnum())

    @staticmethod
    def fallback_name(url):
        handle = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]
        return handle.replace("-", " ").title()

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or "").path.rstrip("/")
        return bool(
            path.lower().startswith("/collections/")
            or re.match(r"^/[a-z]{2}(?:-[a-z]{2,3})?/collections/", path, re.I)
        )

    def collection_url(self, href, collector):
        if not href or href.startswith("#"):
            return ""
        url = collector.normalize_url(href)
        if not self.is_collection(url):
            return ""
        parts = urlsplit(url)
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path.rstrip("/"), parts.query, "")
        )

    def link_name(self, link, url):
        labels = link.xpath(
            ".//*[contains(concat(' ', normalize-space(@class), ' '), "
            "' header-navigation__secondary-link-label ')]/@data-text | "
            ".//*[contains(concat(' ', normalize-space(@class), ' '), "
            "' header-navigation__mega-link-label ')]/text() | "
            ".//*[contains(concat(' ', normalize-space(@class), ' '), "
            "' header-navigation__mobile-category-link-text ')]/text()"
        )
        for label in labels:
            clean_label = " ".join(str(label or "").split())
            if clean_label:
                return clean_label

        name = self.text(link)
        if not name:
            name = " ".join(
                (link.get("aria-label") or link.get("title") or "").split()
            )
        return name or self.fallback_name(url)

    def add_node(self, nodes, name, url, collector, child=None):
        child = child or {}
        if not url and not child:
            return False

        base_name = " ".join((name or "").split())
        if not base_name:
            base_name = self.fallback_name(url) if url else ""
        if not base_name:
            return False

        node_name = base_name
        suffix = 2
        while node_name in nodes:
            existing = nodes[node_name]
            if existing.get("url") == url:
                if child:
                    for child_name, child_node in child.items():
                        self.add_node(
                            existing.setdefault("child", {}),
                            child_name,
                            child_node.get("url") or "",
                            collector,
                            child_node.get("child") or {},
                        )
                return False
            node_name = f"{base_name} ({suffix})"
            suffix += 1

        collector.add_node(nodes, node_name, url, child)
        return True

    def parse_desktop_group(self, group, collector):
        children = {}
        secondary_items = group.xpath(
            "./nav[contains(concat(' ', normalize-space(@class), ' '), "
            "' header-navigation__secondary-nav ')]/ul/li"
        )
        for item in secondary_items:
            links = item.xpath("./a[1][@href]")
            if not links:
                continue
            link = links[0]
            category_url = self.collection_url(link.get("href") or "", collector)
            if not category_url:
                continue

            grandchildren = {}
            panel_id = link.get("aria-controls")
            panels = (
                group.xpath(".//section[@id=$panel_id]", panel_id=panel_id)
                if panel_id
                else []
            )
            if panels:
                for grandchild in panels[0].xpath(
                    ".//div[contains(concat(' ', normalize-space(@class), ' '), "
                    "' header-navigation__mega-links ')]/a[@href]"
                ):
                    grandchild_url = self.collection_url(
                        grandchild.get("href") or "", collector
                    )
                    if grandchild_url:
                        grandchild_name = self.link_name(grandchild, grandchild_url)
                        if (
                            grandchild_url == category_url
                            and self.comparable_name(grandchild_name).startswith("shopall")
                        ):
                            continue
                        self.add_node(
                            grandchildren,
                            grandchild_name,
                            grandchild_url,
                            collector,
                        )

            self.add_node(
                children,
                self.link_name(link, category_url),
                category_url,
                collector,
                grandchildren,
            )
        return children

    def parse_desktop_navigation(self, tree, collector):
        primary_navigation = tree.xpath("//nav[@aria-label='Primary navigation']")
        if not primary_navigation:
            raise RuntimeError("Huda Beauty primary navigation was not found")

        result = {}
        for index, item in enumerate(primary_navigation[0].xpath("./ul/li")):
            links = item.xpath("./a[1][@href]")
            if not links:
                continue
            link = links[0]
            url = self.collection_url(link.get("href") or "", collector)
            if not url:
                continue

            panel_id = f"header-navigation-primary-{index}"
            groups = tree.xpath("//div[@data-primary-panel=$panel_id]", panel_id=panel_id)
            children = self.parse_desktop_group(groups[0], collector) if groups else {}
            self.add_node(result, self.link_name(link, url), url, collector, children)

        if not result:
            raise RuntimeError("Huda Beauty navigation produced no collection URLs")
        return result

    @classmethod
    def known_urls(cls, nodes, urls=None):
        if urls is None:
            urls = set()
        for node in nodes.values():
            if node.get("url"):
                urls.add(node["url"])
            cls.known_urls(node.get("child") or {}, urls)
        return urls

    def find_node(self, nodes, name):
        comparable = self.comparable_name(name)
        for node_name, node in nodes.items():
            if self.comparable_name(node_name) == comparable:
                return node
        return None

    def mobile_category_name(self, category):
        labels = category.xpath(
            "./button//*[contains(concat(' ', normalize-space(@class), ' '), "
            "' header-navigation__mobile-category-title ')]/text()"
        )
        for label in labels:
            clean_label = " ".join(str(label or "").split())
            if clean_label:
                return clean_label

        links = category.xpath("./a[1][@href]")
        if links:
            url = links[0].get("href") or ""
            return self.link_name(links[0], url)
        return ""

    def merge_mobile_categories(self, tree, result, known_urls, collector):
        drawers = tree.xpath("//*[@id='HeaderNavigationMobileDrawer']")
        shop_all = self.find_node(result, "SHOP ALL")
        if not drawers or not shop_all:
            return

        categories = drawers[0].xpath(
            ".//*[contains(concat(' ', normalize-space(@class), ' '), "
            "' header-navigation__mobile-category ')]"
        )
        for category in categories:
            category_name = self.mobile_category_name(category)
            target = self.find_node(shop_all.get("child") or {}, category_name)
            if target is None:
                continue

            panel_links = category.xpath(
                "./div[contains(concat(' ', normalize-space(@class), ' '), "
                "' header-navigation__mobile-category-panel ')]/a[@href]"
            )
            for link in panel_links:
                url = self.collection_url(link.get("href") or "", collector)
                if not url or url in known_urls:
                    continue
                if self.add_node(
                    target.setdefault("child", {}),
                    self.link_name(link, url),
                    url,
                    collector,
                ):
                    known_urls.add(url)

    def add_remaining_links(self, links, result, known_urls, group_name, collector):
        nodes = {}
        for link in links:
            url = self.collection_url(link.get("href") or "", collector)
            if not url or url in known_urls:
                continue
            name = self.link_name(link, url)
            if name.upper() in self.generic_link_labels:
                name = self.fallback_name(url)
            if self.add_node(nodes, name, url, collector):
                known_urls.add(url)

        if nodes:
            candidate = group_name
            suffix = 2
            while candidate in result:
                candidate = f"{group_name}{suffix}"
                suffix += 1
            self.add_node(result, candidate, "", collector, nodes)

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        result = self.parse_desktop_navigation(tree, collector)
        known_urls = self.known_urls(result)
        self.merge_mobile_categories(tree, result, known_urls, collector)

        headers = tree.xpath(
            "//header[contains(concat(' ', normalize-space(@class), ' '), "
            "' section-header-navigation ')]"
        )
        if headers:
            self.add_remaining_links(
                headers[0].xpath(".//a[@href]"),
                result,
                known_urls,
                "Navigation",
                collector,
            )

        other_links = []
        for link in tree.xpath("//a[@href]"):
            if link.xpath(
                "ancestor::header[contains(concat(' ', normalize-space(@class), ' '), "
                "' section-header-navigation ')]"
            ):
                continue
            other_links.append(link)
        self.add_remaining_links(other_links, result, known_urls, "Other", collector)
        return result


class HudaBeautyCatCol(ShopifyCatCol):
    parser_types = (HudaBeautyNavigationParser,)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        HudaBeautyCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site("data/ml.json"),
            Path(__file__).parent / "ts" / "01-catalog" / "homepage.html",
        ).run()
    finally:
        Tool.close()
