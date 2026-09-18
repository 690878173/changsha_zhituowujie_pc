import json

from lxml import etree

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
        return {
            "storefront_token": "37411aa1da884ca2e0b4e66a2194f8f8",
            "store_domain": "sportsresearch.myshopify.com",
            "api_version": "2023-04",
            "country": "US",
            "language": "EN",
        }

    def zdy_zd(self, url, html_text=None):
        tree = etree.HTML(html_text or "")
        if tree is None:
            return {}

        payloads = tree.xpath('//script[@id="__NEXT_DATA__"]/text()')
        if not payloads:
            return {}

        try:
            page_props = json.loads(payloads[0])["props"]["pageProps"]
        except (KeyError, TypeError, json.JSONDecodeError):
            return {}

        product = page_props.get("product") or {}
        content_product = page_props.get("contentProduct") or {}
        fields = {}
        source_fields = {
            "Description": product.get("descriptionHtml") or product.get("description"),
            "Suggested Use": content_product.get("suggestedUse"),
        }
        for name, value in source_fields.items():
            if isinstance(value, str) and value.strip():
                fields[name] = self.tool.HTML.clean_product_desc_str(value)

        return fields


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
        max_threads=10,
        if_wp=if_wp,
        flush=flush,
    ).run()
