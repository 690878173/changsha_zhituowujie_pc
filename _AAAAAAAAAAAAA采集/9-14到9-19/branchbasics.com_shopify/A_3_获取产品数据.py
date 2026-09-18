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
    'dwanonymous_9e217e72155e462deb87a243583f0211': 'abxkrQlPHBqYtBlNjf98UKH7Zs',
    '_pxvid': '5aabeb8a-b1c4-11f1-ac58-f466040a152b',
    'BVBRANDID': '026d96d1-04d2-48c9-917d-8cc6832f7aec',
    '_ga': 'GA1.1.791139228.1789559238',
    '__pxvid': '5e9f7501-b1c4-11f1-ae7e-8615022b3d2a',
    '__kla_id': 'eyJjaWQiOiJaV1k1WTJFelpUZ3RPVE15TkMwMFpXRXdMV0k1TWpNdFlUQXpZelV4TkRVMll6QXoifQ==',
    '_pin_unauth': 'dWlkPU5qZzFNVEU1WmpFdE1qbGtNaTAwWkdRMUxXSXhabVl0T0RNNU16RXhNV1ZtTW1VMw',
    'tangiblee:widget:user': '7b65f4d5-59d4-40ea-b171-aff0d1bd23c0',
    '__cq_dnt': '1',
    'dw_dnt': '1',
    'BVImplmain_site': '17643',
    'tangiblee_widget_container_type': 'OVL%2CEMB',
    'sid': 'aMkpFaPQKxjJSRn9hyceMhX1PHDTOhQVb0M',
    'dwsid': 'm9H4VolK261Bjb8igdY1Lebt7TP5oOSg54c9cJpKwlt-o4DuDV5zB_uc4sqn04ywXn7Lrs7tn6AWkp0ajEZdjg==',
    '_pxhd': 'cGMVVQYqQts2tMMWOdbSfnBzIrAo9rf0X4Am0JwbEEvf7E1v1QjeKvMoAW4YCndtXl7pZ6c5cvl4QUjd3uB/tw==:QI4gHb591Sq17I22KBZPXd6Y4jHpTLnw-FaA1WcQhCUyIOBkkhJIhIY5ZAUmyJUszxhd0tPgUQ9uKgIpLc7CE3Qe/ldWEhUpnk0vvzktBJU=',
    'BVBRANDSID': '4779fdc9-4efb-4613-a0c0-c1adfbd920f5',
    '_px3': 'e3419c2fd69d27f4784144fb2b7447d4d3756fb2defc83b7975366a670785337:bbqI5FSoXanZQrTeS9zWzIAkOkr3/adY9n/DASw/f4JRJTwVURuRNiyrgMld089T3RDfeWJs02z4H9NH7bPmjQ==:1000:SoV9Jx2PCZUl9H9dFfXHmjNK6JdeDH6SahSQzc5nNwUSAPXcplT/oFNk/Kve+CqEqj8YD8Mmo1cdqr/2hyxIY2cCzuSeANBTLciMwnOQiKhgOT5MTJmxf7CLYOffqbn682JPdA0fAyq1Lcp+p21jrvks5aH/ixf7FaNLwiFEniQL5mFyHuaoLbrvRG1zBL1ukOzVY3zNHYNZLAqnTUP3PRiUYML0CoIeXWT74VvIuugQ4jF9ewQ7GSoGQmfu5GXIsXzG34fFvaep5m/oetTfT0J5mfsgLfazzN1EQc4oK5yK23bebKNaPz+kNt0Qk3d0jG+MLRVaTCahnDiedQhcEReRG6IYijue/K9dZJmybU4PDt8w0eVpZ7PkIfmamJgxEErwqW1EDB3Gg0ka8NJtxBcKv8Jn/htwqge7GfGjZ1rVprF3ADCIBL9tjZ0SrH0kaEeVdbZkPziwaFggFFaa71Wh4LfcWgvKZDvoPRuKK1AFRbgAfTaI85023wAlAwos',
    '_px2': 'eyJ1IjoiZTExMmY4MjAtYjI4NC0xMWYxLWI5ZDktMDFmMDExMGYxZDVmIiwidiI6IjVhYWJlYjhhLWIxYzQtMTFmMS1hYzU4LWY0NjYwNDBhMTUyYiIsInQiOjE1NjE1MDcyMDAwMDAsImgiOiI1YjY2ZWUwNWJjMWUxYjQwOGI3M2I5ZWE1YTE0YjczMDY4N2JiMGM3Zjk5OGM5YzJjNDNhMjJmMGEyYTlhYWJlIn0=',
    '_gcl_au': '1.1.677058698.1789559236.-.-.1789643582.1348748235.1789643583.1789643582',
    '_ga_8J57WZMVZ7': 'GS2.1.s1789641922$o5$g1$t1789643618$j7$l0$h0',
    'pxcts': 'rxgdAudfSJfZLfx3m6aJeJ8RQvcpyIPFu/iVcaFOmGI=:QMlRlCk8zmsgeSeU83OGr9xNV3baDQpHqt0WQ8fzFw1ecGlheV337nlp4waQur07WNUFnf-1S03AlEpAW36CksKV0MsHeiP-F2moS0wcrXgYp0IYiiXcOgEcJbUVsEQmYPu0vX4Y7b6aMipy-5V/J4j9ZCtyKBPPWFXL-sm3UnaLq1PPZ-Vfo0i5juvOjtgU',
    '_ga_JQYB8ZRNS5': 'GS2.1.s1789641923$o5$g1$t1789643646$j41$l0$h0',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://shop.samsonite.com/collections/elevation%E2%84%A2-plus/',
    'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
    # 'cookie': 'dwanonymous_9e217e72155e462deb87a243583f0211=abxkrQlPHBqYtBlNjf98UKH7Zs; _pxvid=5aabeb8a-b1c4-11f1-ac58-f466040a152b; BVBRANDID=026d96d1-04d2-48c9-917d-8cc6832f7aec; _ga=GA1.1.791139228.1789559238; __pxvid=5e9f7501-b1c4-11f1-ae7e-8615022b3d2a; __kla_id=eyJjaWQiOiJaV1k1WTJFelpUZ3RPVE15TkMwMFpXRXdMV0k1TWpNdFlUQXpZelV4TkRVMll6QXoifQ==; _pin_unauth=dWlkPU5qZzFNVEU1WmpFdE1qbGtNaTAwWkdRMUxXSXhabVl0T0RNNU16RXhNV1ZtTW1VMw; tangiblee:widget:user=7b65f4d5-59d4-40ea-b171-aff0d1bd23c0; __cq_dnt=1; dw_dnt=1; BVImplmain_site=17643; tangiblee_widget_container_type=OVL%2CEMB; sid=aMkpFaPQKxjJSRn9hyceMhX1PHDTOhQVb0M; dwsid=m9H4VolK261Bjb8igdY1Lebt7TP5oOSg54c9cJpKwlt-o4DuDV5zB_uc4sqn04ywXn7Lrs7tn6AWkp0ajEZdjg==; _pxhd=cGMVVQYqQts2tMMWOdbSfnBzIrAo9rf0X4Am0JwbEEvf7E1v1QjeKvMoAW4YCndtXl7pZ6c5cvl4QUjd3uB/tw==:QI4gHb591Sq17I22KBZPXd6Y4jHpTLnw-FaA1WcQhCUyIOBkkhJIhIY5ZAUmyJUszxhd0tPgUQ9uKgIpLc7CE3Qe/ldWEhUpnk0vvzktBJU=; BVBRANDSID=4779fdc9-4efb-4613-a0c0-c1adfbd920f5; _px3=e3419c2fd69d27f4784144fb2b7447d4d3756fb2defc83b7975366a670785337:bbqI5FSoXanZQrTeS9zWzIAkOkr3/adY9n/DASw/f4JRJTwVURuRNiyrgMld089T3RDfeWJs02z4H9NH7bPmjQ==:1000:SoV9Jx2PCZUl9H9dFfXHmjNK6JdeDH6SahSQzc5nNwUSAPXcplT/oFNk/Kve+CqEqj8YD8Mmo1cdqr/2hyxIY2cCzuSeANBTLciMwnOQiKhgOT5MTJmxf7CLYOffqbn682JPdA0fAyq1Lcp+p21jrvks5aH/ixf7FaNLwiFEniQL5mFyHuaoLbrvRG1zBL1ukOzVY3zNHYNZLAqnTUP3PRiUYML0CoIeXWT74VvIuugQ4jF9ewQ7GSoGQmfu5GXIsXzG34fFvaep5m/oetTfT0J5mfsgLfazzN1EQc4oK5yK23bebKNaPz+kNt0Qk3d0jG+MLRVaTCahnDiedQhcEReRG6IYijue/K9dZJmybU4PDt8w0eVpZ7PkIfmamJgxEErwqW1EDB3Gg0ka8NJtxBcKv8Jn/htwqge7GfGjZ1rVprF3ADCIBL9tjZ0SrH0kaEeVdbZkPziwaFggFFaa71Wh4LfcWgvKZDvoPRuKK1AFRbgAfTaI85023wAlAwos; _px2=eyJ1IjoiZTExMmY4MjAtYjI4NC0xMWYxLWI5ZDktMDFmMDExMGYxZDVmIiwidiI6IjVhYWJlYjhhLWIxYzQtMTFmMS1hYzU4LWY0NjYwNDBhMTUyYiIsInQiOjE1NjE1MDcyMDAwMDAsImgiOiI1YjY2ZWUwNWJjMWUxYjQwOGI3M2I5ZWE1YTE0YjczMDY4N2JiMGM3Zjk5OGM5YzJjNDNhMjJmMGEyYTlhYWJlIn0=; _gcl_au=1.1.677058698.1789559236.-.-.1789643582.1348748235.1789643583.1789643582; _ga_8J57WZMVZ7=GS2.1.s1789641922$o5$g1$t1789643618$j7$l0$h0; pxcts=rxgdAudfSJfZLfx3m6aJeJ8RQvcpyIPFu/iVcaFOmGI=:QMlRlCk8zmsgeSeU83OGr9xNV3baDQpHqt0WQ8fzFw1ecGlheV337nlp4waQur07WNUFnf-1S03AlEpAW36CksKV0MsHeiP-F2moS0wcrXgYp0IYiiXcOgEcJbUVsEQmYPu0vX4Y7b6aMipy-5V/J4j9ZCtyKBPPWFXL-sm3UnaLq1PPZ-Vfo0i5juvOjtgU; _ga_JQYB8ZRNS5=GS2.1.s1789641923$o5$g1$t1789643646$j41$l0$h0',
}

if_wp = False
time_sleep = 2

from _ljp.mb.shopify import Get_Product


class Pc(Get_Product):

    def zdy_zd(self, url):
        '''返回字典格式'''
        res = Tool.get(url)
        html = etree.HTML(res.text)

        Tool.HTML.save(res.text)
        dic = {}
        for node in html.xpath('//div[@data-component="accordion"]'):
            name = node.xpath('./div/h3/button/span/text()')
            if not name:
                continue

            name = name[0]

            for i in ['How To Use', 'Ingredients']:
                if i in name:
                    value = node.xpath('./div')[1]
                    dic[i] = Tool.HTML.clean_product_desc(value)
                    break

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

            try:
                zdy_data = self.zdy_zd(url)
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
