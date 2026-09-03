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
        # 站点专有信息只放在 Step 接口中，不污染 Tool.config。
        return {
            "storefront_token": "ef1b9f624c705ea7623f3c2b31924b44",
            "store_domain": "turtle-beach-usa.myshopify.com",
            "api_version": "2023-07",
            "country": "US",
            "language": "EN",
            "request_delay": 7,
        }

    def zdy_zd(self, url, html_text=None):
        """返回 GraphQL 未提供的站点自定义字段。"""
        return {}


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
