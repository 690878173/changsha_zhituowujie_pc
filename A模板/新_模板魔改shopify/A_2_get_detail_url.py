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
        # 站点专有信息只放在 Step 接口中，不污染 Tool.config。
        return {
            "storefront_token": "ef1b9f624c705ea7623f3c2b31924b44",
            "store_domain": "turtle-beach-usa.myshopify.com",
            "api_version": "2023-07",
            "country": "US",
            "language": "EN",
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
