import json
import re
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from lxml import etree

from config import Tool
from _ljp.mb.zj import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
fail_file = Tool.File.path_add_site('fail/3/fail.json')
catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
output_ts_file = Tool.File.path_add_site('hc/3/ts_url.csv')

# Validate a small number of distinct product tasks before a full run.
ts_num = None
catch_save_num = None
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
fieldnames = None
max_threads = 2


class Pc(Get_Product):
    """Collect Sonos PDP data from server-rendered HTML and its JSON-LD."""

    def fetch_product(self, url, category):
        response = Tool.get(url)
        if response.status_code != 200 or not response.text:
            self._save_failed_response(url, response.text)
            Tool.print(f'[A_3] HTTP {response.status_code}: {url}', color='yellow')
            return []

        parser = _T(url, category, response.text)
        parser.save_snapshot()
        return parser.run()

    @staticmethod
    def _save_failed_response(url, html_text):
        if not html_text:
            return
        slug = urlsplit(url).path.rstrip('/').split('/')[-1] or 'product'
        path = Path(__file__).parent / 'ts' / '03-product-data' / f'{slug}_unknown_page.html'
        try:
            Tool.HTML.save_raw(html_text, path)
        except OSError as exc:
            Tool.print(f'[A_3] failed to save debug HTML: {exc}', color='yellow')


