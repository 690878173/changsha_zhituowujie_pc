"""Collect Shopify products and authoritative King Linked Options relationships."""

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
    """Join split PDP variants only when the site's linked-options app confirms them."""

    linked_options_shop = 'markwins-wnw.myshopify.com'

    @staticmethod
    def text(value):
        return '' if value is None else str(value).strip()

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
