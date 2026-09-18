"""Black Girl Sunscreen product detail parser.

The site's JSON-LD is sometimes inside an HTML comment and WooCommerce puts
variation SKU/price/attributes in ``data-product_variations``.  Parse the raw
response first and use the visible HTML as a fallback.
"""
from __future__ import annotations

import html as html_lib
import json
import re
from urllib.parse import urlparse

from lxml import etree

from config import Tool
from _ljp.mb.zj import Get_Product

input_file = "data/detail_url.json"
output_file = Tool.File.path_add_site("res/result.csv")
fail_file = Tool.File.path_add_site("data/fail.json")
catch_path = Tool.File.path_add_site("hc/3/data.json")
index_path = Tool.File.path_add_site("hc/3/index.json")
output_ts_file = Tool.File.path_add_site("hc/3/result.csv")
ts_num = None
skip_input_url_ls: list[str] = []
skip_output_url_ls: list[str] = []
headers = None
cookies = None
fieldnames = None

_JSONLD_RE = re.compile(
    r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    re.I | re.S,
)
_NUMBER_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def _text(value) -> str:
    if isinstance(value, (list, tuple)):
        value = " ".join(_text(item) for item in value)
    return " ".join(str(value or "").split()).strip()


def _price(value) -> str:
    match = _NUMBER_RE.search(str(value or "").replace(",", ""))
    if not match:
        return ""
    try:
        return f"{float(match.group()):.2f}"
    except (TypeError, ValueError):
        return ""


def _slug(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] or url


