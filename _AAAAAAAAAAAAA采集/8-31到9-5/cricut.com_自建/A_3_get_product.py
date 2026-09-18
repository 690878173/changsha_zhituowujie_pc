import json
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from lxml import etree

from config import Tool
from _ljp.mb.zj import Get_Product


# 文件路径配置
input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
fail_file = Tool.File.path_add_site('data/fail.json')
catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

# 测试数据条数 (None = 全部抓取)
ts_num = None
catch_save_num = None
skip_input_url_ls = []
skip_output_url_ls = []

headers = None
cookies = None
flush = False
fieldnames = None
max_threads = 2

VARIATION_ENDPOINT_MARKER = '/on/demandware.store/'


class Pc(Get_Product):
    def fetch_product(self, url, category):
        """请求 Cricut 商品页及其 Product-Variation JSON。"""
        response = Tool.get(url, headers=headers, cookies=cookies)
        if response.status_code != 200 or not response.text:
            raise RuntimeError(f'商品页面请求失败（HTTP {response.status_code}）：{url}')

        page_html = response.text
        html = etree.HTML(page_html)
        if html is None:
            raise ValueError(f'商品页面不是有效 HTML：{url}')

        variation_urls = _T.extract_variation_urls(html)
        variants = []
        for variation_url in variation_urls:
            request_headers = dict(headers or {})
            request_headers.update({'X-Requested-With': 'XMLHttpRequest', 'Referer': url})
            variation_response = Tool.get(
                variation_url, headers=request_headers, cookies=cookies
            )
            if variation_response.status_code != 200 or not variation_response.text:
                Tool.print(
                    f'变体请求失败（HTTP {variation_response.status_code}）：{variation_url}',
                    color='yellow',
                )
                continue
            try:
                payload = variation_response.json()
                if isinstance(payload, dict) and isinstance(payload.get('product'), dict):
                    variants.append(payload)
            except (TypeError, ValueError) as error:
                Tool.print(f'变体 JSON 解析失败：{error}；{variation_url}', color='yellow')

        return _T(url, category, page_html, variants, variation_urls).run()


