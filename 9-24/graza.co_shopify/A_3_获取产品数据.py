"""Collect a small Graza product sample with the requested PDP tab fields."""

import json
from pathlib import Path

from lxml import html as lxml_html

from config import Tool
from _ljp.mb.shopify import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
fail_file = Tool.File.path_add_site('fail/4_custom_tabs_v1.json')
index_path = Tool.File.path_add_site('hc/4_custom_tabs_v1/index.json')
catch_path = Tool.File.path_add_site('hc/4_custom_tabs_v1/catch.json')

skip_input_url_ls = []
skip_output_url_ls = []
fieldnames = None
ts_num = 10


class Pc(Get_Product):
    """Read only the requested custom fields from Graza's product tab payload."""

    field_names = {
        'Details': 'Details',
        'Harvest': 'Harvest',
        'Uses': 'Use',
        'Refills': 'Refills',
    }

    requirements = {
        "simple": ("SKU", "Name", "Images"),
        "variable": ("SKU", "Name", "Images"),
        "variation": ("SKU", "Name", "Parent"),
    }

    @classmethod
    def find_tabs(cls, value):
        if isinstance(value, dict):
            tabs = value.get('tabs')
            if isinstance(tabs, list) and any(
                isinstance(tab, dict) and tab.get('heading') in cls.field_names for tab in tabs
            ):
                return tabs
            for child in value.values():
                found = cls.find_tabs(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = cls.find_tabs(child)
                if found is not None:
                    return found
        return None

    def zdy_zd(self, handle, html_text):
        """Return Details, Harvest, Use, and Refills from the PDP's tab JSON."""
        fields = {name: '' for name in self.field_names.values()}
        tree = lxml_html.fromstring(html_text)
        product_hero = next(
            (
                node for node in tree.iter('product-hero')
                if ':default-product' in node.attrib
            ),
            None,
        )
        if product_hero is None:
            raise ValueError('PDP product-hero payload was not found')

        product_data = json.loads(product_hero.get(':default-product'))
        for tab in self.find_tabs(product_data) or []:
            if not isinstance(tab, dict):
                continue
            field_name = self.field_names.get(tab.get('heading'))
            content = tab.get('content')
            if field_name and content:
                fields[field_name] = self.tool.HTML.clean_product_desc_str(content)

        self.tool.HTML.save_raw(
            html_text,
            Path(__file__).parent / 'ts' / '03-product-data' / f'{handle}_page.html',
        )
        return fields

    def fetch_product(self, url, category):
        handle = self.tool.URL.get_handle(url)
        try:
            product_response = self.tool.get(
                self.tool.URL.add_site(f'/products/{handle}.json'), timeout=20,
            )
            if product_response.status_code != 200:
                return []
            shopify_product = product_response.json().get('product')
            if not shopify_product:
                return []

            page_response = self.tool.get(url, timeout=20)
            if page_response.status_code != 200:
                return []
            shopify_product[self.tool.custom_key] = self.zdy_zd(handle, page_response.text)
        except Exception as exc:
            self.tool.print(f'[ERROR] Product custom-field parse failed: {url}: {exc}')
            return []

        parent = self.shopify_to_woocommerce(
            shopify_product, brand=self.tool.site, custom_categories=category,
        )
        return [parent, *self.create_variation_products(shopify_product, parent)]


if __name__ == '__main__':
    try:
        Pc(
            tool=Tool,
            input_path=input_file,
            output_path=output_file,
            output_ts_file=output_ts_file,
            fail_file=fail_file,
            catch_path=catch_path,
            index_path=index_path,
            skip_input_url_ls=skip_input_url_ls,
            skip_output_url_ls=skip_output_url_ls,
            fieldnames=fieldnames,
            ts_num=ts_num,
            max_threads=4,
        ).run()
    finally:
        Tool.close()
