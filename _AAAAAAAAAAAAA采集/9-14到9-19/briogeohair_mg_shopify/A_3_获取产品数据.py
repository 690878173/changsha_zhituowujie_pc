from lxml import etree

from config import Tool
from _ljp.mb.mg_shopify import Get_Product


input_file = Tool.File.path_add_site("data/detail_url.json")
output_file = Tool.File.path_add_site("res/result.csv")
output_ts_file = Tool.File.path_add_site("res/ts_res.csv")
fail_file = Tool.File.path_add_site("fail/4.json")
index_path = Tool.File.path_add_site("hc/4/index.json")
catch_path = Tool.File.path_add_site("hc/4/catch.json")

catch_save_num = None
skip_input_url_ls = []
skip_output_url_ls = []
fieldnames = None
ts_num = None
if_wp = False


class Pc(Get_Product):
    def storefront_settings(self):
        return {
            "storefront_token": "60385688208d54f843f3c3cb36d767b2",
            "store_domain": "briogeo-hair-care.myshopify.com",
            "api_version": "2025-04",
            "country": "US",
            "language": "EN",
            "request_delay": 7,
        }

    def zdy_zd(self, url, html_text=None):
        """返回 GraphQL 未提供的站点自定义字段。"""

        res = Tool.get(url)
        html = etree.HTML(res.text)

        Tool.HTML.save(res.text)
        dic = {}
        for node in html.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' accordion-item ')]/div/div"):
            name = node.xpath('./div/p/text()')[0]

            for i in ['how to use', 'claims',"who it's good for",'key benefits']:
                if i in name:
                    value = node.xpath('./div')[1]
                    dic[name] = Tool.HTML.clean_product_desc(value)
                    break

        return dic


if __name__ == "__main__":
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
