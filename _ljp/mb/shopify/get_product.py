
from _ljp import HTML
from _ljp.mb.base import Get_Product as Step


class Get_Product(Step):
    def __init__(self,if_wp= False,**kwargs):
        super().__init__(**kwargs)
        self.if_wp = if_wp


    def get_woo_product(self,brand):
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

        return woo_product

    @staticmethod
    def has_options(shopify_product):
        return shopify_product.get('options') and any(
            len(option.get('values', [])) >= 1 for option in shopify_product.get('options', []))

    def get_attr(self,woo_product,shopify_product):
        Tool = self.tool
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

    def get_sample(self,woo_product,shopify_product,custom_categories=None):
        woo_product['Type'] = 'variable' if self.has_options(shopify_product) else 'simple'
        woo_product['SKU'] = shopify_product.get('handle', '')
        woo_product['Name'] = shopify_product.get('title', '')

        # 填写分类
        if custom_categories:
            if isinstance(custom_categories, list):
                categories = ','.join([cat.strip() for cat in custom_categories if cat.strip()])
            else:
                categories = custom_categories
        else:
            categories = shopify_product.get('productType', '')
        woo_product['Categories'] = categories



        return woo_product




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

    def mg_shopify_to_woocommerce(self,shopify_product,brand, custom_categories=None):
        Tool = self.tool
        woo_product = self.get_woo_product(brand)
        woo_product = self.get_sample( woo_product,shopify_product, custom_categories)

        woo_product['Description'] = shopify_product.get('description', '')
        woo_product['Description'] = self.tool.HTML.clean_product_desc_str(woo_product['Description'])


        # 填写是否有库存
        if woo_product['Type'] == 'simple':
            stock = shopify_product.get('availableForSale')
            woo_product['In stock?'] = 1 if stock else 0


        # 填写价格
        if shopify_product.get('variants', {}).get('nodes'):
            first_variant = shopify_product['variants']['nodes'][0]
            price = self.get_money_amount(first_variant.get('price'))
            compare_at_price = self.get_money_amount(first_variant.get('compareAtPrice'))
            woo_product['Regular price'] = price
            woo_product['Sale price'] = price
            if self.has_discount(compare_at_price, price):
                woo_product['Regular price'] = compare_at_price

        # 填写图片url
        image_urls = [image.get('url', '') for image in shopify_product.get('images', {}).get('nodes', [])]
        woo_product['Images'] = Tool.config.images_split.join(image_urls)

        woo_product = self.get_attr(woo_product,shopify_product)
        return woo_product

    def mg_create_variation_products(self, shopify_product, parent_product):
        """为Shopify产品创建变体产品"""
        Tool = self.tool
        variations = []
        if not self.has_options(shopify_product):
            return variations

        parent_product['Type'] = 'variable'
        parent_sku = parent_product['SKU']

        all_variant_images = []

        for variant in shopify_product.get('variants', {}).get('nodes', []):
            primary_image = variant.get('image', {}).get('url', '')

            mediaGallery = variant.get('mediaGallery', {})
            if mediaGallery:
                gallery_images = [
                    node.get('image', {}).get('url', '')
                    for node in mediaGallery.get('references', {}).get('nodes', [])
                    if node and node.get('image', {}).get('url')
                ]
            else:
                gallery_images = []
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
            if not variant_sku or variant_sku == parent_sku:
                # Storefront product variants may have no merchant SKU.  Keep
                # them distinct in later SKU-based pipeline steps by falling
                # back to Shopify's stable variant ID. A merchant SKU equal
                # to the parent handle also needs this fallback because the
                # parent and child must remain separate rows.
                variant_id = str(variant.get('id') or '').rstrip('/').split('/')[-1]
                variant_sku = f"{parent_sku}-{variant_id}" if variant_id else parent_sku
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
            for i, option in enumerate(variant.get('selectedOptions', [])):
                var[option['name']] = option['value']

            for i, option in enumerate(shopify_product.get('options', [])):
                option_key = option['name']
                if var.get(option_key):
                    variation[f'Attribute {i + 1} value(s)'] = var.get(option_key, '')

            primary_image = variant.get('image', {}).get('url', '')

            mediaGallery = variant.get('mediaGallery', {})

            gallery_images = [primary_image]
            if mediaGallery:
                ls = [
                node.get('image', {}).get('url', '')
                for node in variant.get('mediaGallery', {}).get('references', {}).get('nodes', [])
                if node.get('image', {}).get('url')
            ]
                gallery_images.extend(ls)


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

    def shopify_to_woocommerce(self,shopify_product,brand, custom_categories=None):
        Tool = self.tool


        woo_product = self.get_woo_product(brand)
        woo_product = self.get_sample(woo_product,shopify_product,custom_categories)
        woo_product['Description'] = shopify_product.get('body_html', '')
        woo_product['Description'] = self.tool.HTML.clean_product_desc_str(woo_product['Description'])

        # 填写是否有库存
        if woo_product['Type'] == 'simple':
            stock = shopify_product.get('variants')[0].get('available')
            woo_product['In stock?'] = 1 if stock else 0

        # 填写价格
        if shopify_product.get('variants'):
            first_variant = shopify_product['variants'][0]
            woo_product['Regular price'] = first_variant.get('price', '')
            woo_product['Sale price'] = first_variant.get('price', '')
            if first_variant.get('compare_at_price') and float(first_variant.get('compare_at_price', 0)) >= float(
                    first_variant.get('price', 0)):
                regular_price = first_variant.get('compare_at_price', '')
                woo_product['Regular price'] = regular_price
                woo_product['Sale price'] = regular_price

        # 填写图片url
        image_urls = [image.get('src', '') for image in shopify_product.get('images', [])]
        woo_product['Images'] = Tool.config.images_split.join(image_urls)

        woo_product = self.get_attr(woo_product,shopify_product)
        return woo_product

    def create_variation_products(self,shopify_product, parent_product):
        """为Shopify产品创建变体产品"""
        Tool = self.tool
        variations = []
        if not self.has_options(shopify_product):
            return variations

        parent_product['Type'] = 'variable'
        parent_sku = parent_product['SKU']

        # 添加变体图片
        variant_images = {}
        for image in shopify_product.get('images', []):
            image_url = image.get('src', '')
            for variant_id in image.get('variant_ids', []):
                if str(variant_id) not in variant_images:
                    variant_images[str(variant_id)] = []
                variant_images[str(variant_id)].append(image_url)

        for variant in shopify_product.get('variants', []):
            variation = parent_product.copy()

            variant_id = str(variant.get('id', ''))
            variation['Type'] = 'variation'
            variation['SKU'] = variant_id
            variation['Regular price'] = variant.get('price', '')
            variation['Sale price'] = variant.get('price', '')
            variation['Parent'] = parent_sku

            if variant.get('compare_at_price') and float(variant.get('compare_at_price', 0)) >= float(
                    variant.get('price', 0)):
                regular_price = variant.get('compare_at_price', '')
                variation['Regular price'] = regular_price
                variation['Sale price'] = regular_price

            variation['In stock?'] = '1' if variant.get('available', True) else '0'
            variation['Stock'] = str(variant.get('inventory_quantity', 1000))

            for i, option in enumerate(shopify_product.get('options', [])):
                option_key = f"option{i + 1}"
                if variant.get(option_key):
                    variation[f'Attribute {i + 1} value(s)'] = variant.get(option_key, '')

            if variant_id in variant_images and variant_images[variant_id]:
                variation['Images'] = ','.join(variant_images[variant_id])
            else:
                variation['Images'] = ''

            variation['Description'] = ''

            # 变体不需要自定义字段值，置空
            zdy_data = shopify_product.get(Tool.custom_key, {})
            if zdy_data:
                for key in zdy_data:
                    k = Tool.Product.build_custom_field_name(key)
                    variation[k] = ''
            variations.append(variation)

        return variations




__all__ = ['Get_Product']
