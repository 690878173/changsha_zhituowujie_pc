"""Patagonia variants collected through its browser-served SFCC endpoints."""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from html import escape as escape_html
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from lxml import html

from config import Tool
from _ljp.mb.base import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
fail_file = Tool.File.path_add_site('data/fail.json')
catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

ts_num = None
skip_input_url_ls = [
    '/product/mens-lightweight-synchilla-snap-t-fleece-pullover/25551.html?dwvar_25551_color=OTSM'
]
skip_output_url_ls = []
CUSTOM_FIELD_NAMES = (
    'Fit(product.metafields.c_f.fit)',
    'Specs Features(product.metafields.c_f.specs_features)',
    'Materials Care(product.metafields.c_f.materials_care)',
    'Country of Origin(product.metafields.c_f.country_of_origin)',
    'Weight(product.metafields.c_f.weight)',
)

# Keep only fields consumed by the remaining Patagonia export pipeline.  The
# former Master ID, Product Type and Availability values were endpoint state,
# not useful customer-facing product attributes.
fieldnames = [
    'Type', 'SKU', 'Name', 'Description', 'Sale price', 'Regular price',
    'Categories', 'Tags', 'Images', 'Parent', 'Attribute 1 name',
    'Attribute 1 value(s)', 'Attribute 2 name', 'Attribute 2 value(s)',
    'brand', 'Stock', *CUSTOM_FIELD_NAMES,
]


