import time

from lxml import etree

from config import Tool
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

        res = Tool.get(url)
        html = etree.HTML(res.text)

        Tool.HTML.save(res.text)
        dic = {}
        for node in html.xpath('//s-accordion/div'):
            name = node.xpath('./button/text()')
            if not name:
                continue
            else:
                name = name[0]

            for i in ['Description', 'Product Details','Care Instructions']:
                if i in name:
                    value = node.xpath('./div')[0]
                    dic[i] = Tool.HTML.clean_product_desc(value)
                    break
            else:
                for i in ['Warranty Details','About Us','Help','Where to Buy','Legal','Hard Coolers','Soft Coolers','Electric Coolers','Drinkware','Collabs','Featured']:
                    if i in name:
                        break
                else:

                    print(f'未知字段:{name}')

        return dic

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
