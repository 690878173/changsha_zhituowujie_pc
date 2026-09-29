import re
from urllib.parse import quote

from config import Tool
from _ljp.mb.mg_shopify import Get_Product


input_file = Tool.File.path_add_site("data/detail_url.json")
output_file = Tool.File.path_add_site("res/result.csv")
output_ts_file = Tool.File.path_add_site("res/ts_res.csv")
fail_file = Tool.File.path_add_site("fail/4.json")
index_path = Tool.File.path_add_site("hc/4/index.json")
catch_path = Tool.File.path_add_site("hc/4/catch.json")

catch_save_num = None
skip_input_url_ls = []
skip_output_url_ls = []
fieldnames = None
ts_num = None
if_wp = False
flush = False


class Pc(Get_Product):
    def storefront_settings(self):
        # 站点专有信息只放在 Step 接口中，不污染 Tool.config。
        return {
            "storefront_token": "07a42fb28f2b14504c14f1de815cbd45",
            "store_domain": "checkout.honeylove.com",
            "api_version": "unstable",
            "country": "US",
            "language": "EN",
            "request_delay": 7,
        }

    def _custom_fields(self, custom_data):
        """Extract the PDP-only fields from Honeylove's product-data payload."""
        fabric_details = custom_data.get("fabricDetails") or []
        if not isinstance(fabric_details, list):
            fabric_details = [fabric_details]
        fabric = "<br>".join(str(item) for item in fabric_details if item)
        return {
            "Size & Fit": self.tool.HTML.clean_product_desc_str(
                str(custom_data.get("fitRecommendation") or "")
            ),
            "Fabric": self.tool.HTML.clean_product_desc_str(fabric),
        }

    @staticmethod
    def _option_pairs(selected_options):
        pairs = []
        for option in selected_options or []:
            name = str(option.get("name") or "").strip()
            value = str(option.get("value") or "").strip()
            if name and value:
                pairs.append({"name": name, "value": value})
        return pairs

    @staticmethod
    def _band_and_cup(value):
        match = re.fullmatch(r"\s*(\d+)\s*([A-Za-z]+)\s*", str(value or ""))
        if not match:
            return None
        return match.group(1), match.group(2).upper()

    @staticmethod
    def _variant_id_suffix(variant):
        return str(variant.get("id") or "").rstrip("/").split("/")[-1]

    def _unique_sku(self, candidate, variant, used_skus):
        candidate = str(candidate or "").strip() or self._variant_id_suffix(variant)
        candidate = candidate or "variant"
        if candidate not in used_skus:
            used_skus.add(candidate)
            return candidate

        variant_id = self._variant_id_suffix(variant)
        fallback = f"{candidate}-{variant_id}" if variant_id else candidate
        suffix = 2
        while fallback in used_skus:
            fallback = f"{candidate}-{variant_id or 'variant'}-{suffix}"
            suffix += 1
        used_skus.add(fallback)
        return fallback

    def _variant_image(self, selected_options, color_images):
        color = next(
            (option["value"] for option in selected_options if option["name"].lower() == "color"),
            "",
        )
        return color_images.get(color, "")

    def _normalise_variants(self, rich_product, handle):
        """Make Honeylove's display variants consumable by the shared exporter."""
        color_images = {
            str(color.get("color") or "").strip(): (color.get("featuredImage") or {}).get("url", "")
            for color in rich_product.get("colors") or []
            if isinstance(color, dict)
        }
        is_band_and_cup = bool(rich_product.get("isBandAndCupProduct"))
        used_skus = {handle}
        variants = []

        for source_variant in rich_product.get("variants") or []:
            if not isinstance(source_variant, dict):
                continue
            selected_options = self._option_pairs(source_variant.get("selectedOptions"))
            source_sku = str(source_variant.get("sku") or "").strip()
            source_sku = source_sku or f"{handle}-{self._variant_id_suffix(source_variant)}"
            image_url = self._variant_image(selected_options, color_images)
            band_and_cup_sizes = source_variant.get("bandAndCupSizes") or []
            if isinstance(band_and_cup_sizes, str):
                band_and_cup_sizes = [band_and_cup_sizes]

            if is_band_and_cup and band_and_cup_sizes:
                base_options = [
                    option for option in selected_options
                    if option["name"].lower() not in {"size", "band", "cup"}
                ]
                for band_and_cup in band_and_cup_sizes:
                    parsed = self._band_and_cup(band_and_cup)
                    if not parsed:
                        continue
                    band, cup = parsed
                    variant = dict(source_variant)
                    variant["selectedOptions"] = [
                        *base_options,
                        {"name": "Band", "value": band},
                        {"name": "Cup", "value": cup},
                    ]
                    variant["sku"] = self._unique_sku(
                        f"{source_sku}-{band}{cup}", source_variant, used_skus,
                    )
                    variant["image"] = {"url": image_url} if image_url else {}
                    variants.append(variant)
                continue

            variant = dict(source_variant)
            variant["selectedOptions"] = selected_options
            variant["sku"] = self._unique_sku(source_sku, source_variant, used_skus)
            variant["image"] = {"url": image_url} if image_url else {}
            variants.append(variant)

        return variants, color_images

    @staticmethod
    def _options_from_variants(variants):
        values_by_name = {}
        for variant in variants:
            for option in variant.get("selectedOptions") or []:
                name = option.get("name")
                value = option.get("value")
                if name and value:
                    values_by_name.setdefault(name, [])
                    if value not in values_by_name[name]:
                        values_by_name[name].append(value)
        return [
            {"name": name, "values": values}
            for name, values in values_by_name.items()
        ]

    def fetch_product(self, url, category):
        """Use Honeylove's PDP API because Storefront returns a placeholder variant."""
        try:
            page_response = self.tool.get(url)
            if page_response.status_code == 404:
                return []
            if not 200 <= page_response.status_code < 400:
                raise RuntimeError(f"页面请求状态码: {page_response.status_code}")

            page_url = getattr(page_response, "url", None) or url
            handle = self.tool.URL.get_handle(page_url)
            api_url = self.tool.URL.add_site(f"/product-data/{quote(handle, safe='')}")
            response = self.tool.get(api_url, params={"no-filtering": "true"})
            if response.status_code != 200:
                raise RuntimeError(f"产品数据接口状态码: {response.status_code}")

            payload = response.json()
            product_data = payload.get("product") or {}
            base_product = product_data.get("product") or {}
            rich_product = payload.get("productWithVariants") or {}
            if not base_product or not rich_product:
                return []

            variants, color_images = self._normalise_variants(rich_product, handle)
            if not variants:
                return []

            images = []
            featured_image = base_product.get("featuredImage") or {}
            if featured_image.get("url"):
                images.append(featured_image)
            images.extend(
                {"url": image_url}
                for image_url in color_images.values()
                if image_url
            )

            shopify_product = dict(base_product)
            shopify_product["handle"] = base_product.get("handle") or handle
            shopify_product["description"] = (
                base_product.get("descriptionHtml") or base_product.get("description") or ""
            )
            shopify_product["availableForSale"] = any(
                variant.get("availableForSale") for variant in variants
            )
            shopify_product["variants"] = {"nodes": variants}
            shopify_product["options"] = self._options_from_variants(variants)
            shopify_product["images"] = {"nodes": images}
            shopify_product[self.tool.custom_key] = self._custom_fields(
                product_data.get("productCustomData") or {}
            )
            shopify_product["__url"] = page_url

            parent = self.mg_shopify_to_woocommerce(
                shopify_product,
                brand=self.tool.site,
                custom_categories=category,
            )
            return [parent, *self.mg_create_variation_products(shopify_product, parent)]
        except Exception as exc:
            self.tool.print(f"[ERROR] Honeylove 产品解析失败:{url}: {exc}", color="yellow")
            return []


if __name__ == "__main__":
    Pc(
        tool=Tool,
        input_path=input_file,
        output_path=output_file,
        fail_file=fail_file,
        catch_path=catch_path,
        index_path=index_path,
        output_ts_file=output_ts_file,
        ts_num=ts_num,
        catch_save_num=catch_save_num,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        fieldnames=fieldnames,
        flush=flush,
        max_threads=10,
        if_wp=if_wp,
    ).run()
