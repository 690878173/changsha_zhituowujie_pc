import time

from lxml import html as lxml_html

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
dump_html = False
flush = False


class Pc(Get_Product):
    accordion_xpath = (
        '//div[contains(@class, "product-accordion") and '
        './/div[contains(@class, "product-accordion__panel") or '
        'contains(@class, "product-accordion-grid__panel")]]'
    )
    skip_fields = frozenset({'Shipping and Returns'})

    @staticmethod
    def node_text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def field_name(label):
        return ' '.join(label.replace('&', 'and').split())

    def storefront_settings(self):
        return {
            "storefront_token": "6beb9ad94eb8033605576c7a2f498cb6",
            "store_domain": "www.chubbiesshorts.com",
            "api_version": "unstable",
            "country": "US",
            "language": "EN",
            "request_delay": 0.5,
        }

    def zdy_zd(self, url, html_text=None):
        """返回商品详情折叠面板，排除通用的 Shipping and Returns。"""
        if not html_text:
            return {}
        fields = {}
        tree = lxml_html.fromstring(html_text)
        for accordion in tree.xpath(self.accordion_xpath):
            titles = accordion.xpath('.//div[contains(@class, "buttonTitle")][1]')
            if not titles:
                continue
            name = self.field_name(self.node_text(titles[0]))
            if not name or name in self.skip_fields or name in fields:
                continue
            panels = accordion.xpath(
                './/div[contains(@class, "product-accordion__panel") or '
                'contains(@class, "product-accordion-grid__panel")][1]'
            )
            if not panels:
                continue
            value = self.tool.HTML.clean_product_desc(panels[0])
            if value:
                fields[name] = value
        return fields

    @staticmethod
    def connection_nodes(connection):
        if not isinstance(connection, dict):
            return []
        nodes = connection.get('nodes')
        return [node for node in nodes if isinstance(node, dict)] if isinstance(nodes, list) else []

    @staticmethod
    def image_url(image):
        return image.get('url', '') if isinstance(image, dict) else ''

    def product_options(self, product):
        options = product.get('options') if isinstance(product, dict) else []
        return [option for option in options if isinstance(option, dict)] if isinstance(options, list) else []

    @staticmethod
    def unique_urls(urls):
        return list(dict.fromkeys(url for url in urls if isinstance(url, str) and url))

    def variant_images(self, variant):
        if not isinstance(variant, dict):
            return []
        images = [self.image_url(variant.get('image'))]
        gallery = variant.get('mediaGallery')
        references = gallery.get('references') if isinstance(gallery, dict) else {}
        for node in self.connection_nodes(references):
            images.append(self.image_url(node.get('image')))
        return self.unique_urls(images)

    def mg_shopify_to_woocommerce(self, shopify_product, brand, custom_categories=None):
        """Convert Chubbies Storefront product nodes while tolerating nullable media."""
        product = shopify_product if isinstance(shopify_product, dict) else {}
        variants = self.connection_nodes(product.get('variants'))
        options = self.product_options(product)
        is_variable = len(variants) > 1
        woo_product = self.get_woo_product(brand)

        woo_product['Type'] = 'variable' if is_variable else 'simple'
        woo_product['SKU'] = product.get('handle', '')
        woo_product['Name'] = product.get('title', '')
        woo_product['Categories'] = custom_categories or product.get('productType', '')
        woo_product['Description'] = self.tool.HTML.clean_product_desc_str(product.get('description', ''))

        first_variant = variants[0] if variants else {}
        price = self.get_money_amount(first_variant.get('price'))
        compare_at_price = self.get_money_amount(first_variant.get('compareAtPrice'))
        woo_product['Regular price'] = compare_at_price if self.has_discount(compare_at_price, price) else price
        woo_product['Sale price'] = price
        if not is_variable:
            woo_product['In stock?'] = '1' if first_variant.get('availableForSale', product.get('availableForSale')) else '0'

        product_images = [self.image_url(image) for image in self.connection_nodes(product.get('images'))]
        if not product_images:
            product_images.append(self.image_url(product.get('featuredImage')))
        woo_product['Images'] = self.tool.config.images_split.join(self.unique_urls(product_images))

        if is_variable:
            for index, option in enumerate(options, start=1):
                values = [value for value in option.get('values', []) if isinstance(value, str) and value]
                if not values:
                    continue
                woo_product[f'Attribute {index} name'] = option.get('name', '')
                woo_product[f'Attribute {index} value(s)'] = ','.join(values)
                woo_product[f'Attribute {index} visible'] = 0
                woo_product[f'Attribute {index} global'] = 1

        for key, value in (product.get(self.tool.custom_key) or {}).items():
            woo_product[self.tool.Product.build_custom_field_name(key)] = value
        return woo_product

    def mg_create_variation_products(self, shopify_product, parent_product):
        """Create only real Chubbies variation rows and retain nullable-media fallbacks."""
        product = shopify_product if isinstance(shopify_product, dict) else {}
        variants = self.connection_nodes(product.get('variants'))
        if len(variants) <= 1:
            return []

        parent_product['Type'] = 'variable'
        parent_sku = parent_product.get('SKU', '') or product.get('handle', '')
        product_images = [self.image_url(image) for image in self.connection_nodes(product.get('images'))]
        if not product_images:
            product_images.append(self.image_url(product.get('featuredImage')))
        variant_image_urls = [image for variant in variants for image in self.variant_images(variant)]
        parent_images = self.unique_urls([*product_images, *variant_image_urls])
        parent_product['Images'] = self.tool.config.images_split.join(parent_images)

        options = self.product_options(product)
        custom_keys = (product.get(self.tool.custom_key) or {}).keys()
        variations = []
        for variant in variants:
            variation = parent_product.copy()
            variant_id = str(variant.get('id') or '').rstrip('/').split('/')[-1]
            sku = str(variant.get('sku') or '').strip()
            if not sku or sku == parent_sku:
                sku = f'{parent_sku}-{variant_id}' if variant_id else parent_sku
            price = self.get_money_amount(variant.get('price'))
            compare_at_price = self.get_money_amount(variant.get('compareAtPrice'))

            variation['Type'] = 'variation'
            variation['SKU'] = sku
            variation['Parent'] = parent_sku
            variation['Regular price'] = compare_at_price if self.has_discount(compare_at_price, price) else price
            variation['Sale price'] = price
            variation['In stock?'] = '1' if variant.get('availableForSale') else '0'
            variation['Stock'] = '1000'
            variation['Images'] = self.tool.config.images_split.join(self.variant_images(variant))
            variation['Description'] = ''

            selections = {
                item.get('name'): item.get('value')
                for item in (variant.get('selectedOptions') or [])
                if isinstance(item, dict) and item.get('name') and item.get('value')
            }
            for index, option in enumerate(options, start=1):
                value = selections.get(option.get('name'))
                if value:
                    variation[f'Attribute {index} value(s)'] = value
            for key in custom_keys:
                variation[self.tool.Product.build_custom_field_name(key)] = ''
            variations.append(variation)
        return variations

    def fetch_product(self, url, category):
        """Use Storefront data even when a legacy PDP route responds with 404."""
        try:
            handle = self.tool.URL.get_handle(url)
            product = self.storefront.graphql(self.product_query(), {'handle': handle}).get('product')
            if not product:
                return []

            page_response = self.tool.get(url)
            is_live_page = 200 <= getattr(page_response, 'status_code', 0) < 400
            page_url = getattr(page_response, 'url', None) or url
            extra = self.zdy_zd(page_url, page_response.text) if is_live_page else {}
            product[self.tool.custom_key] = extra or {}
            product['__url'] = url
            if self.request_delay:
                time.sleep(self.request_delay)

            parent = self.mg_shopify_to_woocommerce(product, self.tool.site, category)
            return [parent, *self.mg_create_variation_products(product, parent)]
        except Exception as exc:
            self.tool.print(f'[ERROR] 接口请求失败:{url} 未知异常: {exc}')
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
        flush=flush,
        catch_save_num=catch_save_num,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        fieldnames=fieldnames,
        max_threads=10,
        if_wp=if_wp,
    ).run()
    Tool.close()
