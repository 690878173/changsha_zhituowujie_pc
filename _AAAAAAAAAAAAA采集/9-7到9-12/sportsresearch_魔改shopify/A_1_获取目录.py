import json
import re
from pathlib import Path

from config import Tool, base_url
from _ljp.mb.mg_shopify import CatCol, CatalogParser


save_path = Tool.File.path_add_site("data/ml.json")
html_path = Path(__file__).with_name("1.html")


class SportsResearchCatalogParser(CatalogParser):
    """Parse the homepage navigation data into the standard catalog tree."""

    next_data_pattern = re.compile(
        r'<script[^>]*\bid=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        re.DOTALL,
    )

    def matches(self, html):
        return "__NEXT_DATA__" in html and "shopColumnOneHeading" in html

    def parse(self, html, collector):
        match = self.next_data_pattern.search(html)
        if not match:
            raise RuntimeError("Homepage __NEXT_DATA__ was not found.")

        try:
            navigation = json.loads(match.group(1))["props"]["pageProps"]["navigation"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Unable to parse homepage navigation: {exc}") from exc

        groups = {}
        columns = (
            ("shopColumnOneHeading", "shopColumnOneLinksCollection"),
            ("shopColumnTwoHeading", "shopColumnTwoLinksCollection"),
            ("shopColumnThreeHeading", "shopColumnThreeLinksCollection"),
        )
        for heading_key, links_key in columns:
            heading = navigation.get(heading_key)
            children = {}
            for link in (navigation.get(links_key) or {}).get("items") or []:
                collector.add_node(
                    children,
                    link.get("label"),
                    link.get("target"),
                )
            if children:
                collector.add_node(groups, heading, child=children)

        # Keep the all-products CTA as one leaf without replacing public groups.
        shop_all = navigation.get("shopColumn1Cta") or {}
        collector.add_node(groups, shop_all.get("label"), shop_all.get("target"))

        if len(groups) < 2:
            raise RuntimeError("Homepage navigation did not provide multiple category groups.")

        menu = {}
        collector.add_node(menu, "Shop", child=groups)
        return menu


class SportsResearchCatCol(CatCol):
    parser_types = (SportsResearchCatalogParser,)


if __name__ == "__main__":
    SportsResearchCatCol(Tool, base_url, save_path, html_path).run()
    Tool.close()
