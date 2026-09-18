import time
from pathlib import Path

from lxml import etree

from config import Tool

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')

fail_file = Tool.File.path_add_site('fail/4.json')
# NOTE 缓存策略
index_path = Tool.File.path_add_site('hc/4/index.json')
catch_path = Tool.File.path_add_site('hc/4/catch.json')
catch_save_num = None

skip_input_url_ls = ['https://www.turtlebeach.com/products/roccat-kone-pro-mouse',
                     'https://www.turtlebeach.com/products/roccat-burst-pro-air-mouse',
                     'https://www.turtlebeach.com/products/stealth-700-gen-2-max-refurbished-headset',
                     'https://www.turtlebeach.com/products/victrix-pro-bfg-wireless-controller'

                     ]
skip_output_url_ls = []
# 默认使用fieldnames=None,自动写入自定义字段，需要控制字段写入由下游控制，这里保留所有字段
fieldnames = None

ts_num = None
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Accept": "application/json"
}
cookies = {
    "localization": "US",
    "cart_currency": "USD",
    "_shopify_y": "dabb39cc-bc89-497c-b340-31b2ede021e3",
    "_shopify_analytics": ":AZp2O1QkAAEAHztC69G-yFNChK1vfflUWudV0AhpFiNR6FOoG0JYh1QIeFwE0AplJXKB:",
    "__kla_id": "eyJjaWQiOiJZelJsTnpnNFltSXRaV1ZqWlMwMFkyUTNMV0ppTW1FdFkyUTJNalUxTVdFNE5XWTMifQ==",
    "_dcid": "dcid.1.1762920201737.993685852",
    "_fbp": "fb.1.1762920201752.1616510929",
    "_gtmeec": "e30%3D",
    "_ga": "GA1.1.360526338.1762920202",
    "FPID": "FPID2.2.gkxOzZt5mIdu%2BjM%2FENk%2BINUWEC8WFAK8VJr7qv9DiMI%3D.1762920202",
    "FPAU": "1.2.1363690192.1762920202",
    "_clck": "8r5450%5E2%5Eg13%5E0%5E2142",
    "FPLC": "LgBR2ZulVErPIfYUSJlzshz28PHJYpcZjaf0ttgQ%2BOKvoX%2FTytpvBT1gw9f8w3Skoaoji%2FPT80R%2BxMChx7HVjW9Jmb0vQwpLwbP7lGJTdH2cpIAbSo3WEf43r4%2BDBA%3D%3D",
    "_shg_session_id": "ee3abf4f-7d71-4f24-b659-5c90de46503d",
    "_shg_user_id": "b36c7c32-f288-42a9-b521-223b4178e2b3",
    "wishlist_id": "165828310s5ibxs5m1i",
    "bookmarkeditems": "{\"items\":[]}",
    "wishlist_customer_id": "0",
    "lantern": "34e4017a-dcd0-44ea-86cc-510f559707fd",
    "_ks_scriptVersionChecked": "true",
    "_ks_userCountryUnit": "0",
    "_ks_countryCodeFromIP": "US",
    "_shopify_essential": ":AZp2O1QXAAEAvyFsaVJ70tJgji5ZeWCZ_YjgxwRXjGxAB3b5N-WHhSnud69tQW0MrpYjCka6b3GqbBhR9Uz4BhF9KODipC_2NFZRmCTQFTmhAMAjGv-jGy4tjy0FmTHMickaBcTQYB9gyNeGMX1T3ZL2JQ1P2sZLYPZwXL-juXGHSYiFqr2Gmc3jlKNMgPuEzv0pxSUVdolOYxCzcSwmJ_JEgKtrg_dwrLM_tp1SdVStXGVGDxfT27-4a1Fn6pKOttW0ZLW4JluB7XDeVv2VuUk-0l_ZIXlIrOu1450YtgeUvAjU3fGxv8SJbsptfgcU-GQ7NmT1Nravs3DmiiAUo2_zvYu9sk8dE3QuA-QodGbtyvFwsh4qzVoX5oLuEgUKhsFrxGP3Le-BVpm8PXsJjtIp7D18HUY:",
    "_clsk": "z0wknv%5E1763344068385%5E8%5E1%5Es.clarity.ms%2Fcollect",
    "_shopify_s": "73b24c0d-a8d4-4416-9886-da6ff48b97ce",
    "_uetsid": "94037020c35611f0b6b471d9a3ac75ef",
    "_uetvid": "8406dea0bf7c11f089889339b77b1953",
    "FPGSID": "1.1763343715.1763344093.G-QSD4N22KEF.mFsL74_ybyYhfff-E83nSQ",
    "_ga_QSD4N22KEF": "GS2.1.s1763343714$o2$g1$t1763344100$j51$l0$h694839178",
    "kiwi-sizing-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI4YTliMTk0ZC1iZmY3LTQ3OTktYjMwYS01Zjc1ZWZjMGVjMjIiLCJpYXQiOjE3NjMzNDQxNDYsImV4cCI6MTc2MzM0Nzc0Nn0.6kThd-lf6VF4L_1otBoH8nlTuH0z9Nw5nF0akbIs4UU",
    "keep_alive": "eyJ2IjoyLCJ0cyI6MTc2MzM0NDE5NDYzOSwiZW52Ijp7IndkIjowLCJ1YSI6MSwiY3YiOjEsImJyIjoxfSwiYmh2Ijp7Im1hIjo2NCwiY2EiOjAsImthIjowLCJzYSI6Mywia2JhIjowLCJ0YSI6MCwidCI6MTEyLCJubSI6MSwibXMiOjAuNjMsIm1qIjowLjMyLCJtc3AiOjAuMzUsInZjIjowLCJjcCI6MCwicmMiOjAsImtqIjowLCJraSI6MCwic3MiOjAuMDEsInNqIjowLjAxLCJzc20iOjEsInNwIjoxLCJ0cyI6MCwidGoiOjAsInRwIjowLCJ0c20iOjB9LCJzZXMiOnsicCI6NSwicyI6MTc2MzM0MzcwNDY0MSwiZCI6NDgzfX0%3D"
}