class _T:
    """Parser for a single Sonos product page."""

    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.html = etree.HTML(res_text)
        self.json_ld_items = self._load_json_ld()
        self.product_group = self._find_product_group()
        self.variants = self._group_variants()
        self.selected_variant = self._find_selected_variant()

    @staticmethod
    def _canonical_url(value):
        if not value:
            return ''
        parsed = urlsplit(str(value))
        return f'{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path.rstrip("/")}'

    @classmethod
    def _same_url(cls, first, second):
        return bool(first and second and cls._canonical_url(first) == cls._canonical_url(second))

    @staticmethod
    def _has_type(item, expected_type):
        value = item.get('@type') if isinstance(item, dict) else None
        return expected_type in value if isinstance(value, list) else value == expected_type

    @classmethod
    def _walk_json(cls, value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from cls._walk_json(child)
        elif isinstance(value, list):
            for child in value:
                yield from cls._walk_json(child)

    @staticmethod
    def _node_text(node):
        if node is None:
            return ''
        return ' '.join(
            str(part).strip()
            for part in node.xpath('.//text()')
            if str(part).strip()
        )

    @staticmethod
    def _dedupe(values):
        result = []
        seen = set()
        for value in values:
            value = str(value or '').strip()
            if not value or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    @staticmethod
    def _first_string(value):
        if isinstance(value, list):
            for item in value:
                text = _T._first_string(item)
                if text:
                    return text
            return ''
        return str(value or '').strip()

    def _load_json_ld(self):
        if self.html is None:
            return []

        items = []
        for script in self.html.xpath('//script[@type="application/ld+json"]'):
            payload = (script.text or '').strip()
            if payload.startswith('<!--'):
                payload = payload[4:].removesuffix('-->').strip()
            if not payload:
                continue
            try:
                value = json.loads(payload)
            except json.JSONDecodeError:
                continue
            items.extend(self._walk_json(value))
        return items

    def _find_product_group(self):
        groups = [
            item for item in self.json_ld_items
            if self._has_type(item, 'ProductGroup')
        ]
        for group in groups:
            if self._same_url(group.get('url'), self.url):
                return group
            variants = group.get('hasVariant') or []
            if any(self._same_url(variant.get('url'), self.url) for variant in variants if isinstance(variant, dict)):
                return group
        return groups[0] if len(groups) == 1 else {}

    def _group_variants(self):
        if not isinstance(self.product_group, dict):
            return []
        variants = self.product_group.get('hasVariant') or []
        return [variant for variant in variants if isinstance(variant, dict)]

    def _find_selected_variant(self):
        for variant in self.variants:
            if self._same_url(variant.get('url'), self.url):
                return variant

        for item in self.json_ld_items:
            if self._has_type(item, 'Product') and self._same_url(item.get('url'), self.url):
                return item

        return self.variants[0] if len(self.variants) == 1 else {}

    @staticmethod
    def _clean_price(value):
        if value is None:
            return ''
        price = Tool.clean_price(str(value)).replace(',', '').strip()
        try:
            return price if float(price) > 0 else ''
        except ValueError:
            return ''

    def _variant_price(self, variant):
        offers = variant.get('offers') if isinstance(variant, dict) else None
        offers = offers if isinstance(offers, list) else [offers]
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            for key in ('price', 'lowPrice'):
                price = self._clean_price(offer.get(key))
                if price:
                    return price
            specification = offer.get('priceSpecification')
            specifications = specification if isinstance(specification, list) else [specification]
            for item in specifications:
                if isinstance(item, dict):
                    price = self._clean_price(item.get('price'))
                    if price:
                        return price
        return ''

    def _parent_id(self):
        if not isinstance(self.product_group, dict):
            return ''
        return self._first_string(
            self.product_group.get('productGroupID') or self.product_group.get('sku')
        )

    def _color_variants(self):
        result = []
        seen_skus = set()
        for variant in self.variants:
            sku = self._first_string(variant.get('sku'))
            color = self._first_string(variant.get('color'))
            price = self._variant_price(variant)
            if not sku or not color or not price or sku in seen_skus:
                continue
            seen_skus.add(sku)
            result.append(variant)
        return result

    def _rich_list(self, items, heading='', notes=None):
        notes = notes or []
        parts = []
        if heading:
            parts.append(f'<p><strong>{escape(heading)}</strong></p>')
        if items:
            parts.append('<ul>')
            parts.extend(f'<li>{escape(item)}</li>' for item in items)
            parts.append('</ul>')
        parts.extend(f'<p>{escape(note)}</p>' for note in notes if note)
        return Tool.HTML.clean_product_desc_str(''.join(parts)) if parts else ''

    def get_main_name(self):
        if self.html is not None:
            names = self.html.xpath('//h1[1]')
            if names:
                value = self._node_text(names[0])
                if value:
                    return value
        return self._first_string(
            self.product_group.get('name') if isinstance(self.product_group, dict) else ''
        ) or self._first_string(self.selected_variant.get('name'))

    def get_main_sku(self):
        return self._first_string(self.selected_variant.get('sku'))

    def get_main_price(self):
        price = self._variant_price(self.selected_variant)
        if price:
            return price

        if self.html is None:
            return ''
        main_sections = self.html.xpath('//section[@id="main"]')
        if not main_sections:
            return ''
        prices = main_sections[0].xpath('.//*[@data-testid="main-price"]')
        return self._clean_price(self._node_text(prices[0])) if prices else ''

    def get_main_desc(self):
        text = ''
        if self.html is not None:
            descriptions = self.html.xpath('//*[@data-testid="pdpShortDescription"]')
            if descriptions:
                text = self._node_text(descriptions[0])
        if not text and isinstance(self.product_group, dict):
            text = self._first_string(self.product_group.get('description'))

        paragraphs = [part.strip() for part in re.split(r'(?:\r?\n){2,}', text) if part.strip()]
        return Tool.HTML.clean_product_desc_str(
            ''.join(f'<p>{escape(paragraph)}</p>' for paragraph in paragraphs)
        )

    def get_main_imgs(self):
        images = []
        if self.html is not None:
            images = [
                image.get('src')
                for image in self.html.xpath('//*[@data-testid="product-gallery"]//img[@src]')
                if image.get('src') and not image.get('src').startswith('data:')
            ]
        images = self._dedupe(images)
        if images:
            return images

        fallback = self._first_string(self.selected_variant.get('image'))
        if not fallback and isinstance(self.product_group, dict):
            fallback = self._first_string(self.product_group.get('image'))
        return [fallback] if fallback else []

    def get_features(self):
        if self.html is None:
            return ''
        sections = self.html.xpath('//*[@data-testid="product-features"]')
        if not sections:
            return ''
        values = self._dedupe([
            self._node_text(node)
            for node in sections[0].xpath('.//*[@data-testid="caption-feature-caption"]')
        ])
        return self._rich_list(values)

    def get_whats_included(self):
        if self.html is None:
            return ''
        sections = self.html.xpath('//*[@data-testid="product-whats-included"]')
        if not sections:
            return ''

        section = sections[0]
        headings = section.xpath('.//h1 | .//h2 | .//h3')
        heading = self._node_text(headings[0]) if headings else ''
        lists = section.xpath('.//ul[1]')
        items = self._dedupe([
            self._node_text(item)
            for item in lists[0].xpath('./li')
        ]) if lists else []
        notes = self._dedupe([
            self._node_text(node)
            for node in section.xpath('.//*[@id="disclaimerBox"]')
        ])
        return self._rich_list(items, heading=heading, notes=notes)

    def get_custom_fields(self):
        return {
            'Features': self.get_features(),
            "What's included": self.get_whats_included(),
        }

    def _variant_imgs(self, variant, main_imgs):
        if self._same_url(variant.get('url'), self.url):
            return main_imgs
        image = self._first_string(variant.get('image'))
        return [image] if image else main_imgs[:1]

    def get_cobs(self, name, desc, main_imgs, custom_fields):
        parent = self._parent_id()
        rows = []
        for variant in self._color_variants():
            product = Tool.Product.Variation(
                url=variant.get('url') or self.url,
                cat=self.category,
                imgs=self._variant_imgs(variant, main_imgs),
                name=name,
                desc=desc,
                price=self._variant_price(variant),
                sku=self._first_string(variant.get('sku')),
                parent=parent,
                att={'Color': self._first_string(variant.get('color'))},
                **custom_fields,
            ).to_dic()
            rows.append(product)
        return rows

    def _debug_path(self):
        slug = urlsplit(self.url).path.rstrip('/').split('/')[-1] or 'product'
        parent = self._parent_id() or self.get_main_sku() or 'unknown'
        safe_slug = re.sub(r'[^A-Za-z0-9._-]+', '-', slug).strip('-') or 'product'
        safe_parent = re.sub(r'[^A-Za-z0-9._-]+', '-', parent).strip('-') or 'unknown'
        return Path(__file__).parent / 'ts' / '03-product-data' / f'{safe_slug}_{safe_parent}_page.html'

    def save_snapshot(self):
        try:
            Tool.HTML.save_raw(self.res_text, self._debug_path())
        except OSError as exc:
            Tool.print(f'[A_3] failed to save debug HTML: {exc}', color='yellow')

    def run(self):
        try:
            name = self.get_main_name()
            sku = self.get_main_sku()
            price = self.get_main_price()
            desc = self.get_main_desc()
            main_imgs = self.get_main_imgs()
            custom_fields = self.get_custom_fields()

            if not all((name, sku, price, desc, main_imgs)):
                raise ValueError('missing required product name, SKU, price, description, or images')

            color_variants = self._color_variants()
            if self._parent_id() and len(color_variants) > 1:
                return self.get_cobs(name, desc, main_imgs, custom_fields)

            return [Tool.Product.Simple(
                url=self.url,
                cat=self.category,
                imgs=main_imgs,
                name=name,
                sku=sku,
                price=price,
                desc=desc,
                **custom_fields,
            ).to_dic()]
        except (AttributeError, TypeError, ValueError) as exc:
            Tool.print(f'[A_3] parse failed for {self.url}: {exc}', color='yellow')
            return []


if __name__ == '__main__':
    try:
        Pc(
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
        ).run()
    finally:
        Tool.close()
