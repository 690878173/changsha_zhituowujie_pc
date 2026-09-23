"""Collect Shopify products, PDP custom fields, and linked-option relationships."""

import json

from lxml import html as lxml_html

from config import Tool
from _ljp.mb.shopify import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
fail_file = Tool.File.path_add_site('fail/4_linked_options_v1.json')
index_path = Tool.File.path_add_site('hc/4_linked_options_v1/index.json')
catch_path = Tool.File.path_add_site('hc/4_linked_options_v1/catch.json')

skip_input_url_ls = []
skip_output_url_ls = []
fieldnames = None
ts_num = None


class Pc(Get_Product):
    """Read PDP metafields and join split variants only when the app confirms them."""

    linked_options_shop = 'markwins-wnw.myshopify.com'

    @staticmethod
    def text(value):
        return '' if value is None else str(value).strip()

    def zdy_zd(self, html_text):
        """Extract verified product accordion fields, excluding the main Description."""
        tree = lxml_html.fromstring(html_text)
        fields = {}
        for accordion in tree.xpath(
            '//div[contains(concat(" ", normalize-space(@class), " "), '
            '" product-detail-accordion ")]'
        ):
            titles = accordion.xpath('.//details/summary[1]')
            bodies = accordion.xpath(
                './/details/div[contains(concat(" ", normalize-space(@class), " "), '
                '" cc-accordion-item__panel ")][1]'
            )
            if not titles or not bodies:
                continue
            title = self.text(' '.join(titles[0].xpath('.//text()')))
            if title not in {'Benefits', 'Ingredients', 'Directions'}:
                continue
            fields[title] = self.tool.HTML.clean_product_desc(bodies[0])
        return fields

    def linked_product_relationships(self, url, shopify_product):
        product_id = self.text(shopify_product.get('id'))
        if not product_id:
            raise ValueError(f'Missing Shopify product id for {url}')

        response = self.tool.get(
            self.tool.URL.add_site('/apps/king-linked-options/variants'),
            params={
                'shop': self.linked_options_shop,
                'productId': product_id,
            },
            timeout=20,
        )
        if response.status_code != 200:
            raise ValueError(f'Linked-options API returned {response.status_code} for {url}')

        payload = response.json()
        data = payload.get('data') or {}
        if not isinstance(data, dict) or data.get('enable') != 1:
            return [], {}, {}

        option_name = self.text(data.get('title'))
        products = data.get('products')
        if not option_name or not isinstance(products, list):
            raise ValueError(f'Invalid linked-options payload for {url}')

        handles = []
        source_options = {}
        target_options = {}
        for product in products:
            if not isinstance(product, dict):
                continue
            handle = self.text(product.get('handle'))
            value = self.text(product.get('name'))
            target_id = self.text(product.get('productId'))
            if not handle or not value:
                continue
            if handle not in handles:
                handles.append(handle)
            target_options[handle] = {option_name: value}
            if target_id == product_id:
                source_options[option_name] = value

        if len(handles) < 2 or not source_options:
            return [], {}, {}
        return handles, source_options, target_options

    def fetch_product(self, url, category):
        handle = self.tool.URL.get_handle(url)
        try:
            product_response = self.tool.get(
                self.tool.URL.add_site(f'/products/{handle}.json'),
                timeout=20,
            )
            if product_response.status_code != 200:
                return []
            shopify_product = product_response.json().get('product')
            if not shopify_product:
                return []

            page_response = self.tool.get(url, timeout=20)
            if page_response.status_code != 200:
                return []
            custom_fields = self.zdy_zd(page_response.text)
            relationships = self.linked_product_relationships(url, shopify_product)
        except Exception as exc:
            self.tool.print(f'[ERROR] Product request/parse failed: {url}: {exc}')
            return []

        shopify_product[self.tool.custom_key] = custom_fields
        parent = self.shopify_to_woocommerce(
            shopify_product,
            brand=self.tool.site,
            custom_categories=category,
        )
        handles, source_options, target_options = relationships
        parent['__source_handle'] = shopify_product.get('handle', handle)
        parent['__linked_handles'] = json.dumps(handles, ensure_ascii=False)
        parent['__linked_options'] = json.dumps(source_options, ensure_ascii=False)
        parent['__linked_target_options'] = json.dumps(target_options, ensure_ascii=False)
        return [parent, *self.create_variation_products(shopify_product, parent)]


if __name__ == '__main__':
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
    Tool.close()