if_wp = False
time_sleep = 7
html_dir = Path(__file__).resolve().parent / 'html'
json_dir = Path(__file__).resolve().parent / 'json'

from _ljp.mb.shopify import Get_Product


class Pc(Get_Product):

    @staticmethod
    def save_debug_files(handle, html, api_json):
        html_dir.mkdir(parents=True, exist_ok=True)
        json_dir.mkdir(parents=True, exist_ok=True)

        (html_dir / f'{handle}.html').write_text(html, encoding='utf-8')
        (json_dir / f'{handle}.json').write_text(api_json, encoding='utf-8')

    def zdy_zd(self, url, html_text=None):
        """Extract the product accordion fields that are not in Storefront GraphQL."""
        if html_text is None:
            response = self.tool.get(url)
            if response.status_code != 200:
                return {}
            html_text = response.text

        tree = etree.HTML(html_text)
        if tree is None:
            return {}

        fields = {}
        wanted = {'Technical Specifications', 'Compatibility'}
        for section in tree.xpath('//div[@role="presentation" and @data-accordion-item]'):
            title = ' '.join(
                text.strip()
                for text in section.xpath('.//button//*[normalize-space(text())]/text()')
                if text.strip()
            )
            if title not in wanted:
                continue
            content = section.xpath(
                './/div[contains(concat(" ", normalize-space(@class), " "), " _0Trcb ")]'
            )
            if content:
                value = self.tool.HTML.clean_product_desc(content[0])
                if value:
                    fields[title] = value
        return fields

    def fetch_product(self, url, category) -> list:
        Tool = self.tool
        requested_handle = Tool.URL.get_handle(url)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "X-Shopify-Storefront-Access-Token": "ef1b9f624c705ea7623f3c2b31924b44"
        }
        query = """
            query ProductByHandle($handle: String!) {
              product(handle: $handle) {
                id
                title
                description
                handle
                availableForSale
                productType
                vendor
                tags
                updatedAt
                seo {
                  title
                  description
                }
                featuredImage {
                  url
                  altText
                  width
                  height
                }
                priceRange {
                  minVariantPrice {
                    amount
                    currencyCode
                  }
                  maxVariantPrice {
                    amount
                    currencyCode
                  }
                }

                metafields(
                    identifiers: [
                      {namespace: "custom", key: "ingredients_description"},
                      {namespace: "custom", key: "product_ingredients"}
                    ]
                  ) {
                    key
                    namespace
                    type
                    value
                  }

                options {
                  id
                  name
                  values
                }
                images(first: 100) {
                  nodes {
                    url
                    altText
                    width
                    height
                  }
                }
                variants(first: 100) {
                  nodes {
                    id
                    sku
                    title
                    availableForSale
                    selectedOptions {
                      name
                      value
                    }
                    price {
                      amount
                      currencyCode
                    }
                    compareAtPrice {
                      amount
                      currencyCode
                    }
                    image {
                      url
                      altText
                      width
                      height
                    }
                    mediaGallery: metafield(namespace: "custom", key: "media_gallery") {
                      references(first: 100) {
                        nodes {
                          ... on MediaImage {
                            image {
                              url
                              altText
                              width
                              height
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """

        payload = {
            "query": query,
            "variables": {
                "handle": requested_handle
            }
        }
        retries = 3
        delay = 2
        request_url = 'https://turtle-beach-usa.myshopify.com/api/2023-07/graphql.json'

        try:
            page_response = Tool.get(url)
            if page_response.status_code == 404:
                return []
            if not 200 <= page_response.status_code < 400:
                raise RuntimeError(f'页面请求状态码: {page_response.status_code}')

            # 部分旧商品链接会重定向；接口必须使用最终页面的产品 handle。
            page_url = page_response.url
            handle = Tool.URL.get_handle(page_url)
            payload['variables']['handle'] = handle
            r = Tool.post(request_url, headers=headers, json=payload, timeout=30)

            if r.status_code == 404:
                return []
            self.save_debug_files(requested_handle, page_response.text, r.text)
            data = r.json()['data']

            #TODO 使用原url还是   p_url.replace('.json', '')

            zdy_data = self.zdy_zd(page_url, page_response.text)

            time.sleep(time_sleep)

            shopify_product = data.get("product")

            shopify_product[Tool.custom_key] = zdy_data
            shopify_product['__url'] = page_url

        except Exception as e:
            Tool.print(f'[ERROR] 接口请求失败:{url} 未知异常: {e}')
            return []

        woo_product = self.shopify_to_woocommerce(
            shopify_product,
            brand=Tool.site,
            custom_categories=category
        )
        _products = [woo_product]
        variations = self.create_variation_products(shopify_product, woo_product)

        if variations:
            _products.extend(variations)


        return _products


    def create_variation_products(self,shopify_product, parent_product):
        """为Shopify产品创建变体产品"""
        Tool = self.tool
        variations = []
        has_options = shopify_product.get('options') and any(
            len(option.get('values', [])) >= 1 for option in shopify_product.get('options', []))

        if not has_options:
            return variations

        parent_product['Type'] = 'variable'
        parent_sku = parent_product['SKU']

        # 父产品要展示整个变体系列的图库（包括不同颜色/款式），而不是只展示
        # product.images 中的默认产品图片。
        all_variant_images = []
        for variant in shopify_product.get('variants', {}).get('nodes', []):
            primary_image = variant.get('image', {}).get('url', '')
            gallery_images = [
                node.get('image', {}).get('url', '')
                for node in variant.get('mediaGallery', {}).get('references', {}).get('nodes', [])
                if node.get('image', {}).get('url')
            ]
            all_variant_images.extend([primary_image, *gallery_images])

        product_images = [
            image.get('url', '')
            for image in shopify_product.get('images', {}).get('nodes', [])
            if image.get('url')
        ]
        parent_images = list(dict.fromkeys(
            image for image in [*product_images, *all_variant_images] if image
        ))
        if parent_images:
            parent_product['Images'] = Tool.config.images_split.join(parent_images)

        for variant in shopify_product.get('variants', {}).get('nodes', []):
            variation = parent_product.copy()

            variant_sku = (variant.get('sku') or '').strip()
            price = self.get_money_amount(variant.get('price'))
            compare_at_price = self.get_money_amount(variant.get('compareAtPrice'))
            variation['Type'] = 'variation'
            variation['SKU'] = variant_sku
            variation['Regular price'] = price
            variation['Sale price'] = price
            variation['Parent'] = parent_sku

            if self.has_discount(compare_at_price, price):
                variation['Regular price'] = compare_at_price

            variation['In stock?'] = '1' if variant.get('availableForSale', True) else '0'
            variation['Stock'] = str(variant.get('inventory_quantity', 1000))

            var = {}
            for i ,option in enumerate(variant.get('selectedOptions', [])):
                var[option['name']] = option['value']

            for i, option in enumerate(shopify_product.get('options', [])):
                option_key = option['name']
                if var.get(option_key):
                    variation[f'Attribute {i + 1} value(s)'] = var.get(option_key, '')

            primary_image = variant.get('image', {}).get('url', '')
            gallery_images = [primary_image] + [
                node.get('image', {}).get('url', '')
                for node in variant.get('mediaGallery', {}).get('references', {}).get('nodes', [])
                if node.get('image', {}).get('url')
            ]
            variation['Images'] = Tool.config.images_split.join(
                dict.fromkeys(image for image in gallery_images if image)
            )

            variation['Description'] = ''

            # 变体不需要自定义字段值，置空
            zdy_data = shopify_product.get(Tool.custom_key, {})
            if zdy_data:
                for key in zdy_data:
                    k = Tool.Product.build_custom_field_name(key)
                    variation[k] = ''
            variations.append(variation)

        return variations

    @staticmethod
    def get_money_amount(value):
        if isinstance(value, dict):
            return value.get('amount', '')
        return value if value is not None else ''

    @staticmethod
    def has_discount(compare_at_price, price):
        try:
            return bool(compare_at_price) and float(compare_at_price) >= float(price)
        except (TypeError, ValueError):
            return False



    def shopify_to_woocommerce(self,shopify_product,brand, custom_categories=None):
        Tool = self.tool
        if self.if_wp:
            woo_product = {
                'ID': '', 'Type': '', 'SKU': '', 'Name': '', 'Published': '1', 'Is featured?': '0',
                'Visibility in catalog': 'visible', 'Short description': '', 'Description': '',
                'Date sale price starts': '', 'Date sale price ends': '', 'Tax status': 'taxable',
                'Tax class': '', 'In stock?': '1', 'Stock': '1000', 'Backorders allowed?': '1',
                'Sold individually?': '0', 'Weight (lbs)': '', 'Length (in)': '', 'Width (in)': '',
                'Height (in)': '', 'Allow customer reviews?': '1', 'Purchase note': '',
                'Sale price': '', 'Regular price': '', 'Categories': '', 'Tags': '',
                'Shipping class': '', 'Images': '', 'Download limit': '', 'Download expiry days': '',
                'Parent': '', 'Grouped products': '', 'Upsells': '', 'Cross-sells': '',
                'External URL': '', 'Button text': '', 'Position': '0', 'Meta: _wpcom_is_markdown': '',
                'Download 1 name': '', 'Download 1 URL': '', 'Download 2 name': '',
                'Download 2 URL': '', 'is_upload': 0, 'brand': f'{brand}'
            }
        else:
            woo_product = {
                'ID': '', 'Type': '', 'SKU': '', 'Name': '', 'Description': '', 'Stock': '1000',
                'Sale price': '', 'Regular price': '', 'Categories': '', 'Tags': '',
                'Images': '', 'Parent': '', 'is_upload': 0, 'brand': f'{brand}'
            }

        has_options = shopify_product.get('options') and any(
            len(option.get('values', [])) >= 1 for option in shopify_product.get('options', []))

        woo_product['Type'] = 'variable' if has_options else 'simple'
        woo_product['SKU'] = shopify_product.get('handle', '')
        woo_product['Description'] = shopify_product.get('description', '')
        woo_product['Description'] = self.tool.HTML.clean_product_desc_str(woo_product['Description'])
        woo_product['Name'] = shopify_product.get('title', '')

        # 填写是否有库存
        if woo_product['Type'] == 'simple':
            stock = shopify_product.get('availableForSale')
            woo_product['In stock?'] = 1 if stock else 0

        # 填写分类
        if custom_categories:
            if isinstance(custom_categories, list):
                categories = ','.join([cat.strip() for cat in custom_categories if cat.strip()])
            else:
                categories = custom_categories
        else:
            categories = shopify_product.get('productType', '')
        woo_product['Categories'] = categories

        # 填写价格
        if shopify_product.get('variants',{}).get('nodes'):
            first_variant = shopify_product['variants']['nodes'][0]
            price = self.get_money_amount(first_variant.get('price'))
            compare_at_price = self.get_money_amount(first_variant.get('compareAtPrice'))
            woo_product['Regular price'] = price
            woo_product['Sale price'] = price
            if self.has_discount(compare_at_price, price):
                woo_product['Regular price'] = compare_at_price

        # 填写图片url
        image_urls = [image.get('url', '') for image in shopify_product.get('images', {}).get('nodes',[])]
        woo_product['Images'] = Tool.config.images_split.join(image_urls)

        # 填写属性
        if shopify_product.get('options'):
            for i, option in enumerate(shopify_product.get('options', [])):
                attr_num = i + 1
                woo_product[f'Attribute {attr_num} name'] = option.get('name', '')
                woo_product[f'Attribute {attr_num} value(s)'] = ','.join(option.get('values', []))
                woo_product[f'Attribute {attr_num} visible'] = 0
                woo_product[f'Attribute {attr_num} global'] = 1
        # 添加自定义字段到父类
        zdy_data = shopify_product.get(Tool.custom_key, {})
        if zdy_data:
            for key, value in zdy_data.items():
                k = Tool.Product.build_custom_field_name(key)
                woo_product[k] = value
        return woo_product










if __name__ == '__main__':
    pc = Pc(
        tool=Tool,
        input_path=input_file,
        output_path=output_file,
        fail_file=fail_file,
        catch_path=catch_path,
        index_path=index_path,
        output_ts_file=output_ts_file,
        ts_num=ts_num,
        catch_save_num = catch_save_num,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        fieldnames=fieldnames,
        max_threads=10,
        if_wp=if_wp
    )

    pc.run()
