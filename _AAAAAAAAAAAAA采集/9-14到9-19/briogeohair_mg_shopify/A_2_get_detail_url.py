from config import Tool
from _ljp.mb.mg_shopify import GetDetail


file_path = Tool.File.path_add_site("data/ml.json")
save_path = Tool.File.path_add_site("data/detail_url.json")
catch_path = Tool.File.path_add_site("hc/2/data.json")
index_path = Tool.File.path_add_site("hc/2/index.json")

ts_num = None
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
catch_save_num = None


class Pc(GetDetail):
    def storefront_settings(self):
        return {
            "storefront_token": "60385688208d54f843f3c3cb36d767b2",
            "store_domain": "briogeo-hair-care.myshopify.com",
            "api_version": "2025-04",
            "country": "US",
            "language": "EN",
            "request_delay": 7,
        }


if __name__ == "__main__":
    Pc(
        tool=Tool,
        input_path=file_path,
        output_path=save_path,
        catch_path=catch_path,
        index_path=index_path,
        ts_num=ts_num,
        flush=flush,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        catch_save_num=catch_save_num,
    ).run()
