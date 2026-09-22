import json
import time

from lxml import etree

from config import Tool

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')

fail_file = Tool.File.path_add_site('fail/4_linked_variants_v2.json')
# v2 records each target-link's resolved option combination.  Older entries
# only store the source page's selected values and cannot safely fill options
# hidden on a linked product page.
index_path = Tool.File.path_add_site('hc/4_linked_variants_v2/index.json')
catch_path = Tool.File.path_add_site('hc/4_linked_variants_v2/catch.json')
catch_save_num = None

skip_input_url_ls = ["https://www.maryruthorganics.com/products/gift-card"]
skip_output_url_ls = ["https://www.maryruthorganics.com/products/gift-card"]
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
time_sleep = 2

from _ljp.mb.shopify import Get_Product


class Pc(Get_Product):

    @staticmethod
    def _text(values):
        return ' '.join(' '.join(values).split())

    def linked_variant_data(self, html_text):
        """Read linked PDP swatches and resolve the option values of each target."""
        html = etree.HTML(html_text)
        handles = []
        selected_options = {}
        wrapper_data = []
        swatch_wrappers = html.xpath(
            '//*[contains(concat(" ", normalize-space(@class), " "), " swatch_wrapper ")]'
        )

        for wrapper in swatch_wrappers:
            title = self._text(wrapper.xpath(
                './preceding-sibling::div['
                'contains(concat(" ", normalize-space(@class), " "), " swatch-title-box ")'
                '][1]//h3/text()'
            )).rstrip(':')
            swatches = wrapper.xpath(
                './/*[contains(concat(" ", normalize-space(@class), " "), " swatch_item ")][@data-product]'
            )
            if not title or not swatches:
                continue

            active_value = ''
            choices = []
            for swatch in swatches:
                handle = (swatch.get('data-product') or '').strip()
                if handle and handle not in handles:
                    handles.append(handle)
                option_value = self._text(swatch.xpath('.//text()'))
                if handle and option_value:
                    choices.append((handle, option_value))
                classes = f" {(swatch.get('class') or '').strip()} "
                if ' active ' in classes:
                    active_value = option_value

            if not active_value:
                active_value = self._text(wrapper.xpath(
                    './preceding-sibling::div['
                    'contains(concat(" ", normalize-space(@class), " "), " swatch-title-box ")'
                    '][1]//span/text()'
                ))
            if active_value:
                selected_options[title] = active_value
            wrapper_data.append((title, active_value, choices))

        target_candidates = {}
        current_values = {
            title: value
            for title, value, _ in wrapper_data
            if value
        }
        for title, _, choices in wrapper_data:
            for handle, option_value in choices:
                values = dict(current_values)
                values[title] = option_value
                target_candidates.setdefault(handle, []).append(values)

        # A target can occur in more than one swatch wrapper.  Retain only
        # values every observation agrees on; disagreement means the page
        # does not expose enough information to infer that target option.
        target_options = {}
        for handle, candidates in target_candidates.items():
            option_names = {
                name
                for candidate in candidates
                for name, value in candidate.items()
                if value
            }
            values = {}
            for name in option_names:
                observed = {
                    candidate[name]
                    for candidate in candidates
                    if candidate.get(name)
                }
                if len(observed) == 1:
                    values[name] = observed.pop()
            if values:
                target_options[handle] = values

        return handles, selected_options, target_options

    def zdy_zd(self, url):
        '''Return parent custom fields plus the site's linked-product swatches.'''
        res = Tool.get(url)
        html = etree.HTML(res.text)

        Tool.HTML.save(res.text)
        dic = {}
        for node in html.xpath('//accordion-custom/details'):
            name = node.xpath('./summary/strong/text()')[0]

            for i in ['Benefits', 'How To Take','Important Disclaimer']:
                if i in name:
                    value = node.xpath('./div')[0]
                    dic[i] = Tool.HTML.clean_product_desc(value)
                    break

        linked_handles, linked_options, linked_target_options = self.linked_variant_data(res.text)
        return dic, linked_handles, linked_options, linked_target_options

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

            try:
                zdy_data, linked_handles, linked_options, linked_target_options = self.zdy_zd(url)
            except Exception as e:
                raise ValueError(f'自定义字段获取失败:{e}')

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
        # These columns are consumed and removed by A_3_5 before downstream export.
        woo_product['__linked_handles'] = json.dumps(linked_handles, ensure_ascii=False)
        woo_product['__linked_options'] = json.dumps(linked_options, ensure_ascii=False)
        woo_product['__linked_target_options'] = json.dumps(
            linked_target_options,
            ensure_ascii=False,
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
