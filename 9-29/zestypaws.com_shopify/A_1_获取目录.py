from pathlib import Path

from config import Tool, base_url
from _ljp.mb.shopify import CatCol


class ZestyPawsCatalog(CatCol):
    """保留导航层级，仅修正主题中已失效的 collection 子路径。"""

    url_replacements = {
        f"{base_url}/collections/best-sellers/dog": f"{base_url}/collections/best-sellers",
        f"{base_url}/collections/bundles/dog": f"{base_url}/collections/bundles",
        f"{base_url}/collections/ancient-elements/dog": f"{base_url}/collections/ancient-elements",
        f"{base_url}/collections/vet-strength/dog": f"{base_url}/collections/vet-strength",
        f"{base_url}/collections/all/dog": f"{base_url}/collections/dogs",
        f"{base_url}/collections/treats-chews/dog": f"{base_url}/collections/treats-chews",
        f"{base_url}/collections/drops-oils/dog": f"{base_url}/collections/drops-oils",
        f"{base_url}/collections/powder-supplements/dog": f"{base_url}/collections/powder-supplements",
        f"{base_url}/collections/bath-time/dog": f"{base_url}/collections/bath-time",
        f"{base_url}/collections/shop-weight-management/dog": f"{base_url}/collections/shop-weight-management",
        f"{base_url}/collections/oral-health-for-dogs/dog": f"{base_url}/collections/oral-health-for-dogs",
        f"{base_url}/collections/healthy-aging/dog": f"{base_url}/collections/healthy-aging",
        f"{base_url}/collections/best-sellers/cat": f"{base_url}/collections/best-sellers",
        f"{base_url}/collections/bundles/cat": f"{base_url}/collections/bundles",
        f"{base_url}/collections/all/cat": f"{base_url}/collections/cats",
        f"{base_url}/collections/treats-chews/cat": f"{base_url}/collections/treats-chews",
        f"{base_url}/collections/drops-oils/cat": f"{base_url}/collections/drops-oils",
        f"{base_url}/collections/mousses/cat": f"{base_url}/collections/mousses",
        f"{base_url}/collections/diffuser/cat": f"{base_url}/collections/diffuser",
    }

    def replace_urls(self, nodes):
        for node in nodes.values():
            url = node.get("url")
            if url in self.url_replacements:
                node["url"] = self.url_replacements[url]
            self.replace_urls(node.get("child") or {})

    def after_parse(self, menu):
        self.replace_urls(menu)
        return menu


if __name__ == "__main__":
    ZestyPawsCatalog(
        Tool,
        base_url,
        Tool.File.path_add_site("data/ml.json"),
        Path(__file__).parent / "ts" / "01-catalog" / "homepage.html",
    ).run()
