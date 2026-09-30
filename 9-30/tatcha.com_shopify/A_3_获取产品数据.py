"""Collect a small verified Tatcha Shopify product sample with Ingredients."""

from pathlib import Path

from lxml import html as lxml_html

from config import Tool
from _ljp.mb.shopify import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
fail_file = Tool.File.path_add_site('fail/4.json')
index_path = Tool.File.path_add_site('hc/4/index.json')
catch_path = Tool.File.path_add_site('hc/4/catch.json')

# Keep the first verification run deliberately small. Set to None only after review.
ts_num = None
flush = False
catch_save_num = None
skip_input_url_ls = []
skip_output_url_ls = []
fieldnames = None


class TatchaProductCollector(Get_Product):
    """Add the public product-page Ingredients drawer to standard Shopify rows."""

    @staticmethod
    def snapshot_stem(handle, parent_sku):
        return f'{handle}_{parent_sku or handle}'

    def save_product_json(self, payload, handle, parent_sku):
        self.tool.File.save_json(
            payload,
            f'ts/03-product/{self.snapshot_stem(handle, parent_sku)}_product.json',
        )

    def save_product_page(self, page_html, handle, parent_sku):
        snapshot_path = (
            Path(__file__).parent
            / 'ts'
            / '03-product'
            / f'{self.snapshot_stem(handle, parent_sku)}_page.html'
        )
        self.tool.HTML.save_raw(page_html, snapshot_path)

    @staticmethod
    def is_ingredients_heading(node):
        return ' '.join(node.xpath('.//text()')).strip().lower() == 'ingredients'

    def extract_ingredients(self, page_html):
        tree = lxml_html.fromstring(page_html)
        for drawer in tree.xpath('//x-drawer'):
            headings = drawer.xpath('./*[self::span or self::h2 or self::h3 or self::h4]')
            if not any(self.is_ingredients_heading(heading) for heading in headings):
                continue
            content = drawer.xpath('./div[contains(concat(" ", normalize-space(@class), " "), " prose ")]')
            if not content:
                content = drawer.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " metafield-rich_text_field ")]')
            if content:
                return self.tool.HTML.clean_product_desc(content[0])
        return ''

    def extract_description(self, page_html):
        tree = lxml_html.fromstring(page_html)
        nodes = tree.xpath(
            '//section[contains(@class, "main-product")]'
            '//*[@data-block-type="secondary-name"]'
            '//div[contains(concat(" ", normalize-space(@class), " "), " prose ")]'
        )
        if nodes:
            return self.tool.HTML.clean_product_desc(nodes[0])
        return ''

    def custom_fields(self, page_html):
        return {'Ingredients': self.extract_ingredients(page_html)}

    def fetch_product(self, url, category):
        handle = self.tool.URL.get_handle(url)
        try:
            product_response = self.tool.get(
                self.tool.URL.add_site(f'/products/{handle}.json'),
                timeout=20,
            )
            if product_response.status_code != 200:
                return []
            product_payload = product_response.json()
            shopify_product = product_payload.get('product')
            if not shopify_product:
                return []

            parent_sku = shopify_product.get('handle') or handle
            self.save_product_json(product_payload, handle, parent_sku)

            fields = {'Ingredients': ''}
            page_response = self.tool.get(url, timeout=20)
            if page_response.status_code == 200 and page_response.text:
                self.save_product_page(page_response.text, handle, parent_sku)
                fields = self.custom_fields(page_response.text)
                description = self.extract_description(page_response.text)
                if description:
                    shopify_product['body_html'] = description
            else:
                self.tool.print(
                    f'[WARN] Product page unavailable for Ingredients: {url} '
                    f'(status {page_response.status_code})',
                    color='yellow',
                )

            shopify_product[self.tool.custom_key] = fields
            parent = self.shopify_to_woocommerce(
                shopify_product,
                brand=self.tool.site,
                custom_categories=category,
            )
            return [parent, *self.create_variation_products(shopify_product, parent)]
        except Exception as exc:
            self.tool.print(f'[ERROR] Product request/parse failed: {url}: {exc}')
            return []


if __name__ == '__main__':
    try:
        TatchaProductCollector(
            tool=Tool,
            input_path=input_file,
            output_path=output_file,
            output_ts_file=output_ts_file,
            fail_file=fail_file,
            catch_path=catch_path,
            index_path=index_path,
            ts_num=ts_num,
            flush=flush,
            catch_save_num=catch_save_num,
            skip_input_url_ls=skip_input_url_ls,
            skip_output_url_ls=skip_output_url_ls,
            fieldnames=fieldnames,
            max_threads=2,
        ).run()
    finally:
        Tool.close()