class Pc(Get_Product):
    """Use the exact endpoints requested when Patagonia color controls change."""

    max_attempts = 2
    variation_path = '/on/demandware.store/Sites-patagonia-us-Site/en_US/Product-Variation'
    alt_assets_path = '/on/demandware.store/Sites-patagonia-us-Site/en_US/Product-AltAssets'

    @staticmethod
    def _product_id(url):
        name = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
        if not name.endswith('.html') or not name[:-5]:
            raise ValueError(f'Cannot find product id in PDP URL: {url}')
        return name[:-5]

    @staticmethod
    def _color_id(url, product_id):
        values = parse_qs(urlsplit(url).query).get(f'dwvar_{product_id}_color', [])
        return next((value for value in values if value), '')

    @staticmethod
    def _is_not_found_html(source):
        try:
            tree = html.fromstring(source)
            title = ' '.join(tree.xpath('//title//text()')).strip().lower()
            body = ' '.join(tree.xpath('//body//text()')).strip().lower()
        except Exception:
            return False
        return title in {'404', '404 not found', 'not found', 'page not found'} or body in {
            '404', '404 not found', 'not found', 'page not found',
        }

    def _endpoint_body(self, endpoint, *, allow_empty=False):
        """Send one real browser navigation to an SFCC endpoint."""
        page = self.get_page()
        try:
            response = page.goto(endpoint, wait_until='domcontentloaded', timeout=60000)
            if response is None or not 200 <= response.status < 300:
                status = response.status if response else 0
                raise RuntimeError(f'Browser endpoint returned HTTP {status}: {endpoint}')
            source = response.body().decode('utf-8', errors='replace')
            if not source.strip() and not allow_empty:
                raise RuntimeError(f'Browser endpoint returned an empty response: {endpoint}')
            if self._is_not_found_html(source):
                raise RuntimeError(f'Browser endpoint returned a Not found page: {endpoint}')
            return source
        finally:
            try:
                page.close()
            except Exception:
                pass

    def _endpoint_url(self, path, **params):
        query = {key: value for key, value in params.items() if value not in (None, '')}
        return urljoin(Tool.config.base_url, path) + '?' + urlencode(query)

    def _variation(self, product_id, color=''):
        params = {'pid': product_id, 'quantity': 1}
        if color:
            params[f'dwvar_{product_id}_color'] = color
        source = self._endpoint_body(self._endpoint_url(self.variation_path, **params))
        try:
            payload = json.loads(source)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Product-Variation returned invalid JSON: {exc}') from exc
        product = payload.get('product') if isinstance(payload, Mapping) else None
        if not isinstance(product, Mapping):
            raise ValueError('Product-Variation response has no product object.')
        return product

    def _color_images(self, product_id, color):
        source = self._endpoint_body(
            self._endpoint_url(self.alt_assets_path, pid=product_id, selectedColor=color),
            allow_empty=True,
        )
        # Some valid colors have no alternate assets; SFCC returns whitespace only.
        if not source.strip():
            return []
        tree = html.fromstring(source)
        urls = []
        for srcset in tree.xpath('//source[@srcset]/@srcset'):
            candidates = [item.strip().split()[0] for item in srcset.split(',') if item.strip()]
            if candidates:
                urls.append(candidates[-1])
        return Tool.Product.clean_imgs(list(dict.fromkeys(urls)))

    @staticmethod
    def _attribute(product, attribute_id):
        for attribute in product.get('variationAttributes') or []:
            if isinstance(attribute, Mapping) and attribute.get('id') == attribute_id:
                return attribute
        return {}

    @classmethod
    def _color_values(cls, product):
        values = cls._attribute(product, 'color').get('values') or []
        return [value for value in values if isinstance(value, Mapping) and value.get('id')]

    @classmethod
    def _size_values(cls, product):
        values = cls._attribute(product, 'size').get('values') or []
        return [value for value in values if isinstance(value, Mapping) and value.get('id')]

    @staticmethod
    def _price(product):
        sales = (product.get('price') or {}).get('sales') or {}
        value = sales.get('value')
        if value is None:
            value = sales.get('formatted')
        return Tool.clean_price(value) if value is not None else ''

    @staticmethod
    def _text(nodes):
        return ' '.join(
            ' '.join(' '.join(node.itertext()).split())
            for node in nodes
            if ' '.join(node.itertext()).strip()
        )

    @staticmethod
    def _as_html_paragraph(value):
        value = ' '.join(str(value or '').split())
        return f'<p>{escape_html(value)}</p>' if value else ''

    @classmethod
    def _accordion_entries(cls, tree, name):
        groups = tree.xpath(f'//div[@data-pdp-accordion-{name}]')
        if not groups:
            return []
        entries = []
        for item in groups[0].xpath('.//li[./h3 or ./p]'):
            if 'init-fit-reviews' in item.get('class', ''):
                continue
            heading = cls._text(item.xpath('./h3'))
            content = cls._text(item.xpath('./p'))
            if content:
                entries.append((heading, content))
        return entries

    @classmethod
    def _entries_as_html(cls, entries):
        parts = []
        for heading, content in entries:
            if heading:
                parts.append(
                    f'<p><strong>{escape_html(heading)}</strong><br>'
                    f'{escape_html(content)}</p>'
                )
            else:
                parts.append(cls._as_html_paragraph(content))
        return ''.join(parts)

    @staticmethod
    def _entry_value(entries, heading):
        wanted = heading.casefold()
        for title, value in entries:
            if title.casefold() == wanted:
                return value
        return ''

    @staticmethod
    def _json_ld_items(tree):
        for source in tree.xpath('//script[@type="application/ld+json"]/text()'):
            try:
                payload = json.loads(source)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, list):
                yield from (item for item in payload if isinstance(item, Mapping))
            elif isinstance(payload, Mapping):
                yield payload

    @classmethod
    def _pdp_details(cls, source):
        """Extract customer-facing fields from the rendered Patagonia PDP HTML."""
        try:
            tree = html.fromstring(source)
        except (TypeError, ValueError) as exc:
            raise ValueError(f'Could not parse Patagonia PDP HTML: {exc}') from exc

        product_group = next(
            (
                item for item in cls._json_ld_items(tree)
                if 'ProductGroup' in (
                    item.get('@type', []) if isinstance(item.get('@type'), list)
                    else [item.get('@type')]
                )
            ),
            {},
        )
        description = cls._as_html_paragraph(product_group.get('description'))
        if not description:
            description = cls._as_html_paragraph(cls._text(tree.xpath(
                '//*[contains(concat(" ", normalize-space(@class), " "), '
                '" pdp-intro__description ")]'
            )))
        if not description:
            raise ValueError('Patagonia PDP has no product description.')

        fit = cls._accordion_entries(tree, 'fit')
        specs = cls._accordion_entries(tree, 'specs')
        materials = cls._accordion_entries(tree, 'materials')
        brand = (product_group.get('brand') or {}).get('name') or 'Patagonia'
        return {
            'description': description,
            'brand': str(brand).strip(),
            CUSTOM_FIELD_NAMES[0]: cls._entries_as_html(fit[:1]),
            CUSTOM_FIELD_NAMES[1]: cls._entries_as_html(specs),
            CUSTOM_FIELD_NAMES[2]: cls._entries_as_html(materials),
            CUSTOM_FIELD_NAMES[3]: cls._entry_value(specs, 'Country of Origin'),
            CUSTOM_FIELD_NAMES[4]: cls._entry_value(specs, 'Weight'),
        }

    def _product_details(self, url):
        return self._pdp_details(self._endpoint_body(url))

    def _rows_for_color(self, url, category, product_id, product, images, details):
        selected_color = product.get('selectedColor') or {}
        color_code = str(selected_color.get('colorCode') or '').strip()
        color_name = str(selected_color.get('colorText') or color_code).strip()
        name = str(product.get('productName') or '').strip()
        price = self._price(product)
        if not (name and price):
            raise ValueError(f'Incomplete Product-Variation data: name={name!r}, price={price!r}')

        rows = []
        sizes = self._size_values(product)
        if not sizes:
            sku = str(product.get('id') or product_id).strip()
            attributes = {'Color': color_name} if color_name else {'Style': product_id}
            rows.append(Tool.Product.Variation(
                url=url, cat=category, imgs=images, name=name,
                desc=details['description'], price=price,
                sku=sku, att=attributes, parent=product_id,
                brand=details['brand'], stock=0 if product.get('available') is False else None,
                **{key: details[key] for key in CUSTOM_FIELD_NAMES},
            ).to_dic())
            return rows

        for size in sizes:
            sku = str(size.get('pid') or '').strip()
            if not sku:
                continue
            size_name = str(size.get('displayValue') or size.get('id')).strip()
            row = Tool.Product.Variation(
                url=url,
                cat=category,
                imgs=images,
                name=name,
                desc=details['description'],
                price=price,
                sku=sku,
                att={'Color': color_name, 'Size': size_name},
                parent=product_id,
                brand=details['brand'],
                stock=None if size.get('selectable') else 0,
                **{key: details[key] for key in CUSTOM_FIELD_NAMES},
            ).to_dic()
            rows.append(row)
            safe_name = name.encode('ascii', errors='backslashreplace').decode('ascii')
            safe_color = color_name.encode('ascii', errors='backslashreplace').decode('ascii')
            print(
                f'[DATA] sku={sku} | name={safe_name} | price={price} '
                f'| Color={safe_color} | Size={size_name}'
            )
        if not rows:
            raise ValueError(f'Color {color_code or color_name!r} has no SKU-bearing size values.')
        return rows

    def fetch_product(self, url, category):
        url = Tool.URL.add_site(url)
        product_id = self._product_id(url)
        requested_color = self._color_id(url, product_id)
        last_error = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                details = self._product_details(url)
                if requested_color:
                    color_products = [self._variation(product_id, requested_color)]
                else:
                    master = self._variation(product_id)
                    colors = self._color_values(master)
                    color_products = [
                        self._variation(product_id, str(color['id'])) for color in colors
                    ] or [master]

                rows = []
                for product in color_products:
                    color = str((product.get('selectedColor') or {}).get('colorCode') or '').strip()
                    images = self._color_images(product_id, color) if color else []
                    rows.extend(
                        self._rows_for_color(url, category, product_id, product, images, details)
                    )
                if not rows:
                    raise ValueError('Product-Variation returned no SKU rows.')
                return rows
            except Exception as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    is_not_found = 'not found' in str(exc).lower()
                    action = 'Not found detected; relaunching browser' if is_not_found else 'Browser request failed; relaunching browser'
                    Tool.print(f'{action} ({attempt}/{self.max_attempts}): {exc}', color='yellow')
                    Tool.browser.restart_context(relaunch_browser=True)
        raise RuntimeError(str(last_error))

    def run(self):
        """Patagonia returns false 404s if its browser is created by a worker thread."""
        self.load_tasks()
        self.Tool.print(f'Total tasks to process: {self.total_tasks}')
        writer_thread = threading.Thread(target=self.writer_worker)
        writer_thread.start()
        self.request_worker()
        self.result_queue.put(None)
        writer_thread.join()

        all_rows = list(self._iter_all_product_rows())
        self.tool.File.save_csv(all_rows, self.output_ts_file, columns=self.fieldnames)
        clean_rows = self.tool.json_del_url(all_rows)
        self.tool.File.save_csv(clean_rows, self.output_file, columns=self.fieldnames)
        self.tool.File.save_json(self.failures, self.fail_file)
        self.Tool.print(f'Browser-fetched cache misses: {len(self.fetched_urls)}')
        self.Tool.print('==================== Done ====================')
        return all_rows


if __name__ == '__main__':
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
        max_threads=1,
    ).run()
