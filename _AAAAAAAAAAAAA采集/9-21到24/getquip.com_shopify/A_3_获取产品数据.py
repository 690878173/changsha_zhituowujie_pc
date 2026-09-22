"""Collect native Shopify variants and explicit cross-PDP swatch links."""

from lxml import html as lxml_html

from config import Tool
from _ljp.mb.shopify import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
fail_file = Tool.File.path_add_site('fail/4_linked_swatch_v1.json')
index_path = Tool.File.path_add_site('hc/4_linked_swatch_v1/index.json')
catch_path = Tool.File.path_add_site('hc/4_linked_swatch_v1/catch.json')


class Pc(Get_Product):
    @staticmethod
    def text(nodes):
        return ' '.join(' '.join(nodes).split())

    def linked_swatch_metadata(self, html_text, product_id):
        """Use only custom-swatch product IDs and their linked PDP URLs."""
        tree = lxml_html.fromstring(html_text)
        source_id = str(product_id or '').strip()
        handles, source_options, target_options = [], {}, {}
        for swatch in tree.xpath('//a[@data-product-custom-swatch]'):
            target_id = (swatch.get('data-product-custom-swatch') or '').strip()
            option = swatch.xpath(
                'ancestor::product-radio-option[@data-product-radio-option-name][1]'
            )
            value = self.text(swatch.xpath(
                './/*[contains(concat(" ", normalize-space(@class), " "), '
                '" color-swatch__tooltip ")]//text()'
            ))
            name = (option[0].get('data-product-radio-option-name') or '').strip() if option else ''
            if not target_id or not name or not value:
                continue
            if target_id == source_id:
                source_options[name] = value
            if not swatch.get('href'):
                continue
            target_handle = self.tool.URL.get_handle(
                self.tool.URL.add_site(swatch.get('href') or '')
            )
            if not target_handle:
                continue
            if target_handle not in handles:
                handles.append(target_handle)
            target_options.setdefault(target_handle, {})[name] = value
        return handles, source_options, target_options

    def linked_product_relationships(self, url, shopify_product):
        try:
            page_response = self.tool.get(url, timeout=20)
            if page_response.status_code != 200:
                raise ValueError(f'PDP returned {page_response.status_code}')
            return self.linked_swatch_metadata(page_response.text, shopify_product.get('id'))
        except Exception as exc:
            raise ValueError(f'Linked-swatch parse failed for {url}: {exc}') from exc


if __name__ == '__main__':
    Pc(
        tool=Tool, input_path=input_file, output_path=output_file,
        output_ts_file=output_ts_file, fail_file=fail_file,
        catch_path=catch_path, index_path=index_path, fieldnames=None,
        max_threads=2, if_wp=False,
    ).run()
    Tool.close()
