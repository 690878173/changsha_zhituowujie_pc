import time

from lxml import etree

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
cookies = {
    '__apex_test__': '',
    'localization': 'CN',
    'cart_currency': 'USD',
    '_shopify_y': 'f0e4b057-2967-4ab9-b2d5-0b180a1f8ce8',
    'hasVisited': 'true',
    'shopify_client_id': 'f0e4b057-2967-4ab9-b2d5-0b180a1f8ce8',
    '_ga': 'GA1.1.946634668.1787534220',
    '__kla_id': 'eyJjaWQiOiJabU13TnpjMllXVXRPVE5qWXkwMFlUaGtMVGxqWXpNdE1EVmtaalptWlRnME1HTmgifQ==',
    '_rdt_uuid': '1787534220921.b2bf27cb-a7d3-44e7-8f68-a3f1d002b735',
    '__ps_slu': 'https://www.american-giant.com/',
    '__ps_sr': '_',
    '__ps_lu_query': '{}',
    '__ps_lu': 'https://www.american-giant.com/',
    '__ps_did': 'f170cd28-6f7d-4d6b-a228-601c72b2b3ab',
    '__spdt': 'b59f90b823bb4f6180389454309f4a69',
    '_fbp': 'fb.1.1787534221693.7069826436',
    '_hjSessionUser_292067': 'eyJpZCI6ImYwNTk3NGEyLWUxNGEtNTA2Ni1hZjIxLTM3YTYyZDQxYTVhNiIsImNyZWF0ZWQiOjE3ODc1MzQyMjIxOTksImV4aXN0aW5nIjp0cnVlfQ==',
    '_shopify_analytics': ':AaAxV460AAEADDyXJldPTQF8-xNMQvyLWs0En6X4dKVq_W_YEmUzOYw7SPE_ZSVtj_R8dBOrsf5uCt3gaeddCyLoD1I7YZr7UYS_ip1GXYpF659__1uu3Xe1PEUF2owdqUWVifzemi4mO1s:',
    '_shopify_marketing': ':AaAxV461AAEA6vOQTTjqNXbu_6DXBAt0u7maKpKZQogsn4-ax5JifmrmDnJCnRQKnEjLnHp00LELYcxz7sI5Z39lv-riYTFvlNxGNVhGXO8Y66wJQO9owOHFk_u8Qlgv6Knu9wJzIak0y2BijqJ3CT8c5cA:',
    '_ttp': '01M0RNGZX4VAHXDAE8J8HFBV0Q_.tt.0',
    '_scid': 'PbY7wxruGZZSXFTnVX21JlPL91tYdOyq',
    '_sctr': '1%7C1787500800000',
    '_svsid': '953802c976ffddc363e2657697a19dbf',
    '_lc2_fpi': '4b6e8ba82db0--01m0rnh4fby64zwcmxd3zz27cy',
    'rbuid': 'rbos-4dfb5865-68af-47f3-bb13-3c4e7f3afbe8',
    'addshoppers.com': '2%7C1%3A0%7C10%3A1787534285%7C15%3Aaddshoppers.com%7C44%3AMTM0MDE4Y2M4YWU5NGM4YzgwZTUyODQyYTVjNTBlMzQ%3D%7Cc1436215f39fb94c35c1959707853e5782cf27460bed8de9506b7950ec0e7c3f',
    '_shopify_s': '158b9df6-6ac6-46f2-b811-bb038c65db36',
    '__ps_fva': '1787551312115',
    'yotpo_pixel': '9524bff8-4b13-4636-877d-4477002921c8',
    '_sp_ses.2712': '*',
    '_hjSession_292067': 'eyJpZCI6IjVjODk3NWNjLTM0ZGMtNDBlMy05YWZhLTdkZDI3NzY5ZDA0NiIsImMiOjE3ODc1NTEzMTQyNDgsInMiOjEsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MX0=',
    'builderSessionId': '8b3c390def614482b57dff637fbaf5ef',
    '_li_dcdm_c': '.american-giant.com',
    '_lc2_fpi_js': '4b6e8ba82db0--01m0rnh4fby64zwcmxd3zz27cy',
    'builder.userAttributes': '{"urlPath":"/","host":"www.american-giant.com","device":"desktop","customerType":"returning"}',
    'builderSessionId': '8b3c390def614482b57dff637fbaf5ef',
    '__apex_test__': '',
    'dicbo_id': '%7B%22dicbo_fetch%22%3A1787551983645%7D',
    '_ga_VY113HX0GN': 'GS2.1.s1787551313$o3$g1$t1787551996$j44$l0$h0',
    'ttcsid_C8EMOP908UUP07H0LQJG': '1787551312512::exDsVpp7CrwnOBvfCEbe.2.1787551997380.0',
    'ttcsid': '1787551312515::J2cDaIAy2gCQbtPj-Ufy.2.1787551997386.0',
    '_ga_PEGGHXQ82W': 'GS2.1.s1787551313$o3$g1$t1787551997$j43$l0$h266771133',
    '_scid_r': 'SDY7wxruGZZSXFTnVX21JlPL91tYdOyqEGXCdg',
    '_sp_id.2712': '1fd2ff2d30d535f0.1787551314.1.1787552000.1787551314',
    '_gcl_au': '1.1.439817878.1787534220.-.-.1787534219.1172797109.1787534220.1787552001',
    '_shopify_essential': ':AaAxV44zAAEAbse1Q98wrm-Z7H0dgtWw8Z1trKIiag_OnUYlcuSLe86xLcpBYZhfMAkFYZYOz8ni3EqPPWL21KeOMueEMujGLJmZAAjJFRB0k1B8sSZm6acG9YasJmycNL99h0Iw-42sAxK_8VcFaIJQNmB7JUBazLjffYDg7viSf1fwIsfdYKKCAQA0DnAjIaO216T6Xtqo3SQGZWLsU4K4hNnDc3NBhgDwqwqX5VUvSyuWGw77bKHaRwQNrV4pGLxWI3UJRV0UY4vLOCHoGNgISia5VVBZqE5nujZlz1_yTJq_P8nAXI49Y19z8pB7FieJHxaj6tY8Co_xKLcQ0HYvdRO2JbzkeMkxGqzkIMC5RKM22YstDxr6oddRwmSsNnMYHx5wgOjiSw2LUPDKQnMH-DEYWaCjSpQhQz4s_EtIe3p2CnSmspkwUYsYriGFdrNoLPxTjaqLVwdJylaCXtzawj7krPAqsLp9D7e6diAR58eZ-IB9mX-wZvA1_JNsohLzR78YNRM3Bh0bZttyOU_c2b4ymdcPe2U5wu8bhbUUME-CmyrXB_baAILdI3t7bhb7omb-EZhggQ7aWMBEOWXf-cT3v6TXnsYxzSng1yAagCRswC9dvZCQ5mcjDysqyh9cFi2Z4tXS-vepPkPr5f-IwHJpASlmpRJsW_R5_haVzA:',
    '_uetsid': '9bc464a09f5911f189fff547a66ccc1c',
    '_uetvid': '9bc4a6f09f5911f18dd40fe22e3c3b51',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'max-age=0',
    'if-none-match': '"page_cache:8134492257:ProductDetailsController:7d50249f28754e4ee843ef104adbfdfd:36b676273fb29c017e76fa18871a751d"',
    'priority': 'u=0, i',
    'referer': 'https://www.american-giant.com/products/womens-linen-wide-leg-pant-cotton?pr_prod_strat=e5_desc&pr_rec_id=086ab9e25&pr_rec_pid=7653234835637&pr_ref_pid=8192541360309&pr_seq=uniform',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
    # 'cookie': '__apex_test__=; localization=CN; cart_currency=USD; _shopify_y=f0e4b057-2967-4ab9-b2d5-0b180a1f8ce8; hasVisited=true; shopify_client_id=f0e4b057-2967-4ab9-b2d5-0b180a1f8ce8; _ga=GA1.1.946634668.1787534220; __kla_id=eyJjaWQiOiJabU13TnpjMllXVXRPVE5qWXkwMFlUaGtMVGxqWXpNdE1EVmtaalptWlRnME1HTmgifQ==; _rdt_uuid=1787534220921.b2bf27cb-a7d3-44e7-8f68-a3f1d002b735; __ps_slu=https://www.american-giant.com/; __ps_sr=_; __ps_lu_query={}; __ps_lu=https://www.american-giant.com/; __ps_did=f170cd28-6f7d-4d6b-a228-601c72b2b3ab; __spdt=b59f90b823bb4f6180389454309f4a69; _fbp=fb.1.1787534221693.7069826436; _hjSessionUser_292067=eyJpZCI6ImYwNTk3NGEyLWUxNGEtNTA2Ni1hZjIxLTM3YTYyZDQxYTVhNiIsImNyZWF0ZWQiOjE3ODc1MzQyMjIxOTksImV4aXN0aW5nIjp0cnVlfQ==; _shopify_analytics=:AaAxV460AAEADDyXJldPTQF8-xNMQvyLWs0En6X4dKVq_W_YEmUzOYw7SPE_ZSVtj_R8dBOrsf5uCt3gaeddCyLoD1I7YZr7UYS_ip1GXYpF659__1uu3Xe1PEUF2owdqUWVifzemi4mO1s:; _shopify_marketing=:AaAxV461AAEA6vOQTTjqNXbu_6DXBAt0u7maKpKZQogsn4-ax5JifmrmDnJCnRQKnEjLnHp00LELYcxz7sI5Z39lv-riYTFvlNxGNVhGXO8Y66wJQO9owOHFk_u8Qlgv6Knu9wJzIak0y2BijqJ3CT8c5cA:; _ttp=01M0RNGZX4VAHXDAE8J8HFBV0Q_.tt.0; _scid=PbY7wxruGZZSXFTnVX21JlPL91tYdOyq; _sctr=1%7C1787500800000; _svsid=953802c976ffddc363e2657697a19dbf; _lc2_fpi=4b6e8ba82db0--01m0rnh4fby64zwcmxd3zz27cy; rbuid=rbos-4dfb5865-68af-47f3-bb13-3c4e7f3afbe8; addshoppers.com=2%7C1%3A0%7C10%3A1787534285%7C15%3Aaddshoppers.com%7C44%3AMTM0MDE4Y2M4YWU5NGM4YzgwZTUyODQyYTVjNTBlMzQ%3D%7Cc1436215f39fb94c35c1959707853e5782cf27460bed8de9506b7950ec0e7c3f; _shopify_s=158b9df6-6ac6-46f2-b811-bb038c65db36; __ps_fva=1787551312115; yotpo_pixel=9524bff8-4b13-4636-877d-4477002921c8; _sp_ses.2712=*; _hjSession_292067=eyJpZCI6IjVjODk3NWNjLTM0ZGMtNDBlMy05YWZhLTdkZDI3NzY5ZDA0NiIsImMiOjE3ODc1NTEzMTQyNDgsInMiOjEsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MX0=; builderSessionId=8b3c390def614482b57dff637fbaf5ef; _li_dcdm_c=.american-giant.com; _lc2_fpi_js=4b6e8ba82db0--01m0rnh4fby64zwcmxd3zz27cy; builder.userAttributes={"urlPath":"/","host":"www.american-giant.com","device":"desktop","customerType":"returning"}; builderSessionId=8b3c390def614482b57dff637fbaf5ef; __apex_test__=; dicbo_id=%7B%22dicbo_fetch%22%3A1787551983645%7D; _ga_VY113HX0GN=GS2.1.s1787551313$o3$g1$t1787551996$j44$l0$h0; ttcsid_C8EMOP908UUP07H0LQJG=1787551312512::exDsVpp7CrwnOBvfCEbe.2.1787551997380.0; ttcsid=1787551312515::J2cDaIAy2gCQbtPj-Ufy.2.1787551997386.0; _ga_PEGGHXQ82W=GS2.1.s1787551313$o3$g1$t1787551997$j43$l0$h266771133; _scid_r=SDY7wxruGZZSXFTnVX21JlPL91tYdOyqEGXCdg; _sp_id.2712=1fd2ff2d30d535f0.1787551314.1.1787552000.1787551314; _gcl_au=1.1.439817878.1787534220.-.-.1787534219.1172797109.1787534220.1787552001; _shopify_essential=:AaAxV44zAAEAbse1Q98wrm-Z7H0dgtWw8Z1trKIiag_OnUYlcuSLe86xLcpBYZhfMAkFYZYOz8ni3EqPPWL21KeOMueEMujGLJmZAAjJFRB0k1B8sSZm6acG9YasJmycNL99h0Iw-42sAxK_8VcFaIJQNmB7JUBazLjffYDg7viSf1fwIsfdYKKCAQA0DnAjIaO216T6Xtqo3SQGZWLsU4K4hNnDc3NBhgDwqwqX5VUvSyuWGw77bKHaRwQNrV4pGLxWI3UJRV0UY4vLOCHoGNgISia5VVBZqE5nujZlz1_yTJq_P8nAXI49Y19z8pB7FieJHxaj6tY8Co_xKLcQ0HYvdRO2JbzkeMkxGqzkIMC5RKM22YstDxr6oddRwmSsNnMYHx5wgOjiSw2LUPDKQnMH-DEYWaCjSpQhQz4s_EtIe3p2CnSmspkwUYsYriGFdrNoLPxTjaqLVwdJylaCXtzawj7krPAqsLp9D7e6diAR58eZ-IB9mX-wZvA1_JNsohLzR78YNRM3Bh0bZttyOU_c2b4ymdcPe2U5wu8bhbUUME-CmyrXB_baAILdI3t7bhb7omb-EZhggQ7aWMBEOWXf-cT3v6TXnsYxzSng1yAagCRswC9dvZCQ5mcjDysqyh9cFi2Z4tXS-vepPkPr5f-IwHJpASlmpRJsW_R5_haVzA:; _uetsid=9bc464a09f5911f189fff547a66ccc1c; _uetvid=9bc4a6f09f5911f18dd40fe22e3c3b51',
}

if_wp = False
time_sleep = 7

from _ljp.mb.shopify import Get_Product
class Pc(Get_Product):


    def zdy_zd(self,url):
        '''返回字典格式'''
        res = Tool.get(url, headers=headers,cookies=cookies)
        Tool.HTML.save(res.text)
        html = etree.HTML(res.text)

        dic = {}
        d_ls = html.xpath('//div[@class="pv-details__item"]')
        for d in d_ls:
            title = d.xpath('./button/h2/text()')[0]
            value = d.xpath('./div')[0]
            value1 = Tool.HTML.clean_product_desc(value)
            if 'Description' in title:
                # print(f'描述:{value1},原始描述:{Tool.HTML.to_str(value)}')
                dic['Description'] = value1
            elif 'Details' in title:
                dic['Details'] = value1

        return dic
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

            Description = zdy_data.pop('Description','')

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
        woo_product['Description'] = Description
        _products = [woo_product]
        variations = self.create_variation_products(shopify_product, woo_product)

        if variations:
            _products.extend(variations)


        return _products



if __name__ == '__main__':
    pc = Pc(
        tool=Tool,
        input_file=input_file,
        output_file=output_file,
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