class _T:
    """将 Cricut 商品页和变体接口响应转换为标准产品行。"""

    DISPLAY_FIELDS = ('Features', 'Included')

    def __init__(self, url, category, page_html, variants=None, variation_urls=None):
        self.url = url
        self.category = category
        self.page_html = page_html
        self.html = etree.HTML(page_html)
        self.variants = variants or []
        self.variation_urls = variation_urls or []

    @staticmethod
    def _text(value):
        return ' '.join(str(value or '').split()).strip()

    @staticmethod
    def _product_json(html):
        for script in html.xpath('//script[@type="application/ld+json"]'):
            try:
                data = json.loads(''.join(script.itertext()))
            except (TypeError, ValueError):
                continue
            if isinstance(data, dict) and data.get('@type') == 'Product':
                return data
        return {}

    @staticmethod
    def _section_fields(html):
        if html is None:
            return {}
        fields = {}
        sections = html.xpath(
            '//div[contains(@class, "product-collapse")]'
            '[.//span[contains(@class, "product-collapse__title")]]'
        )
        for section in sections:
            title = _T._text(''.join(section.xpath(
                './/span[contains(@class, "product-collapse__title")]//text()'
            )))
            if title not in _T.DISPLAY_FIELDS:
                continue
            content = section.xpath(
                './/div[contains(@class, "product-collapse__content")][@id][1]'
            )
            if not content:
                continue
            value = ''.join(
                etree.tostring(child, encoding='unicode', method='html')
                for child in content[0]
            ).strip()
            if value:
                fields[title] = value
        return fields

    @staticmethod
    def _normalise_html(value):
        return ''.join((value or '').split())

    @classmethod
    def _common_fields(cls, page_html, variants):
        field_maps = [cls._section_fields(etree.HTML(page_html))]
        for payload in variants:
            panel = payload.get('fullBuyPanelHtml')
            if panel:
                field_maps.append(cls._section_fields(etree.HTML(panel)))
        common = {}
        for name in cls.DISPLAY_FIELDS:
            values = [fields.get(name) for fields in field_maps]
            if values[0] and all(
                value and cls._normalise_html(value) == cls._normalise_html(values[0])
                for value in values[1:]
            ):
                common[name] = values[0]
        return common

    @staticmethod
    def _price(product):
        price = product.get('price') or {}
        if not isinstance(price, dict):
            return None
        # Cricut exposes the undiscounted amount under list and the current
        # promotion under sales. Export the original amount when available.
        listed = price.get('list')
        if isinstance(listed, dict) and isinstance(listed.get('value'), (int, float)):
            return listed['value']
        sales = price.get('sales')
        value = sales.get('value') if isinstance(sales, dict) else None
        return value if isinstance(value, (int, float)) else None

    @staticmethod
    def _images(product, fallback=None):
        images = product.get('images') if isinstance(product, dict) else None
        if isinstance(images, dict):
            images = images.get('large') or images.get('thumbnail') or []
            result = [item.get('url') for item in images if isinstance(item, dict)]
            result = [item for item in result if item]
            if result:
                return result
        return list(fallback or [])

    @staticmethod
    def _attributes(product):
        attributes = {}
        for item in product.get('variationAttributes') or []:
            if not isinstance(item, dict):
                continue
            name = _T._text(item.get('displayName') or item.get('attributeId'))
            value = _T._text(item.get('displayValue'))
            if name and value:
                attributes[name] = value
        return attributes

    @staticmethod
    def _variant_sku(payload):
        product = payload.get('product') or {}
        sku = product.get('id')
        if sku:
            return str(sku)
        panel = etree.HTML(payload.get('fullBuyPanelHtml') or '')
        value = panel.xpath('string((//*[contains(@class, "product-id")])[1])')
        return _T._text(value) or None

    @staticmethod
    def _stock(product):
        return 1 if product.get('available') or product.get('isInStock') else 0

    @staticmethod
    def _fallback_product(html):
        data = _T._product_json(html)
        if data:
            offers = data.get('offers') or {}
            availability = str(offers.get('availability') or '')
            price = None
            # JSON-LD marks the original price as StrikethroughPrice.
            for spec in offers.get('priceSpecification') or []:
                if isinstance(spec, dict) and spec.get('priceType'):
                    if 'StrikethroughPrice' in str(spec.get('priceType')):
                        price = spec.get('price')
                        break
            if price is None:
                for spec in offers.get('priceSpecification') or []:
                    if isinstance(spec, dict) and spec.get('priceType') is None:
                        price = spec.get('price')
                        break
            if price is None and isinstance(offers, dict):
                price = offers.get('price')
            try:
                price = float(price) if price is not None else None
            except (TypeError, ValueError):
                price = None
            return {
                'name': data.get('name'),
                'sku': data.get('sku') or data.get('mpn'),
                'price': price,
                'description': data.get('description') or '',
                'images': data.get('image') or [],
                'stock': 1 if 'InStock' in availability else 0,
                'brand': data.get('brand') or 'Cricut',
            }

        name = _T._text(html.xpath('string((//h1[contains(@class, "product-name")])[1])'))
        sku = _T._text(html.xpath('string((//*[contains(@class, "product-id")])[1])'))
        price = html.xpath(
            'string((//*[@data-automation-price-strike-through-value][1])/@data-automation-price-strike-through-value)'
        ) or html.xpath('string((//*[@data-automation-price][1])/@data-automation-price)')
        try:
            price = float(price) if price else None
        except (TypeError, ValueError):
            price = None
        desc = html.xpath(
            '(//div[contains(@class, "product-collapse")][.//span[normalize-space()="Description"]]'
            '//div[contains(@class, "product-collapse__content")][@id])[1]'
        )
        return {
            'name': name,
            'sku': sku or None,
            'price': price,
            'description': etree.tostring(desc[0], encoding='unicode', method='html') if desc else '',
            'images': html.xpath('//div[contains(@class, "product-detail")]//img[@itemprop="image"]/@src'),
            'stock': 0,
            'brand': 'Cricut',
        }

    @staticmethod
    def extract_variation_urls(html):
        urls = []
        for button in html.xpath('//button[contains(@class, "js-swatch")][@data-url]'):
            raw_url = (button.get('data-url') or '').strip()
            if not raw_url:
                continue
            if raw_url.startswith('/'):
                raw_url = Tool.URL.add_site(raw_url)
            parts = urlsplit(raw_url)
            query = parse_qsl(parts.query, keep_blank_values=True)
            attr_value = (button.get('data-attr-value') or '').strip()
            attr_id = (button.get('data-attr-id') or '').strip()
            # This is the selected-color display button rather than a variant.
            # Its URL leaves a dwvar value blank and returns an unpriced master.
            if not attr_id and not attr_value and any(
                key.startswith('dwvar_') and not value for key, value in query
            ):
                continue
            if attr_value:
                query = [
                    (
                        key,
                        attr_value
                        if key.startswith('dwvar_')
                        and not value
                        and (not attr_id or key.endswith(f'_{attr_id}'))
                        else value,
                    )
                    for key, value in query
                ]
            normalised = urlunsplit(
                (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
            )
            if VARIATION_ENDPOINT_MARKER in normalised and normalised not in urls:
                urls.append(normalised)
        return urls

    @staticmethod
    def _parent_id(variation_urls, fallback):
        for url in variation_urls:
            for key, value in parse_qsl(urlsplit(url).query, keep_blank_values=True):
                if key == 'pid' and value:
                    return value
        return fallback

    def run(self):
        if self.html is None:
            raise ValueError(f'商品 HTML 解析失败：{self.url}')

        fallback = self._fallback_product(self.html)
        common_fields = self._common_fields(self.page_html, self.variants)
        variation_urls = self.extract_variation_urls(self.html)
        valid_variants = []
        for payload in self.variants:
            product = payload.get('product') or {}
            price = self._price(product)
            name = self._text(product.get('productName'))
            if price is not None and name:
                valid_variants.append((payload, product, price))

        if self.variation_urls and len(valid_variants) < len(self.variation_urls):
            raise RuntimeError(
                f'变体数据不完整（{len(valid_variants)}/{len(self.variation_urls)}）：{self.url}'
            )

        if len(valid_variants) <= 1:
            if valid_variants:
                payload, product, price = valid_variants[0]
                return [Tool.Product.Simple(
                    url=self.url,
                    cat=self.category,
                    imgs=Tool.Product.clean_imgs(self._images(product, fallback['images'])),
                    name=self._text(product.get('productName')),
                    sku=self._variant_sku(payload) or fallback['sku'],
                    price=price,
                    desc=product.get('longDescription') or fallback['description'],
                    brand=product.get('brand') or fallback['brand'] or 'Cricut',
                    stock=self._stock(product),
                    **common_fields,
                ).to_dic()]
            if fallback['price'] is None or not fallback['name']:
                raise ValueError(f'商品缺少名称或价格：{self.url}')
            return [Tool.Product.Simple(
                url=self.url,
                cat=self.category,
                imgs=Tool.Product.clean_imgs(fallback['images']),
                name=fallback['name'],
                sku=fallback['sku'],
                price=fallback['price'],
                desc=fallback['description'],
                brand=fallback['brand'],
                stock=fallback['stock'],
                **common_fields,
            ).to_dic()]

        parent = self._parent_id(variation_urls, fallback['sku'] or fallback['name'])
        rows = []
        for payload, product, price in valid_variants:
            rows.append(Tool.Product.Variation(
                url=self.url,
                cat=self.category,
                imgs=Tool.Product.clean_imgs(self._images(product, fallback['images'])),
                name=self._text(product.get('productName')),
                sku=self._variant_sku(payload),
                price=price,
                desc=product.get('longDescription') or fallback['description'],
                att=self._attributes(product),
                parent=parent,
                brand=product.get('brand') or fallback['brand'] or 'Cricut',
                stock=self._stock(product),
                **common_fields,
            ).to_dic())
        return rows


if __name__ == '__main__':
    pc = Pc(
        tool=Tool,
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
        catch_save_num=catch_save_num,
    )
    pc.run()
