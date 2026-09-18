import json
import re

from lxml import etree

from config import Tool

# 文件路径配置
input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site("res/result.csv")
fail_file = Tool.File.path_add_site('data/fail.json')

catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
# 携带原始url输出文件
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

# Set to None for the user's full run. Thirteen pages provide a broad SKU sample.
ts_num = 13

catch_save_num = None
# URL黑名单
skip_input_url_ls = []
# 未实现字段
skip_output_url_ls = []

flush = False

# CSV输出表头,默认就应该为None，表头后续会处理
fieldnames = None

max_threads = 2

from _ljp.mb.zj import Get_Product


class Pc(Get_Product):
    def fetch_product(self, url, category):
        response = Tool.get(url)
        if response.status_code != 200:
            Tool.print(f"商品页请求失败: {response.status_code} {url}", color="red")
            return []
        return _T(url, category, response.text).run()


class _T:
    """Convert Pampers JSON-LD Product and ProductGroup records into product rows."""

    CUSTOM_FIELDS = ("Size Range", "Age Range", "Baby Weight Range", "Baby Weight", "Retailers")

    def __init__(self, url, category, response_text):
        self.url = url
        self.category = category
        self.html = etree.HTML(response_text)

    @staticmethod
    def _text(values):
        return " ".join(" ".join(values).split())

    @staticmethod
    def _numeric_price(value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        if isinstance(value, str):
            matched = re.fullmatch(r"\s*\$?(\d+(?:\.\d+)?)\s*", value)
            if matched:
                return float(matched.group(1))
        return ""

    def get_product_data(self):
        for script in self.html.xpath("//script[@type='application/ld+json']"):
            try:
                payload = json.loads(script.text or "")
            except json.JSONDecodeError:
                continue
            records = payload if isinstance(payload, list) else [payload]
            for record in records:
                if isinstance(record, dict) and record.get("@type") in {"Product", "ProductGroup"}:
                    return record
        return None

    def get_name(self, product_data):
        names = self.html.xpath("//section[@id='to-main-content']//h1[1]//text()")
        return self._text(names) or product_data.get("name", "")

    def get_images(self, product_data):
        images = self.html.xpath(
            "//section[@id='to-main-content']//img[@data-testid='image-asset']/@src"
        )
        primary_image = product_data.get("image")
        if isinstance(primary_image, dict):
            images.append(primary_image.get("url", ""))
        elif isinstance(primary_image, str):
            images.append(primary_image)

        result = []
        for image in images:
            if image and image not in result:
                result.append(image)
        return result

    def get_tags(self, product_data):
        tags = self.html.xpath(
            "//section[@id='to-main-content']//aside[contains(@class, 'right-column')]"
            "//span[@data-component='StaticTag']//span/text()"
        )
        tags.append(product_data.get("category", ""))
        result = []
        for tag in tags:
            tag = self._text([str(tag)])
            if tag and tag not in result:
                result.append(tag)
        return ",".join(result)

    @staticmethod
    def get_properties(product_data):
        properties = {}
        for item in product_data.get("additionalProperty") or []:
            if isinstance(item, dict) and item.get("name"):
                properties[item["name"]] = str(item.get("value", ""))
        return properties

    @staticmethod
    def get_offers(product_data):
        offers = product_data.get("offers") or {}
        if isinstance(offers, dict):
            offers = offers.get("offers") or [offers]
        return [offer for offer in offers if isinstance(offer, dict)]

    @staticmethod
    def get_offer_sku(offer):
        return str(offer.get("sku") or offer.get("gtin13") or offer.get("gtin") or "").strip()

    @staticmethod
    def get_variant_attributes(label, fallback):
        matched = re.match(r"^(.*?)\s*(?:\u2014|-)\s*Pack of\s+(.+)$", label or "")
        if matched:
            return {"Size": matched.group(1).strip(), "Pack Count": matched.group(2).strip()}
        if fallback:
            return {"Size": fallback}
        return {}

    def get_variant_lookup(self, product_data):
        lookup = {}
        for variant in product_data.get("hasVariant") or []:
            if not isinstance(variant, dict):
                continue
            key = str(variant.get("size") or variant.get("name") or "").casefold()
            if key:
                lookup[key] = variant
        return lookup

    def get_variant_seeds(self, product_data):
        grouped = {}
        for offer in self.get_offers(product_data):
            sku = self.get_offer_sku(offer)
            if sku:
                grouped.setdefault(sku, []).append(offer)
        if grouped:
            return [(sku, offers) for sku, offers in grouped.items()]

        seeds = []
        for variant in product_data.get("hasVariant") or []:
            if isinstance(variant, dict) and self.get_offer_sku(variant):
                seeds.append((self.get_offer_sku(variant), [variant]))
        return seeds

    def get_custom_fields(self, properties, variant, offers):
        retailers = []
        for offer in offers:
            seller = offer.get("seller") or {}
            seller_name = seller.get("name", "") if isinstance(seller, dict) else ""
            if seller_name and seller_name not in retailers:
                retailers.append(seller_name)

        baby_weight = str(variant.get("description", "")) if variant else ""
        if not re.search(r"\b(?:lb|lbs|pounds?)\b", baby_weight, flags=re.IGNORECASE):
            baby_weight = ""

        return {
            "Size Range": properties.get("Size Range", ""),
            "Age Range": properties.get("Age Range", ""),
            "Baby Weight Range": properties.get("Baby Weight", ""),
            "Baby Weight": baby_weight,
            "Retailers": ", ".join(retailers),
        }

    def build_variations(self, product_data, name, images, tags, properties, seeds):
        parent_sku = str(product_data.get("sku") or seeds[0][0]).strip()
        variants = self.get_variant_lookup(product_data)
        rows = []
        for sku, offers in seeds:
            offer = offers[0]
            label = str(offer.get("name", ""))
            raw_size = label.split("\u2014", 1)[0].strip() if label else ""
            variant = variants.get(raw_size.casefold(), {})
            attributes = self.get_variant_attributes(label, str(variant.get("size", "")))
            price = next(
                (self._numeric_price(item.get("price")) for item in offers if self._numeric_price(item.get("price")) != ""),
                "",
            )
            if price == "":
                variant_offer = variant.get("offers") or {}
                if isinstance(variant_offer, dict):
                    price = self._numeric_price(variant_offer.get("price"))

            availability = " ".join(str(item.get("availability", "")) for item in offers)
            stock = 0 if "OutOfStock" in availability else None
            rows.append(
                Tool.Product.Variation(
                    url=self.url,
                    cat=self.category,
                    imgs=images,
                    name=name,
                    desc=product_data.get("description", ""),
                    price=price,
                    sku=sku,
                    parent=parent_sku,
                    att=attributes,
                    brand=(product_data.get("brand") or {}).get("name", "Pampers"),
                    stock=stock,
                    tags=tags,
                    **self.get_custom_fields(properties, variant, offers),
                ).to_dic()
            )
        return rows

    def build_simple(self, product_data, name, images, tags, properties):
        offers = self.get_offers(product_data)
        price = next(
            (self._numeric_price(item.get("price")) for item in offers if self._numeric_price(item.get("price")) != ""),
            "",
        )
        sku = str(product_data.get("sku") or (self.get_offer_sku(offers[0]) if offers else "")).strip()
        if not sku:
            sku = Tool.URL.get_handle(self.url)
        return Tool.Product.Simple(
            url=self.url,
            cat=self.category,
            imgs=images,
            name=name,
            desc=product_data.get("description", ""),
            price=price,
            sku=sku,
            brand=(product_data.get("brand") or {}).get("name", "Pampers"),
            tags=tags,
            **self.get_custom_fields(properties, {}, offers),
        ).to_dic()

    def run(self):
        product_data = self.get_product_data()
        if not product_data:
            Tool.print(f"未找到 Product JSON-LD: {self.url}", color="red")
            return []

        name = self.get_name(product_data)
        images = self.get_images(product_data)
        if not name or not images:
            Tool.print(f"商品缺少名称或图片: {self.url}", color="red")
            return []

        tags = self.get_tags(product_data)
        properties = self.get_properties(product_data)
        seeds = self.get_variant_seeds(product_data)
        if len(seeds) > 1:
            return self.build_variations(product_data, name, images, tags, properties, seeds)
        return [self.build_simple(product_data, name, images, tags, properties)]






if __name__ == '__main__':
    pc = Pc(tool=Tool,
            input_path=input_file,
            output_path=output_file,
            fail_file=fail_file,
            skip_input_url_ls=skip_input_url_ls,
            skip_output_url_ls=skip_output_url_ls,
            ts_num=ts_num,
            fieldnames=fieldnames,
            catch_path=catch_path,
            index_path=index_path,
            output_ts_file=output_ts_file,
            flush=flush,
            max_threads=max_threads,
            catch_save_num=catch_save_num
            )
    pc.run()
