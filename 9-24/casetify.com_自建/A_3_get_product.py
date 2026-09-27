"""Export CASETiFY design pages as Shopify-ready variation families."""

import json
import re
from hashlib import sha1
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit

from lxml import etree

from config import Tool
from _ljp.mb.zj import Get_Product


INPUT_FILE = Tool.File.path_add_site('data/detail_url.json')
OUTPUT_FILE = Tool.File.path_add_site('res/result.csv')
FAIL_FILE = Tool.File.path_add_site('fail/3/fail.json')
CATCH_PATH = Tool.File.path_add_site('hc/3/data_product_case_type_v3.json')
INDEX_PATH = Tool.File.path_add_site('hc/3/index_product_case_type_v3.json')
OUTPUT_TS_FILE = Tool.File.path_add_site('hc/3/ts_url.csv')

# Two design pages are enough to inspect family fields before a full export.
ts_num = None
catch_save_num = 50
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
fieldnames = None
max_threads = 10


class Pc(Get_Product):
    """Load one canonical design page per category and exclude value sets."""
    bundle_markers = ('bundle', 'blind-box', '-set', '-sets', 'box-')

    @classmethod
    def is_bundle_url(cls, url):
        return any(marker in urlsplit(url).path.casefold() for marker in cls.bundle_markers)

    @staticmethod
    def canonical_design_url(url):
        parsed = urlsplit(url)
        parts = [part for part in parsed.path.split('/') if part]
        if len(parts) < 3 or parts[:2] != ['en_US', 'product']:
            return ''
        return urlunsplit((parsed.scheme, parsed.netloc, f'/en_US/product/{parts[2]}', '', ''))

    def load_tasks(self):
        source = Tool.File.load_json(self.input_path)
        filtered = {}
        for category, urls in source.items():
            seen = set()
            design_urls = []
            for url in urls:
                if self.is_bundle_url(url):
                    continue
                design_url = self.canonical_design_url(url)
                if design_url and design_url not in seen:
                    seen.add(design_url)
                    design_urls.append(design_url)
            if design_urls:
                filtered[category] = design_urls
        self._load_tasks_from_mapping(filtered)

    def fetch_product(self, url, category):
        response = Tool.get(url)
        if response.status_code != 200 or not response.text:
            raise ValueError(f'PDP request failed: HTTP {response.status_code}')
        if not hasattr(self, '_product_spec_cache'):
            self._product_spec_cache = {}
        return _T(
            url,
            category,
            response.text,
            Tool.config.headers,
            self._product_spec_cache,
        ).run()


