"""Wahl PRO 商品详情解析（Magento 2 / Hyva）。

字段来源：
  - schema.org Product JSON-LD：名称、SKU、价格、库存、主图、分类
  - initConfigurableOptions()：可配置商品的变体矩阵（属性名、属性值、子 SKU、价格、图片）
  - 折叠区：Product Details / What's in the Box / Specifications
"""

import html as html_lib
import json
import re

from lxml import etree

from config import Tool
from _ljp.mb.zj import Get_Product

# 文件路径配置
input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site("res/result.csv")
fail_file = Tool.File.path_add_site('data/fail.json')

catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
# 携带原始url输出文件
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

# 测试数据条数 (None = 全部抓取)
ts_num = None

catch_save_num = None
# URL黑名单
skip_input_url_ls = []
# 未实现字段
skip_output_url_ls = []

headers = None
cookies = None

flush = False

# CSV输出表头,默认就应该为None，表头后续会处理
fieldnames = None

max_threads = 2

BRAND = 'Wahl Professional'
CUSTOM_FIELDS = ('Product Details', "What's in the Box", 'Specifications')
AVAILABILITY_OUT = 'outofstock'

_LD_JSON_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.S | re.I,
)
_CONFIGURABLE_RE = re.compile(
    r'initConfigurableOptions\(\s*\'(\d+)\'\s*,\s*(\{.*?\})\s*\)\s*;',
    re.S,
)
_VENDOR_SKU_RE = re.compile(r'(\d{4,5}(?:-\d{2,4})*)$')
_PAGE_BUILDER_STYLE_RE = re.compile(
    r'#html-body\s+\[data-pb-style=(?:["\'])?[A-Za-z0-9_-]+(?:["\'])?\]'
    r'[^{}]*\{[^{}]*\}\s*',
    re.I,
)


def product_json(text):
    """返回页面里的 schema.org Product 对象。"""
    for block in _LD_JSON_RE.findall(text or ''):
        try:
            value = json.loads(html_lib.unescape(block.strip()))
        except ValueError:
            continue
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, dict) and item.get('@type') == 'Product':
                return item
    return {}


def offer_list(product):
    """schema.org offers 既可能是对象（单变体），也可能是数组（多变体）。"""
    offers = product.get('offers')
    if isinstance(offers, list):
        return [item for item in offers if isinstance(item, dict)]
    if isinstance(offers, dict):
        return [offers]
    return []


def configurable_config(text):
    """可变商品的变体矩阵由 initConfigurableOptions(productId, {...}) 内联。"""
    match = _CONFIGURABLE_RE.search(text or '')
    if not match:
        return {}
    try:
        value = json.loads(match.group(2))
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def availability_of(offer):
    return str((offer or {}).get('availability') or '').rsplit('/', 1)[-1].lower()


def text_of(value):
    return '' if value is None else str(value).strip()


def embedded_array(text, key):
    """取 ``"key": [...]`` 里的 JSON 数组；用括号配对，避免惰性正则被截断。"""
    match = re.search(r'"%s"\s*:\s*\[' % re.escape(key), text or '')
    if not match:
        return []
    start = text.index('[', match.start())
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == '[':
            depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:index + 1])
                except ValueError:
                    return []
    return []


def image_entries(entries):
    """把图库/变体图片条目转成去重后的原图链接；跳过视频缩略图。"""
    if not isinstance(entries, list):
        return []
    result = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('type') == 'video':
            continue
        url = text_of(entry.get('full') or entry.get('img') or entry.get('thumb'))
        if url and url not in result:
            result.append(url)
    return result


