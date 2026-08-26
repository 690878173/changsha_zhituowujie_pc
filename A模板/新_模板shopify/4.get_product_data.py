import time
from config import Tool

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')

fail_file = Tool.File.path_add_site('dail/4.json')
# NOTE 缓存策略
index_path = Tool.File.path_add_site('hc/4/index.json')
catch_path = Tool.File.path_add_site('hc/4/catch.json')
catch_save_num = None

skip_input_url_ls = []
skip_output_url_ls = []
# 默认使用fieldnames=None,自动写入自定义字段，需要控制字段写入由下游控制，这里保留所有字段
fieldnames = None

ts_num = None
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Accept": "application/json"
}
cookies = {
    "localization": "US",
    "cart_currency": "USD",
    "_shopify_y": "dabb39cc-bc89-497c-b340-31b2ede021e3",
    "_shopify_analytics": ":AZp2O1QkAAEAHztC69G-yFNChK1vfflUWudV0AhpFiNR6FOoG0JYh1QIeFwE0AplJXKB:",
    "__kla_id": "eyJjaWQiOiJZelJsTnpnNFltSXRaV1ZqWlMwMFkyUTNMV0ppTW1FdFkyUTJNalUxTVdFNE5XWTMifQ==",
    "_dcid": "dcid.1.1762920201737.993685852",
    "_fbp": "fb.1.1762920201752.1616510929",
    "_gtmeec": "e30%3D",
    "_ga": "GA1.1.360526338.1762920202",
    "FPID": "FPID2.2.gkxOzZt5mIdu%2BjM%2FENk%2BINUWEC8WFAK8VJr7qv9DiMI%3D.1762920202",
    "FPAU": "1.2.1363690192.1762920202",
    "_clck": "8r5450%5E2%5Eg13%5E0%5E2142",
    "FPLC": "LgBR2ZulVErPIfYUSJlzshz28PHJYpcZjaf0ttgQ%2BOKvoX%2FTytpvBT1gw9f8w3Skoaoji%2FPT80R%2BxMChx7HVjW9Jmb0vQwpLwbP7lGJTdH2cpIAbSo3WEf43r4%2BDBA%3D%3D",
    "_shg_session_id": "ee3abf4f-7d71-4f24-b659-5c90de46503d",
    "_shg_user_id": "b36c7c32-f288-42a9-b521-223b4178e2b3",
    "wishlist_id": "165828310s5ibxs5m1i",
    "bookmarkeditems": "{\"items\":[]}",
    "wishlist_customer_id": "0",
    "lantern": "34e4017a-dcd0-44ea-86cc-510f559707fd",
    "_ks_scriptVersionChecked": "true",
    "_ks_userCountryUnit": "0",
    "_ks_countryCodeFromIP": "US",
    "_shopify_essential": ":AZp2O1QXAAEAvyFsaVJ70tJgji5ZeWCZ_YjgxwRXjGxAB3b5N-WHhSnud69tQW0MrpYjCka6b3GqbBhR9Uz4BhF9KODipC_2NFZRmCTQFTmhAMAjGv-jGy4tjy0FmTHMickaBcTQYB9gyNeGMX1T3ZL2JQ1P2sZLYPZwXL-juXGHSYiFqr2Gmc3jlKNMgPuEzv0pxSUVdolOYxCzcSwmJ_JEgKtrg_dwrLM_tp1SdVStXGVGDxfT27-4a1Fn6pKOttW0ZLW4JluB7XDeVv2VuUk-0l_ZIXlIrOu1450YtgeUvAjU3fGxv8SJbsptfgcU-GQ7NmT1Nravs3DmiiAUo2_zvYu9sk8dE3QuA-QodGbtyvFwsh4qzVoX5oLuEgUKhsFrxGP3Le-BVpm8PXsJjtIp7D18HUY:",
    "_clsk": "z0wknv%5E1763344068385%5E8%5E1%5Es.clarity.ms%2Fcollect",
    "_shopify_s": "73b24c0d-a8d4-4416-9886-da6ff48b97ce",
    "_uetsid": "94037020c35611f0b6b471d9a3ac75ef",
    "_uetvid": "8406dea0bf7c11f089889339b77b1953",
    "FPGSID": "1.1763343715.1763344093.G-QSD4N22KEF.mFsL74_ybyYhfff-E83nSQ",
    "_ga_QSD4N22KEF": "GS2.1.s1763343714$o2$g1$t1763344100$j51$l0$h694839178",
    "kiwi-sizing-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI4YTliMTk0ZC1iZmY3LTQ3OTktYjMwYS01Zjc1ZWZjMGVjMjIiLCJpYXQiOjE3NjMzNDQxNDYsImV4cCI6MTc2MzM0Nzc0Nn0.6kThd-lf6VF4L_1otBoH8nlTuH0z9Nw5nF0akbIs4UU",
    "keep_alive": "eyJ2IjoyLCJ0cyI6MTc2MzM0NDE5NDYzOSwiZW52Ijp7IndkIjowLCJ1YSI6MSwiY3YiOjEsImJyIjoxfSwiYmh2Ijp7Im1hIjo2NCwiY2EiOjAsImthIjowLCJzYSI6Mywia2JhIjowLCJ0YSI6MCwidCI6MTEyLCJubSI6MSwibXMiOjAuNjMsIm1qIjowLjMyLCJtc3AiOjAuMzUsInZjIjowLCJjcCI6MCwicmMiOjAsImtqIjowLCJraSI6MCwic3MiOjAuMDEsInNqIjowLjAxLCJzc20iOjEsInNwIjoxLCJ0cyI6MCwidGoiOjAsInRwIjowLCJ0c20iOjB9LCJzZXMiOnsicCI6NSwicyI6MTc2MzM0MzcwNDY0MSwiZCI6NDgzfX0%3D"
}

if_wp = False
time_sleep = 7

from _ljp.mb.shopify import Step4
class Pc(Step4):


    def zdy_zd(self,url):
        '''返回字典格式'''
        pass

    def fetch_product(self, url, category) -> list:
        Tool = self.tool
        handle = Tool.URL.get_handle(url)

        p_url = f"https://www.{Tool.site}.com/products/{handle}.json"

        try:
            r = Tool.get(p_url, headers=headers,cookies=cookies,timeout=15)

            if r.status_code == 404:
                return []
            data = r.json()

            #TODO 使用原url还是   p_url.replace('.json', '')

            zdy_data = self.zdy_zd(url)

            time.sleep(time_sleep)

            shopify_product = data.get("product")

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