class _T:
    """Convert every sellable item option on one design page into variations."""

    product_fields = (
        'itemList.id,itemList.device_type_id,itemList.product_type_id,'
        'itemList.item_type_description,itemList.description,itemList.status,'
        'itemList.base_price,itemList.original_base_price,itemList.product_images,'
        'deviceList.id,deviceList.description,deviceList.short_name,'
        'productList.id,productList.description,productList.short_name'
    )

    def __init__(self, url, category, res_text, headers, product_spec_cache=None):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.headers = headers
        self.html = etree.HTML(res_text)
        if self.html is None:
            raise ValueError('PDP HTML is invalid')
        self.prefetch = self.get_server_object('Server.prefetchArtwork')
        self.filter_hints = self.get_server_object('Server.artworkFilterHints')
        self.schema = self.get_schema_product()
        self.api_data = None
        self.devices = {}
        self.products = {}
        resolved_filter = self.filter_hints.get('resolvedFilter') or {}
        self.segment_ids = {
            str(segment_id)
            for segment_id in resolved_filter.get('segmentIds') or []
            if segment_id is not None
        }
        self.product_spec_cache = product_spec_cache if product_spec_cache is not None else {}

    def get_server_object(self, variable):
        data = Tool.HTML.extract_js_object(self.res_text, variable)
        if not isinstance(data, dict):
            raise ValueError(f'PDP missing {variable}')
        return data

    def get_schema_product(self):
        for text in self.html.xpath('//script[@type="application/ld+json"]/text()'):
            try:
                data = json.loads(text)
            except (TypeError, json.JSONDecodeError):
                continue
            values = data if isinstance(data, list) else [data]
            for value in values:
                if isinstance(value, dict) and value.get('@type') == 'Product':
                    return value
        return {}

    def get_product_api_data(self):
        resolved = self.filter_hints.get('resolvedFilter')
        if not isinstance(resolved, dict):
            raise ValueError('PDP has no resolved product filter')

        params = {
            'fn': 'getProductDetail',
            'lang': 'en_US',
            'fields': self.product_fields,
            'artworkId': resolved.get('artworkId') or self.prefetch.get('id'),
            'layout': resolved.get('layout') or '',
            'sizeIds': ','.join(resolved.get('sizeIds') or []),
            'brandIds': ','.join(resolved.get('brandIds') or []),
            'segmentIds': ','.join(resolved.get('segmentIds') or []),
            'priceTierId': resolved.get('priceTierId') or '',
            'countryId': resolved.get('countryId') or '',
            'currency': resolved.get('currency') or '',
            'isRequestFromAd': resolved.get('isRequestFromAd') or '0',
        }
        response = Tool.get(
            'https://cdn.casetify.com/api-cache/10m/Artwork?' + urlencode(params),
            headers=self.headers,
        )
        if response.status_code != 200:
            raise ValueError(f'Product API request failed: HTTP {response.status_code}')
        payload = response.json()
        data = payload.get('data') if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise ValueError('Product API payload has no data object')
        return data

    def get_main_name(self):
        return str(
            self.schema.get('name')
            or self.prefetch.get('art_work_name')
            or self.prefetch.get('art_work_url_name')
            or ''
        ).strip()

    def get_parent_sku(self, item=None, content=None):
        artwork_id = str(self.prefetch.get('id') or '').strip()
        if not artwork_id:
            raise ValueError('PDP has no artwork id')
        if item is None:
            return f'CTF-{artwork_id}'

        case_type = self.get_item_case_type(item)
        if not case_type:
            raise ValueError('Product item has no case type')
        if content is None:
            content = self.get_item_content(item)
        spec_key = '\x00'.join(
            [content.get('Description', ''), content.get('Product Details', '')]
        )
        case_hash = sha1(case_type.encode('utf-8')).hexdigest()[:10]
        spec_hash = sha1(spec_key.encode('utf-8')).hexdigest()[:10]
        return f'CTF-{artwork_id}-CT{case_hash}-S{spec_hash}'

    def get_sellable_items(self):
        items = self.api_data.get('itemList') or []
        sellable = []
        for item in items:
            if not isinstance(item, dict) or item.get('status') not in {'A', 'P'}:
                continue
            sale_price = item.get('base_price')
            regular_price = item.get('original_base_price') or sale_price
            if sale_price is None or regular_price is None:
                continue
            try:
                if float(sale_price) <= 0 or float(regular_price) <= 0:
                    continue
            except (TypeError, ValueError):
                continue
            sellable.append(item)
        if not sellable:
            raise ValueError('Product API contains no sellable item options')
        return sellable

    def load_option_maps(self):
        self.devices = {
            str(item.get('id')): str(item.get('description') or '').strip()
            for item in self.api_data.get('deviceList') or []
        }
        self.products = {
            str(item.get('id')): str(item.get('description') or '').strip()
            for item in self.api_data.get('productList') or []
        }

    @staticmethod
    def get_case_type(product):
        return str(product or '').strip()

    def get_item_case_type(self, item):
        return self.get_case_type(self.products.get(str(item.get('product_type_id'))))

    @staticmethod
    def get_item_color(item, device):
        color = str(item.get('item_type_description') or '').strip()
        if color:
            return color
        parts = [part.strip() for part in str(item.get('description') or '').split(' - ')]
        if len(parts) > 1 and parts[0].casefold() == device.casefold():
            return parts[-1]
        return ''

    def get_item_attributes(self, item):
        device = self.devices.get(str(item.get('device_type_id'))) or 'Universal'
        case_type = self.get_item_case_type(item)
        return {
            'Device': device,
            'Case Type': case_type,
            'Color': self.get_item_color(item, device),
        }

    def get_item_sku(self, item):
        return f'{self.get_parent_sku()}-{item["id"]}'

    def get_item_name(self, item):
        case_type = self.get_item_case_type(item)
        main_name = self.get_main_name()
        return f'{main_name} - {case_type}' if main_name and case_type else main_name or case_type

    @staticmethod
    def get_localized_value(value):
        if isinstance(value, dict):
            value = value.get('en_US') or value.get('en_GB') or next(
                (item for item in value.values() if item),
                '',
            )
        return str(value or '').strip()

    def is_visible(self, block):
        visibility = block.get('visibility') if isinstance(block, dict) else None
        if not isinstance(visibility, dict):
            return True
        included = {str(segment_id) for segment_id in visibility.get('includedSegmentIds') or []}
        excluded = {str(segment_id) for segment_id in visibility.get('excludedSegmentIds') or []}
        if self.segment_ids and included and not self.segment_ids.intersection(included):
            return False
        return not self.segment_ids.intersection(excluded)

    def get_spec_block_content(self, blocks):
        values = []
        for block in blocks or []:
            if not isinstance(block, dict) or not self.is_visible(block):
                continue
            data = block.get('data') or {}
            for key in ('html', 'text'):
                value = self.get_localized_value(data.get(key))
                if value:
                    values.append(value)
            values.extend(self.get_spec_block_content(block.get('blocks')))
        return values

    def get_product_spec(self, product_type_id):
        product_type_id = str(product_type_id or '').strip()
        if not product_type_id:
            return {}
        cache_key = (product_type_id, tuple(sorted(self.segment_ids)))
        cached = self.product_spec_cache.get(cache_key)
        if cached is not None:
            return cached

        response = Tool.get(
            'https://cdn.casetify.com/api-cache/1h/CartesianProduct',
            params={'fn': 'getProductSpec', 'productTypeId': product_type_id},
            headers=self.headers,
        )
        if response.status_code != 200:
            raise ValueError(f'Product spec request failed: HTTP {response.status_code}')
        payload = response.json()
        blocks = payload.get('data') if isinstance(payload, dict) else None
        if not isinstance(blocks, list):
            raise ValueError(f'Product spec payload is invalid for product type {product_type_id}')

        spec = {}
        for block in blocks:
            if not isinstance(block, dict) or not self.is_visible(block):
                continue
            title = self.get_localized_value((block.get('data') or {}).get('title')).casefold()
            if title not in {'description', 'product details'}:
                continue
            value = '\n'.join(self.get_spec_block_content(block.get('blocks')))
            if value:
                spec[title] = value
        self.product_spec_cache[cache_key] = spec
        return spec

    @staticmethod
    def clean_price(value):
        return Tool.clean_price(value)

    def render_image_url(self, source, meta):
        replacements = {
            'UserBucket': self.prefetch.get('bucket_id', ''),
            'UserId': self.prefetch.get('user_id', ''),
            'ArtworkVersion': self.prefetch.get('version', ''),
            'DeviceVersion': '',
            'ItemOptionVersion': '',
            'ArtworkID': self.prefetch.get('id', ''),
            'DeviceColor': (meta or {}).get('deviceColor', ''),
            'PaletteOptionId': '',
        }
        for key, value in replacements.items():
            source = source.replace('{{' + key + '}}', str(value))
        return re.sub(r'\{\{[^}]+\}\}', '', source)

    def get_item_images(self, item):
        images = []
        for image in item.get('product_images') or []:
            if isinstance(image, dict) and image.get('src'):
                images.append(self.render_image_url(image['src'], image.get('meta')))
        if not images:
            schema_images = self.schema.get('image') or []
            if isinstance(schema_images, str):
                schema_images = [schema_images]
            images.extend(image for image in schema_images if isinstance(image, str))

        unique_images = {}
        for image in Tool.Product.clean_imgs(images):
            unique_images.setdefault(urlsplit(image).path, image)
        return list(unique_images.values())

    def get_item_content(self, item):
        spec = self.get_product_spec(item.get('product_type_id'))
        return {
            'Description': spec.get('description', ''),
            'Product Details': spec.get('product details', ''),
        }

    def save_debug_snapshots(self):
        slug = self.prefetch.get('art_work_url_name') or self.prefetch.get('id')
        slug = re.sub(r'[^A-Za-z0-9._-]+', '-', str(slug)).strip('-') or 'product'
        debug_dir = Path(__file__).with_name('ts') / '03-product-data'
        Tool.HTML.save_raw(self.res_text, debug_dir / f'{slug}_page.html')
        (debug_dir / f'{slug}_{self.get_parent_sku()}_variations.json').write_text(
            json.dumps(self.api_data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    def get_cobs(self):
        variations = []
        for item in self.get_sellable_items():
            sale_price = self.clean_price(item.get('base_price'))
            regular_price = self.clean_price(item.get('original_base_price') or sale_price)
            content = self.get_item_content(item)
            parent_sku = self.get_parent_sku(item, content)
            variation = Tool.Product.Variation(
                url=self.url,
                cat=self.category,
                imgs=self.get_item_images(item),
                name=self.get_item_name(item),
                desc=Tool.HTML.clean_product_desc_str(content['Description']),
                price=sale_price,
                sku=self.get_item_sku(item),
                parent=parent_sku,
                att=self.get_item_attributes(item),
                **{'Product Details': content['Product Details']},
            ).to_dic()
            variation['Regular price'] = regular_price
            variations.append(variation)
        return variations

    def run(self):
        self.api_data = self.get_product_api_data()
        self.load_option_maps()
        self.save_debug_snapshots()
        return self.get_cobs()


if __name__ == '__main__':
    Pc(
        tool=Tool,
        input_path=INPUT_FILE,
        output_path=OUTPUT_FILE,
        fail_file=FAIL_FILE,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        ts_num=ts_num,
        fieldnames=fieldnames,
        catch_path=CATCH_PATH,
        index_path=INDEX_PATH,
        output_ts_file=OUTPUT_TS_FILE,
        flush=flush,
        max_threads=max_threads,
        catch_save_num=catch_save_num,
    ).run()