class _T:
    def __init__(self, url: str, category: str, res_text: str):
        self.url, self.category, self.res_text = url, category, res_text or ""
        self.html = etree.HTML(self.res_text) or etree.Element("html")
        self.slug = _slug(url)
        self.jsonld_products = self._jsonld_products()

    def _jsonld_products(self) -> list[dict]:
        # etree hides scripts inside comments; inspect the raw response instead.
        products = []
        for match in _JSONLD_RE.finditer(self.res_text):
            raw = html_lib.unescape(match.group(1)).strip()
            raw = raw[4:] if raw.startswith("<!--") else raw
            raw = raw[:-3] if raw.endswith("-->") else raw
            try:
                payload = json.loads(raw.strip())
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            nodes = payload if isinstance(payload, list) else payload.get("@graph", [payload])
            for node in nodes:
                typ = node.get("@type") if isinstance(node, dict) else None
                if isinstance(node, dict) and (typ == "Product" or (isinstance(typ, list) and "Product" in typ)):
                    products.append(node)
        return products

    @property
    def product_schema(self) -> dict:
        return self.jsonld_products[0] if self.jsonld_products else {}

    def _schema_price(self) -> str:
        offers = self.product_schema.get("offers", [])
        offers = [offers] if isinstance(offers, dict) else offers
        for offer in offers or []:
            if not isinstance(offer, dict):
                continue
            value = offer.get("price")
            specs = offer.get("priceSpecification")
            if value in (None, ""):
                if isinstance(specs, dict):
                    value = specs.get("price")
                elif isinstance(specs, list):
                    value = next((s.get("price") for s in specs if isinstance(s, dict)), None)
            if _price(value):
                return _price(value)
        return ""

    def name(self) -> str:
        return (_text(self.html.xpath("string((//h1[contains(@class,'product_title')][1]))"))
                or _text(self.html.xpath("string((//h1)[1])"))
                or _text(self.product_schema.get("name")))

    def sku(self) -> str:
        nodes = self.html.xpath("//*[contains(concat(' ',normalize-space(@class),' '),' sku ')]//text()")
        for node in nodes:
            value = re.sub(r"^SKU\s*:\s*", "", _text(node), flags=re.I)
            if value and value.upper() not in {"N/A", "NA", "NONE"}:
                return value
        return _text(self.product_schema.get("sku")) or self.slug

    def price(self) -> str:
        value = self._schema_price()
        if value:
            return value
        values = self.html.xpath(
            "//div[contains(@class,'summary')]//p[contains(@class,'price')]//bdi//text()"
            " | //p[contains(@class,'price')]//bdi//text()"
        )
        return _price(values[0] if values else "")

    def description(self) -> str:
        nodes = self.html.xpath("//div[contains(concat(' ',normalize-space(@class),' '), ' woocommerce-product-details__short-description ')]")
        return etree.tostring(nodes[0], encoding="unicode", method="html") if nodes else ""

    def summary(self) -> str:
        nodes = self.html.xpath("//div[contains(@class,'wd-accordion-item')]")
        return etree.tostring(nodes[0], encoding="unicode", method="html") if nodes else ""

    def images(self) -> list[str]:
        nodes = self.html.xpath("//div[contains(concat(' ',normalize-space(@class),' '), ' wd-gallery-images ')]//img")
        if not nodes:
            nodes = self.html.xpath("//div[contains(@class,'wd-gallery-inner')]//img")
        result, seen = [], set()
        for node in nodes:
            value = (node.get("data-large_image") or node.get("data-src") or node.get("src") or "").strip()
            if value and not value.startswith("data:") and value not in seen:
                result.append(value)
                seen.add(value)
        return result

    def brand(self) -> str:
        brand = self.product_schema.get("brand", {})
        return _text(brand.get("name") if isinstance(brand, dict) else brand) or "Black Girl Sunscreen"

    def variations(self) -> list[dict]:
        forms = self.html.xpath("//form[contains(@class,'variations_form')]")
        if not forms:
            return []
        raw = forms[0].get("data-product_variations") or ""
        try:
            values = json.loads(html_lib.unescape(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            return []
        return [v for v in values if isinstance(v, dict) and v.get("variation_is_visible", True)]

    @staticmethod
    def attrs(variation: dict) -> dict:
        result = {}
        for key, value in (variation.get("attributes") or {}).items():
            value = _text(value)
            if value:
                result[re.sub(r"^attribute_(?:pa_)?", "", str(key), flags=re.I)] = value
        return result

    def make_product(self, *, name, sku, price, desc, imgs, att=None, parent=None, typ="simple"):
        common = dict(
            url=self.url, cat=self.category, imgs=Tool.Product.clean_imgs(imgs), name=name,
            desc=desc, price=Tool.clean_price(price), sku=sku, brand=self.brand(), stock=1000,
            is_upload=0, **{"Summary (product.metafields.c_f.zdy_tabs1)": self.summary()},
        )
        if typ == "variation":
            return Tool.Product.Variation(att=att or {}, parent=parent, **common).to_dic()
        return Tool.Product.Simple(parent=parent, **common).to_dic()

    def run(self) -> list[dict]:
        name, desc, imgs, parent_sku = self.name(), self.description(), self.images(), self.sku()
        variations = self.variations()
        if not variations:
            return [self.make_product(name=name, sku=parent_sku, price=self.price(), desc=desc, imgs=imgs)]

        attributes = [self.attrs(v) for v in variations]
        values = {}
        for att in attributes:
            for key, value in att.items():
                if value not in values.setdefault(key, []):
                    values[key].append(value)
        parent = self.make_product(name=name, sku=parent_sku, price="", desc=desc, imgs=imgs)
        parent["Type"] = "variable"
        for index, (key, vals) in enumerate(values.items(), 1):
            parent[f"Attribute {index} name"] = key
            parent[f"Attribute {index} value(s)"] = ", ".join(vals)
        rows = [parent]
        for variation, att in zip(variations, attributes):
            sku = _text(variation.get("sku")) or f"{parent_sku}-{'-'.join(att.values())}"
            rows.append(self.make_product(name=name, sku=sku, price=_price(variation.get("display_price")),
                                          desc=desc, imgs=imgs, att=att, parent=parent_sku, typ="variation"))
        return rows


class Pc(Get_Product):
    def fetch_product(self, url, category):
        response = Tool.get(url, headers=headers, cookies=cookies)
        if getattr(response, "status_code", 0) != 200 or not response.text:
            raise RuntimeError(f"详情页请求失败: status={getattr(response, 'status_code', 0)}")
        return _T(url, category, response.text).run()


if __name__ == "__main__":
    Pc(tool=Tool, input_path=input_file, output_path=output_file, fail_file=fail_file,
       skip_input_url_ls=skip_input_url_ls, skip_output_url_ls=skip_output_url_ls,
       ts_num=ts_num, fieldnames=fieldnames, catch_path=catch_path,
       index_path=index_path, output_ts_file=output_ts_file).run()
