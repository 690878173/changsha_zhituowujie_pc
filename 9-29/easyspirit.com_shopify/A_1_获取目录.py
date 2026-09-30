"""Collect Easy Spirit's public Shopify collection navigation."""

import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class EasySpiritMegaMenuParser(CatalogParser):
    """Parse the server-rendered desktop mega menu and homepage collections."""

    generic_link_labels = {"SHOP NOW", "SHOP", "SHOP ALL", "START SHOPPING"}

    def matches(self, html):
        return "<mega-menu" in html and "MegaMenu-Content-" in html

    @staticmethod
    def text(node):
        values = node.xpath(
            ".//text()[not(ancestor::svg)][not(ancestor::script)]"
            "[not(ancestor::style)]"
        )
        return " ".join(" ".join(values).split())

    @staticmethod
    def is_collection(url):
        return urlsplit(url or "").path.rstrip("/").lower().startswith("/collections/")

    @staticmethod
    def fallback_name(url):
        handle = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]
        return handle.replace("-", " ").title()

    @staticmethod
    def comparable_name(name):
        normalized = " ".join((name or "").lower().split())
        if normalized.startswith("all "):
            normalized = normalized[4:]
        return normalized

    def collection_url(self, href, collector):
        if not href or href.startswith("#"):
            return ""
        url = collector.normalize_url(href)
        parts = urlsplit(url)
        path = parts.path.rstrip("/")
        if not path.lower().startswith("/collections/"):
            return ""
        return urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))

    def link_name(self, link, url):
        name = self.text(link)
        if not name:
            name = " ".join(
                (link.get("aria-label") or link.get("title") or "").split()
            )
        if not name:
            image_alt = link.xpath("string(.//img[1]/@alt)")
            name = " ".join(image_alt.split())
        return name or self.fallback_name(url)

    def promo_name(self, item, link, url):
        headings = item.xpath("(.//h1 | .//h2 | .//h3 | .//h4 | .//h5 | .//h6)[1]")
        if headings:
            name = self.text(headings[0])
            if name:
                return name
        return self.link_name(link, url)

    def add_node(self, nodes, name, url, collector, child=None):
        child = child or {}
        if not url and not child:
            return False

        base_name = " ".join((name or "").split())
        if not base_name:
            base_name = self.fallback_name(url) if url else ""
        if not base_name:
            return False

        if url and not child and any(
            node.get("url") == url for node in nodes.values()
        ):
            return False

        node_name = base_name
        suffix = 2
        while node_name in nodes:
            existing = nodes[node_name]
            if existing.get("url") == url and not child:
                return False
            node_name = f"{base_name} ({suffix})"
            suffix += 1

        collector.add_node(nodes, node_name, url, child)
        return True

    def panel_children(self, panel_item, collector):
        children = {}
        for link in panel_item.xpath("./ul[1]/li/a[1][@href]"):
            url = self.collection_url(link.get("href") or "", collector)
            if url:
                self.add_node(children, self.link_name(link, url), url, collector)
        return children

    def parse_desktop_menu(self, tree, collector):
        menus = tree.xpath("//mega-menu")
        if not menus:
            raise RuntimeError("Easy Spirit desktop mega menu was not found")

        result = {}
        for top_item in menus[0].xpath("./ul/li"):
            triggers = top_item.xpath("./a[1][@href]")
            if not triggers:
                continue

            trigger = triggers[0]
            top_name = self.text(trigger)
            top_url = self.collection_url(trigger.get("href") or "", collector)
            panel_id = trigger.get("aria-controls")
            panels = (
                top_item.xpath("./div[@id=$panel_id]", panel_id=panel_id)
                if panel_id
                else []
            )
            children = {}

            if panels:
                for panel_item in panels[0].xpath("./ul[1]/li"):
                    headings = panel_item.xpath("./a[1][@href]")
                    if not headings:
                        continue
                    heading = headings[0]
                    group_name = self.text(heading)
                    group_url = self.collection_url(heading.get("href") or "", collector)
                    group_children = self.panel_children(panel_item, collector)

                    if group_children:
                        is_redundant = (
                            bool(top_url)
                            and group_url == top_url
                            and self.comparable_name(group_name)
                            == self.comparable_name(top_name)
                        )
                        if is_redundant:
                            for child_name, child_node in group_children.items():
                                self.add_node(
                                    children,
                                    child_name,
                                    child_node.get("url") or "",
                                    collector,
                                    child_node.get("child") or {},
                                )
                        elif group_name:
                            self.add_node(
                                children,
                                group_name,
                                group_url,
                                collector,
                                group_children,
                            )
                        else:
                            for child_name, child_node in group_children.items():
                                self.add_node(
                                    children,
                                    child_name,
                                    child_node.get("url") or "",
                                    collector,
                                    child_node.get("child") or {},
                                )
                    elif group_url:
                        self.add_node(
                            children,
                            self.promo_name(panel_item, heading, group_url),
                            group_url,
                            collector,
                        )

            if top_name and (top_url or children):
                self.add_node(result, top_name, top_url, collector, children)

        if not result:
            raise RuntimeError("Easy Spirit desktop navigation produced no collection URLs")
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
        result = self.parse_desktop_menu(tree, collector)
        known_urls = self.known_urls(result)

        mobile_links = tree.xpath(
            "//nav[@aria-label='Main Menu Drawer']//a[@href]"
        )
        self.add_remaining_links(
            mobile_links, result, known_urls, "Navigation", collector
        )

        other_links = []
        for link in tree.xpath("//a[@href]"):
            if link.xpath("ancestor::mega-menu") or link.xpath("ancestor::nav"):
                continue
            other_links.append(link)
        self.add_remaining_links(other_links, result, known_urls, "Other", collector)

        result["Other,Other All Shoes"] = "https://easyspirit.com/collections/shoes"
        result['ACTIVE,ACTIVE EASYCRUZ SOEASY™ SNEAKERS'] = 'https://easyspirit.com/collections/shoes?filter.v.availability=1'
        return result


class EasySpiritCatCol(ShopifyCatCol):
    parser_types = (EasySpiritMegaMenuParser,)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        EasySpiritCatCol(
            Tool,
            base_url,
            Tool.File.path_add_site("data/ml.json"),
            Path(__file__).parent / "ts" / "01-catalog" / "homepage.html",
        ).run()
    finally:
        Tool.close()