class _T:
    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.html = etree.HTML(res_text)
        self.product = product_json(res_text)
        self.offers = offer_list(self.product)
        self.config = configurable_config(res_text)

    # ------------------ 通用取值 ------------------

    def meta(self, key):
        values = self.html.xpath('//meta[@property=$key]/@content', key=key)
        return text_of(values[0]) if values else ''

    # ------------------ 主商品字段 ------------------

    def get_main_name(self):
        return self.meta('og:title') or text_of(self.product.get('name'))

    def get_main_sku(self):
        return (
            text_of(self.product.get('sku') or self.product.get('productID'))
            or self.meta('product:retailer_item_id')
        )

    def get_main_price(self):
        if self.offers:
            return Tool.clean_price(self.offers[0].get('price'))
        return Tool.clean_price(self.html.xpath('string((//meta[@itemprop="price"]/@content)[1])'))

    def get_main_desc(self):
        value = self.meta('og:description') or text_of(self.product.get('description'))
        return self.clean_rich_text(value)

    @staticmethod
    def clean_rich_text(value):
        """移除 Magento Page Builder 的样式残留后保留可展示的富文本。"""
        value = text_of(value)
        for _ in range(3):
            decoded = html_lib.unescape(value)
            if decoded == value:
                break
            value = decoded

        had_page_builder_style = bool(_PAGE_BUILDER_STYLE_RE.search(value))
        value = _PAGE_BUILDER_STYLE_RE.sub('', value)
        if had_page_builder_style:
            value = re.sub(r'(<p[^>]*>)\s*Description\s*', r'\1', value, count=1, flags=re.I)

        cleaned = Tool.HTML.clean_product_desc_str(value)
        return re.sub(r'<p>\s*(?:<br>)?\s*</p>', '', cleaned).strip()

    def get_main_imgs(self):
        """整组图库图片（initialImages），而不是 og:image 的单张缩略图。"""
        images = image_entries(embedded_array(self.res_text, 'initialImages'))
        if images:
            return images
        fallback = self.meta('og:image') or text_of(self.product.get('image'))
        return [fallback] if fallback else []

    def get_main_stock(self):
        return self.stock_of(self.offers[0]) if self.offers else None

    @staticmethod
    def stock_of(offer):
        return 0 if availability_of(offer) == AVAILABILITY_OUT else None

    # ------------------ 自定义字段 ------------------

    def get_att(self):
        """三个折叠区，作为自定义字段导出。"""
        return {title: self.get_section(title) for title in CUSTOM_FIELDS}

    def get_section(self, title):
        nodes = self.html.xpath(
            '//button[.//span[normalize-space()=$title]]'
            '/following-sibling::div[@role="region"][1]',
            title=title,
        )
        if not nodes:
            return ''
        holder = nodes[0].xpath('.//div[@class="pb-4"]') or nodes
        return self.clean_section(holder[0])

    def clean_section(self, node):
        table = node.xpath('.//table')
        if table:
            return self.clean_table(table[0])
        return self.clean_rich_text(Tool.HTML.clean_product_desc(node))

    def clean_table(self, table):
        items = ['<ul>']
        for row in table.xpath('.//tr'):
            label = text_of(' '.join(row.xpath('./th//text()')))
            value = text_of(' '.join(row.xpath('./td//text()')))
            if label or value:
                items.append(
                    f'<li><strong>{html_lib.escape(label)}</strong>: '
                    f'{html_lib.escape(value)}</li>'
                )
        items.append('</ul>')
        return self.clean_rich_text(''.join(items))

    # ------------------ 变体 ------------------

    def check_cob(self):
        return bool(self.variants())

    def variants(self):
        """优先用页面变体矩阵；退化时用 JSON-LD 的多条 offer。"""
        from_config = self.config_variants() if self.config else []
        if from_config:
            return from_config
        if len(self.offers) > 1:
            return self.offer_variants()
        return []

    def config_variants(self):
        index = self.config.get('index') or {}
        attributes = self.config.get('attributes') or {}
        prices = self.config.get('optionPrices') or {}
        images = self.config.get('images') or {}
        skus = self.config.get('sku') or {}
        salable = self.config.get('salable') or {}

        rows = []
        for child_id, selection in index.items():
            att = {}
            for attribute_id, option_id in (selection or {}).items():
                meta = attributes.get(attribute_id) or {}
                label = text_of(meta.get('label') or meta.get('code') or attribute_id)
                value = ''
                for option in meta.get('options') or []:
                    if text_of(option.get('id')) == text_of(option_id):
                        value = text_of(option.get('label'))
                        break
                if label and value:
                    att[label] = value
            if not att:
                continue
            rows.append({
                'sku': text_of(skus.get(child_id)) or None,
                'price': self.config_price(prices.get(child_id)),
                'att': att,
                'imgs': self.config_images(images.get(child_id)),
                'stock': self.config_stock(child_id, selection, salable),
            })
        return rows

    @staticmethod
    def config_price(node):
        if not isinstance(node, dict):
            return ''
        for key in ('finalPrice', 'basePrice', 'oldPrice'):
            amount = (node.get(key) or {}).get('amount')
            if amount not in (None, ''):
                return Tool.clean_price(amount)
        return ''

    @staticmethod
    def config_images(entries):
        """该变体的全部静态图；跳过 Magic360 / 视频缩略图。"""
        return image_entries(entries)

    @staticmethod
    def config_stock(child_id, selection, salable):
        if not salable:
            return None
        for attribute_id, option_id in (selection or {}).items():
            allowed = (salable.get(attribute_id) or {}).get(option_id)
            if allowed is not None and child_id not in allowed:
                return 0
        return None

    def offer_variants(self):
        """没有变体矩阵时，用 JSON-LD 的 offer 列表拆分变体。"""
        name = self.get_main_name()
        name_words = {word for word in name.split() if word}
        rows = []
        for offer in self.offers:
            offer_sku = text_of(offer.get('sku'))
            offer_name = text_of(offer.get('name'))
            # 变体名里去掉主商品名后剩下的部分就是区分值，
            # 例如 "Arco® Radiant Pink" -> "Radiant Pink"。
            value = ' '.join(
                word for word in offer_name.split() if word not in name_words
            ).strip(' -–|')
            if not value and name and offer_name.startswith(name):
                value = offer_name[len(name):].strip(' -–|')
            if not value:
                match = _VENDOR_SKU_RE.search(offer_sku)
                value = match.group(1) if match else offer_sku
            if not offer_sku or not value:
                continue
            rows.append({
                'sku': offer_sku,
                'price': Tool.clean_price(offer.get('price')),
                'att': {'Variant': value},
                'imgs': [],
                'stock': self.stock_of(offer),
            })
        return rows

    # ------------------ 入口 ------------------

    def run(self):
        name = self.get_main_name()
        price = self.get_main_price()
        sku = self.get_main_sku()
        desc = self.get_main_desc()
        imgs = self.get_main_imgs()
        custom = self.get_att()

        variants = self.variants()
        if variants:
            rows = []
            for item in variants:
                rows.append(Tool.Product.Variation(
                    url=self.url,
                    cat=self.category,
                    imgs=item['imgs'] or imgs,
                    name=name,
                    desc=desc,
                    price=item['price'] or price,
                    sku=item['sku'],
                    att=item['att'],
                    parent=sku,
                    brand=BRAND,
                    stock=item['stock'],
                    **custom,
                ).to_dic())
            return rows

        return [Tool.Product.Simple(
            url=self.url,
            cat=self.category,
            imgs=imgs,
            name=name,
            sku=sku,
            price=price,
            desc=desc,
            stock=self.get_main_stock(),
            brand=BRAND,
            **custom,
        ).to_dic()]


class Pc(Get_Product):
    def fetch_product(self, url, category):
        """请求并解析单个商品。"""
        res = Tool.get(url, headers=headers, cookies=cookies)
        if res.status_code != 200 or not res.text:
            raise RuntimeError(f'详情页请求失败（HTTP {res.status_code}）：{url}')
        return _T(url, category, res.text).run()


if __name__ == '__main__':
    pc = Pc(tool=Tool,
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
            catch_save_num=catch_save_num
            )
    pc.run()
