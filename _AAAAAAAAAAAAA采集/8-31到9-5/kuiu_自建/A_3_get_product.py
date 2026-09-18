from html import escape

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


class Pc(Get_Product):
    def fetch_product(self, url, category):
        product_response = Tool.get(f'{url.rstrip("/")}.js', headers=headers, cookies=cookies)
        page_response = Tool.get(url, headers=headers, cookies=cookies)

        if product_response.status_code != 200:
            raise RuntimeError(f'商品 JSON 请求失败（HTTP {product_response.status_code}）')
        if page_response.status_code != 200:
            raise RuntimeError(f'商品页面请求失败（HTTP {page_response.status_code}）')

        return _T(url, category, product_response.json(), page_response.text).run()


class _T:
    def __init__(self, url, category, product, page_html):
        if not isinstance(product, dict):
            raise TypeError(f'商品 JSON 不是字典：{url}')

        self.url = url
        self.category = category
        self.product = product
        self.html = etree.HTML(page_html)

    @staticmethod
    def _text(node):
        return ' '.join(''.join(node.itertext()).split())

    @staticmethod
    def _inner_html(node, excluded_tags=()):
        fragments = []
        if node.text and node.text.strip():
            fragments.append(f'<p>{escape(node.text.strip())}</p>')
        for child in node:
            if child.tag not in excluded_tags:
                fragments.append(etree.tostring(child, encoding='unicode', method='html'))
            if child.tail and child.tail.strip():
                fragments.append(f'<p>{escape(child.tail.strip())}</p>')
        return ''.join(fragments)

    def get_main_name(self):
        title = (self.product.get('title') or '').strip()
        name, separator, _ = title.partition(' | ')
        return name.strip() if separator else title

    def get_color(self):
        title = (self.product.get('title') or '').strip()
        _, separator, color = title.partition(' | ')
        return color.strip() if separator else ''

    def get_main_desc(self):
        return self.product.get('description') or ''

    def get_main_imgs(self):
        images = self.product.get('images') or []
        return [f'https:{image}' if image.startswith('//') else image for image in images]

    def get_custom_fields(self):
        fields = {}
        short_desc = self.html.xpath('string((//*[contains(@class, "PDP-Product-Short-Description")])[1])')
        if short_desc := ' '.join(short_desc.split()):
            fields['Short Description'] = short_desc

        feature_sections = self.html.xpath('//section[h2[normalize-space()="Features"]]')
        if not feature_sections:
            return fields

        feature_section = feature_sections[0]
        feature_parts = []
        for child in feature_section:
            if child.tag == 'h2':
                continue
            if child.tag == 'ul' and child.xpath('./li[h3]'):
                for item in child.xpath('./li[h3]'):
                    label = self._text(item.xpath('./h3')[0])
                    detail = self._inner_html(item, excluded_tags={'h3'})
                    if label and detail:
                        fields[label] = detail
                continue
            feature_parts.append(etree.tostring(child, encoding='unicode', method='html'))
            if child.tail and child.tail.strip():
                feature_parts.append(f'<p>{escape(child.tail.strip())}</p>')

        features = ''.join(feature_parts).strip()
        if features:
            fields['Features'] = features
        return fields

    def get_variant_attributes(self, variant):
        attributes = {}
        color = self.get_color()
        if color:
            attributes['Color'] = color

        for option in self.product.get('options') or []:
            position = option.get('position')
            name = (option.get('name') or '').strip()
            value = variant.get(f'option{position}') if position else None
            if name and value:
                attributes[name] = str(value).strip()
        return attributes

    @staticmethod
    def get_variant_price(variant):
        price = variant.get('price')
        if not isinstance(price, (int, float)):
            raise ValueError(f'变体价格无效：{price!r}')
        return price / 100

    def get_variant_images(self, variant, main_images):
        featured = variant.get('featured_image') or {}
        source = featured.get('src') if isinstance(featured, dict) else None
        if source:
            return [f'https:{source}' if source.startswith('//') else source]
        return main_images

    def run(self):
        variants = self.product.get('variants') or []
        if not variants:
            raise ValueError('商品没有可用的变体数据')

        name = self.get_main_name()
        if not name:
            raise ValueError('商品名称为空')

        images = Tool.Product.clean_imgs(self.get_main_imgs())
        description = self.get_main_desc()
        custom_fields = self.get_custom_fields()
        if color := self.get_color():
            custom_fields['Color'] = color

        if len(variants) == 1:
            variant = variants[0]
            return [
                Tool.Product.Simple(
                    url=self.url,
                    cat=self.category,
                    imgs=self.get_variant_images(variant, images),
                    name=name,
                    sku=variant.get('sku') or self.product.get('handle'),
                    price=self.get_variant_price(variant),
                    desc=description,
                    brand=self.product.get('vendor'),
                    stock=1 if variant.get('available') else 0,
                    **custom_fields,
                ).to_dic()
            ]

        parent = str(self.product.get('id') or self.product.get('handle') or name)
        products = []
        for variant in variants:
            products.append(
                Tool.Product.Variation(
                    url=self.url,
                    cat=self.category,
                    imgs=self.get_variant_images(variant, images),
                    name=name,
                    desc=description,
                    price=self.get_variant_price(variant),
                    sku=variant.get('sku'),
                    att=self.get_variant_attributes(variant),
                    parent=parent,
                    brand=self.product.get('vendor'),
                    stock=1 if variant.get('available') else 0,
                    **custom_fields,
                ).to_dic()
            )
        return products


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
