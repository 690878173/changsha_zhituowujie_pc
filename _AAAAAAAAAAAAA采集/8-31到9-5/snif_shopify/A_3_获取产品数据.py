import time

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
cookies = {
    'localization': 'US',
    'cart_currency': 'USD',
    '_shopify_y': '2fe79cd4-1ec9-4e60-a16b-0cb38bb4fe64',
    '_shopify_analytics': ':AaA8vDlHAAEA2ihsWxYdrbajazw6JNIKW-2JAof4VdznbjIYNqRNmaui1Lf-hrXW0VlBlfiQCr2zt_lhixKTh0Y-G64wByke23updsblmJy_jIeqkPDQABVHPZ6Bd1Ba4N-Iy4jgnXwJUhQW:',
    '_shopify_marketing': ':AaA8vDlIAAEAGO-0Q2xVL3JKoDsqi8Gnnqey4Qd-6JpHXianxVJt-MkdCRZ9PFdsVvTfIda789nXi1lZoBg8WSPlQA-TnvZZ-Mih61XhSFM4Lh7uOKOwBrqyaFeUJIby5VpF:',
    '_ga': 'GA1.1.483868149.1787725366',
    'ugc_vid_3eb67891-0917-45db-87f4-fe8f75b15677': 'ad3933e7-af6b-471a-9e25-02f2ab93e254',
    'storefront_url': 'https://snif.co',
    'shopify_client_id': '2fe79cd4-1ec9-4e60-a16b-0cb38bb4fe64',
    '_ps_site_visit': 'true',
    '__kla_id': 'eyJjaWQiOiJZamc1T0daa09UQXROalJsT0MwMFlUSTVMVGxtWXpBdE5UTmxNV015WXpoaVl6WTEifQ==',
    'cart': 'hWNG5hku5G5ybRWpjTm0FuSO%3Fkey%3D56d80b2eefafeba93707b88a79675234',
    '_ps_unique_impression_2e208963-d9ac-474f-ae98-767591bfafb8': 'true',
    '_shopify_s': '978b81bf-118e-4a3a-b2e7-f512ca03da60',
    '_nb_sp_ses.9d4a': '*',
    '_nb_sp_ses.4209': '*',
    '_ama': '483868149.1787725366',
    'first_pla_call': 'none',
    '_ps_session': 'jiqTQIvIeYgoS_Cueld9S',
    '_ps_pop_2e208963-d9ac-474f-ae98-767591bfafb8': 'r',
    '_nb_sp_id.9d4a': 'e25a54fa-c5ea-423d-80f5-b261420fd80c.1787725366.2.1788164811.1787725366.ba6ca736-eb94-4468-8f06-6f0dda7a1627',
    '_ga_CE4NYPT0L3': 'GS2.1.s1788161489$o2$g1$t1788164811$j49$l0$h0',
    '_pin_unauth': 'dWlkPVl6QTJOVEZrTURVdFltWXlOaTAwTUdJMUxUaG1OakV0WlRjM1l6WXlZVGxsT0dFdw',
    '_shopify_essential': ':AaA8vDkuAAEAgBCEC1P21oBV_TJKSYpRStUMhzrDD7dwzgLbuw6f2rqNf05B1dWSQC75SmwOP1DRG67M_phz0u3dh0cjMd_rJsZZ51w1mnpY_PrUVf4N_h1ASqFIB3sBqQUUcygmAWz4GTF347KzgraYX4NUIlvjNNapIa7cqyk32vJRz9vT3Z9EH9qFmBbifJvLTG7bUOdFp5yU4wVMEcZ0DWu5NbPX18vbz1RKzxtqXz5iZ_9ng6NwCc_CO5poxoKRYvusHsyh63N9hqCybXZ-djhR2fkOQmRhLQlsNjRQYwiLznueuxevQv7Jdswoe0616nxWehEn-1X5NZmukdZ5t9cS9NJj8rbeXKUC1OB0Yg5SRZFSjLtrrzygmgk3aX_vGj9qiaOXn-1lhquMRwp5cDEIdFNA4_EwIUPY9kJ2ZYCQsWK2CvMouFSwYb9i1tYu7VbZB-pFThyqkUY9GSZ3scvqD6Yy-Gc9fg-zqlepVedcpnYmb7RF6Uv1Mh_bHAMjdMSrug_pwqtG6BAMp-Qt586e716rl2dtnlNy9-Jf3byq90MVkVuXm3iLNZmLOLLeGJsSRQMFzPkY2ex3ku7oZSmpO-EOvNG-BctnMEqWsaTohXql1SAYG8sDkevxYSjn9rIxsB4OH8AnUZRfq7FwHDxbdXBZ4gtaTTS8ExaT-0KxXUmsSYRnXUD-o9UKsF3cXu5oaEcmimWTFKA28ZUPXvgVuHwqaK7OarDOZcYFm7vwFfR3GeZL5yHqIeiVuQtzD4Gynzcjc6G0BXNe4u_IDGomJ8GRqtUyBocO8OKo:',
    '_ps_session_site_visit': '%7B%22sessionId%22%3A%22d8c1b7fe-bcca-4655-a8d3-10c460607271%22%2C%22startTime%22%3A1788164828667%7D',
    '_dd_s': 'aid=05e20264-8276-41d7-b8b8-729447bebbb5&logs=1&id=cf5a0dc6-4891-44a8-b404-ed364bbd5511&created=1788164830735&expire=1788165730735',
    '_nb_sp_id.4209': 'ab308006-0d0f-4caf-afc0-c4107689d2a1.1787725369.2.1788164854.1787726599.0013189a-fe01-4929-b4b7-4d4506ab118b',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-viewport-width': '1912',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'localization=US; cart_currency=USD; _shopify_y=2fe79cd4-1ec9-4e60-a16b-0cb38bb4fe64; _shopify_analytics=:AaA8vDlHAAEA2ihsWxYdrbajazw6JNIKW-2JAof4VdznbjIYNqRNmaui1Lf-hrXW0VlBlfiQCr2zt_lhixKTh0Y-G64wByke23updsblmJy_jIeqkPDQABVHPZ6Bd1Ba4N-Iy4jgnXwJUhQW:; _shopify_marketing=:AaA8vDlIAAEAGO-0Q2xVL3JKoDsqi8Gnnqey4Qd-6JpHXianxVJt-MkdCRZ9PFdsVvTfIda789nXi1lZoBg8WSPlQA-TnvZZ-Mih61XhSFM4Lh7uOKOwBrqyaFeUJIby5VpF:; _ga=GA1.1.483868149.1787725366; ugc_vid_3eb67891-0917-45db-87f4-fe8f75b15677=ad3933e7-af6b-471a-9e25-02f2ab93e254; storefront_url=https://snif.co; shopify_client_id=2fe79cd4-1ec9-4e60-a16b-0cb38bb4fe64; _ps_site_visit=true; __kla_id=eyJjaWQiOiJZamc1T0daa09UQXROalJsT0MwMFlUSTVMVGxtWXpBdE5UTmxNV015WXpoaVl6WTEifQ==; cart=hWNG5hku5G5ybRWpjTm0FuSO%3Fkey%3D56d80b2eefafeba93707b88a79675234; _ps_unique_impression_2e208963-d9ac-474f-ae98-767591bfafb8=true; _shopify_s=978b81bf-118e-4a3a-b2e7-f512ca03da60; _nb_sp_ses.9d4a=*; _nb_sp_ses.4209=*; _ama=483868149.1787725366; first_pla_call=none; _ps_session=jiqTQIvIeYgoS_Cueld9S; _ps_pop_2e208963-d9ac-474f-ae98-767591bfafb8=r; _nb_sp_id.9d4a=e25a54fa-c5ea-423d-80f5-b261420fd80c.1787725366.2.1788164811.1787725366.ba6ca736-eb94-4468-8f06-6f0dda7a1627; _ga_CE4NYPT0L3=GS2.1.s1788161489$o2$g1$t1788164811$j49$l0$h0; _pin_unauth=dWlkPVl6QTJOVEZrTURVdFltWXlOaTAwTUdJMUxUaG1OakV0WlRjM1l6WXlZVGxsT0dFdw; _shopify_essential=:AaA8vDkuAAEAgBCEC1P21oBV_TJKSYpRStUMhzrDD7dwzgLbuw6f2rqNf05B1dWSQC75SmwOP1DRG67M_phz0u3dh0cjMd_rJsZZ51w1mnpY_PrUVf4N_h1ASqFIB3sBqQUUcygmAWz4GTF347KzgraYX4NUIlvjNNapIa7cqyk32vJRz9vT3Z9EH9qFmBbifJvLTG7bUOdFp5yU4wVMEcZ0DWu5NbPX18vbz1RKzxtqXz5iZ_9ng6NwCc_CO5poxoKRYvusHsyh63N9hqCybXZ-djhR2fkOQmRhLQlsNjRQYwiLznueuxevQv7Jdswoe0616nxWehEn-1X5NZmukdZ5t9cS9NJj8rbeXKUC1OB0Yg5SRZFSjLtrrzygmgk3aX_vGj9qiaOXn-1lhquMRwp5cDEIdFNA4_EwIUPY9kJ2ZYCQsWK2CvMouFSwYb9i1tYu7VbZB-pFThyqkUY9GSZ3scvqD6Yy-Gc9fg-zqlepVedcpnYmb7RF6Uv1Mh_bHAMjdMSrug_pwqtG6BAMp-Qt586e716rl2dtnlNy9-Jf3byq90MVkVuXm3iLNZmLOLLeGJsSRQMFzPkY2ex3ku7oZSmpO-EOvNG-BctnMEqWsaTohXql1SAYG8sDkevxYSjn9rIxsB4OH8AnUZRfq7FwHDxbdXBZ4gtaTTS8ExaT-0KxXUmsSYRnXUD-o9UKsF3cXu5oaEcmimWTFKA28ZUPXvgVuHwqaK7OarDOZcYFm7vwFfR3GeZL5yHqIeiVuQtzD4Gynzcjc6G0BXNe4u_IDGomJ8GRqtUyBocO8OKo:; _ps_session_site_visit=%7B%22sessionId%22%3A%22d8c1b7fe-bcca-4655-a8d3-10c460607271%22%2C%22startTime%22%3A1788164828667%7D; _dd_s=aid=05e20264-8276-41d7-b8b8-729447bebbb5&logs=1&id=cf5a0dc6-4891-44a8-b404-ed364bbd5511&created=1788164830735&expire=1788165730735; _nb_sp_id.4209=ab308006-0d0f-4caf-afc0-c4107689d2a1.1787725369.2.1788164854.1787726599.0013189a-fe01-4929-b4b7-4d4506ab118b',
}

if_wp = False
time_sleep = 7

from _ljp.mb.shopify import Get_Product


class Pc(Get_Product):

    def zdy_zd(self, url):
        '''返回字典格式'''
        res = Tool.get(url)
        html = etree.HTML(res.text)
        #
        # Tool.HTML.save(res.text)
        dic = {}
        lis = html.xpath('//ul[@class="product__accordion"]/li')
        for li in lis:
            name = li.xpath('./button/h2/text()')
            name = ''.join(name).strip()
            if name:
                for i in ['Fine Fragrance-Level Scents','Non-toxic, Vegan Formulas','Room-filling + Extended burn','Candle Care']:
                    if i in name:
                        value = li.xpath('./div')[0]
                        dic[i] = Tool.HTML.clean_product_desc(value)
        return dic

    def fetch_product(self, url, category) -> list:
        Tool = self.tool
        handle = Tool.URL.get_handle(url)

        p_url = f"https://snif.co/products/{handle}.json"

        try:
            r = Tool.get(p_url, headers=headers,cookies=cookies,timeout=15, verify=False)

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