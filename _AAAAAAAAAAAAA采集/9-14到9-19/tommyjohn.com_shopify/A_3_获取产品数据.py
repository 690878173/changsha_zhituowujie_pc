import html as html_lib
import json
import re
import time

from config import Tool
from lxml import html as lxml_html
from _ljp.mb.shopify import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
fail_file = Tool.File.path_add_site('fail/4.json')
index_path = Tool.File.path_add_site('hc/4/index.json')
catch_path = Tool.File.path_add_site('hc/4/catch.json')
catch_save_num = None
skip_input_url_ls = []
skip_output_url_ls = []
fieldnames = None
ts_num = None
if_wp = False
time_sleep = 1


class Pc(Get_Product):
    def zdy_zd(self, url):
        """Read product accordion panels keyed by their button text."""
        try:
            response = self.tool.get(
                url,
                headers=self.tool.headers or None,
                cookies=self.tool.cookies or None,
                timeout=15,
            )
            if response.status_code != 200 or not response.text:
                return {}
            tree = lxml_html.fromstring(response.text)
        except Exception as exc:
            self.tool.print(f'[WARN] custom fields unavailable: {url}: {exc}')
            return {}

        fields = {}
        button_xpath = (
            '//button[@aria-controls and '
            'contains(concat(" ", normalize-space(@class), " "), " expandable ") and '
            'contains(concat(" ", normalize-space(@class), " "), " pt-lg ") and '
            'contains(concat(" ", normalize-space(@class), " "), " text-body-lg ") and '
            'contains(concat(" ", normalize-space(@class), " "), " border-t ")]'
        )
        for button in tree.xpath(button_xpath):
            name = ' '.join(' '.join(button.itertext()).split())
            panel_id = button.get('aria-controls')
            panels = tree.xpath('//*[@id=$panel_id]', panel_id=panel_id)
            if not name or not panels:
                continue
            value = self.tool.HTML.clean_product_desc(panels[0])
            if value:
                fields[name] = value

        # product-features is rendered client-side, so its panel is empty in
        # the initial DOM. The same server response embeds its data in
        # theme.product; use it only for the otherwise empty Details field.
        if 'The Details' not in fields:
            details = self._details_from_theme_product(response.text)
            if details:
                fields['The Details'] = details
        return fields

    @staticmethod
    def _details_from_theme_product(page_html):
        start = page_html.find('theme.product =')
        end = page_html.find('theme.collection', start + 1) if start >= 0 else -1
        if start < 0 or end < 0:
            return ''
        blob = page_html[start:end]
        match = re.search(
            r'"features"\s*:\s*\[(.*?)\],\s*"details"\s*:\s*\[(.*?)\],\s*"size_guide"',
            blob,
            flags=re.DOTALL,
        )
        if not match:
            return ''

        def decode(value):
            try:
                return json.loads(f'"{value}"')
            except Exception:
                return value

        features = re.findall(
            r'"label"\s*:\s*"((?:\\.|[^"\\])*)"\s*,\s*"icon"',
            match.group(1),
        )
        item_pairs = re.findall(
            r'"label"\s*:\s*"((?:\\.|[^"\\])*)"\s*,\s*"description"\s*:\s*"((?:\\.|[^"\\])*)"',
            match.group(2),
        )
        lines = [f'<ul><li>{html_lib.escape(decode(label))}</li>' for label in features]
        lines.extend(
            f'<li><strong>{html_lib.escape(decode(label))}</strong>: '
            f'{html_lib.escape(decode(description))}</li>'
            for label, description in item_pairs
        )
        return ''.join(lines) + '</ul>' if lines else ''

    def fetch_product(self, url, category):
        handle = self.tool.URL.get_handle(url)
        product_url = self.tool.URL.add_site(f'/products/{handle}.json')
        try:
            response = self.tool.get(
                product_url,
                headers=self.tool.headers or None,
                cookies=self.tool.cookies or None,
                timeout=15,
            )
            if response.status_code != 200:
                return []
            product = response.json().get('product')
            if not product:
                return []
            custom_key = self.tool.custom_key
            if custom_key:
                product[custom_key] = self.zdy_zd(url)
            product['__url'] = url
            time.sleep(time_sleep)
        except Exception as exc:
            self.tool.print(f'[ERROR] product request failed: {url}: {exc}')
            return []

        parent = self.shopify_to_woocommerce(
            product,
            brand=self.tool.site,
            custom_categories=category,
        )
        rows = [parent]
        rows.extend(self.create_variation_products(product, parent) or [])
        return rows


if __name__ == '__main__':
    Pc(
        tool=Tool,
        input_path=input_file,
        output_path=output_file,
        fail_file=fail_file,
        catch_path=catch_path,
        index_path=index_path,
        output_ts_file=output_ts_file,
        ts_num=ts_num,
        catch_save_num=catch_save_num,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        fieldnames=fieldnames,
        max_threads=10,
        if_wp=if_wp,
    ).run()
    Tool.close()
