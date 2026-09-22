import time
import json
from html import escape

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

skip_input_url_ls = []
skip_output_url_ls = []
# 默认使用fieldnames=None,自动写入自定义字段，需要控制字段写入由下游控制，这里保留所有字段
fieldnames = None

ts_num = None
headers=None
cookies=None
if_wp = False
time_sleep = 2

from _ljp.mb.shopify import Get_Product


class Pc(Get_Product):

    SANITY_FIELDS = {
        'description': 'Description',
        'whats_included': 'Whats Included',
        'tech_specs': 'Tech Specs',
        'vibration_solution': 'Vibration Solution',
    }

    @staticmethod
    def _script_json(tree, attribute):
        text = tree.xpath(f'string(//script[@{attribute}])').strip()
        return json.loads(text) if text else None

    @staticmethod
    def _inline_html(block):
        parts = []
        for child in block.get('children') or []:
            text = str(child.get('text') or '')
            if text:
                parts.append(escape(text))
        return ''.join(parts).strip()

    @staticmethod
    def _referenced_blocks(block, reusable):
        mark_keys = {
            mark
            for child in block.get('children') or []
            for mark in child.get('marks') or []
        }
        resolved = []
        for definition in block.get('markDefs') or []:
            reference = definition.get('_ref')
            if reference and definition.get('_key') in mark_keys:
                value = reusable.get(reference) or {}
                text_blocks = value.get('text_blocks')
                if not isinstance(text_blocks, list):
                    text_blocks = value.get('body')
                if isinstance(text_blocks, list):
                    resolved.extend(
                        item for item in text_blocks if isinstance(item, dict)
                    )
        return resolved

    def _portable_html(self, blocks, reusable, *, resolve_references=True):
        result = []
        list_tag = ''
        list_items = []

        def flush_list():
            nonlocal list_tag, list_items
            if list_items:
                result.append(f'<{list_tag}>' + ''.join(list_items) + f'</{list_tag}>')
            list_tag = ''
            list_items = []

        for block in blocks or []:
            if not isinstance(block, dict):
                continue
            text = self._inline_html(block)
            referenced = (
                self._referenced_blocks(block, reusable) if resolve_references else []
            )
            if referenced:
                flush_list()
                if text:
                    result.append(f'<h6>{text}</h6>')
                result.append(
                    self._portable_html(
                        referenced,
                        reusable,
                        resolve_references=False,
                    )
                )
                continue

            if not text:
                continue
            list_item = block.get('listItem')
            if list_item:
                next_list_tag = 'ol' if list_item == 'number' else 'ul'
                if list_tag and list_tag != next_list_tag:
                    flush_list()
                list_tag = next_list_tag
                list_items.append(f'<li>{text}</li>')
                continue

            flush_list()
            style = str(block.get('style') or '').lower()
            tag = style if style in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'} else 'p'
            result.append(f'<{tag}>{text}</{tag}>')

        flush_list()
        return ''.join(result)

    def zdy_zd(self, url, html_text=None):
        """读取 Quad Lock 页面内嵌的 Sanity 自定义产品内容。"""
        fields = {name: '' for name in self.SANITY_FIELDS.values()}
        if not html_text:
            response = self.tool.get(url, headers=headers, cookies=cookies, timeout=15)
            if response.status_code != 200:
                self.tool.print(f'[WARN] 自定义字段页面请求失败: {url}')
                return fields
            html_text = response.text

        try:
            tree = etree.HTML(html_text)
            content = self._script_json(tree, 'data-sanity-content-json') or {}
            reusable_data = self._script_json(tree, 'data-sanity-reusable-json') or []
            reusable = {
                item.get('_id'): item
                for item in reusable_data
                if isinstance(item, dict) and item.get('_id')
            }
            for item in content.get('moreInfoContent') or []:
                title = str(item.get('title') or '').strip().lower().replace(' ', '_')
                field_name = self.SANITY_FIELDS.get(title)
                if not field_name:
                    continue
                raw_html = self._portable_html(item.get('text') or [], reusable)
                fields[field_name] = self.tool.HTML.clean_product_desc_str(raw_html)
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError) as error:
            self.tool.print(f'[WARN] 自定义字段解析失败: {url} | {error}')
        return fields

    def fetch_product(self, url, category) -> list:
        Tool = self.tool
        handle = Tool.URL.get_handle(url)

        p_url = f"https://www.{Tool.site}.com/products/{handle}.json"

        try:
            r = Tool.get(p_url, headers=headers,cookies=cookies,timeout=15)

            if r.status_code != 200:
                return []
            data = r.json()

            page_response = Tool.get(url, headers=headers, cookies=cookies, timeout=15)
            zdy_data = self.zdy_zd(url, page_response.text if page_response.status_code == 200 else None)

            time.sleep(time_sleep)

            shopify_product = data.get("product")
            if not isinstance(shopify_product, dict):
                return []

            shopify_product[Tool.custom_key] = zdy_data
            shopify_product['__url'] = url

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
