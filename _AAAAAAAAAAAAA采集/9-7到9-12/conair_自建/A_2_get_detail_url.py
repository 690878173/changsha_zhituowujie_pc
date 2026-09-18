from lxml import etree

from config import Tool

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')

catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

# 测试数据条数,以初始url数量计数
ts_num = None

# 排除某些 URL（输入分类黑名单）
skip_input_url_ls = []
# 输出商品链接黑名单
skip_output_url_ls = []

# 覆盖缓存：True=无视本地缓存强制重新请求
flush = False

catch_save_num = None

from _ljp.mb.model import PageModel
from _ljp.mb.zj import GetDetail


cookies = {
    'dwsid': 'PUeEi89avnu5o_ls0ZaaWWBzzIVQprRdZsJ8EEVO2A3Gj1FRZpaf7NWT4luUaimLMdS-tDyujDyswoRbCtGDvA==',
    'sid': '_E25i6MK4ovGTkH8kSmtDKF58YU89uitGS8',
    'dwanonymous_472d7a68ade4fc9505b4fb3556d571a0': 'abdOPQx49VA5NuPM7jtlNbDo12',
    '_pxhd': '98e6aed5222af19aec88bfe6ee18d48f232abb4683df3490052ad6fcd2b38ebd:8a2dc13a-ace1-11f1-af07-8573aadf94f8',
    '__cq_dnt': '1',
    'dw_dnt': '1',
    '__kla_id': 'eyJjaWQiOiJZek5sWXpaaE0yUXRNR0k0WmkwME5qY3pMV0U1TURJdE56bGtNREE0TXpoa1l6VXkifQ==',
    '_pxvid': '8a2dc13a-ace1-11f1-af07-8573aadf94f8',
    '__pxvid': '8c93574f-ace1-11f1-9f74-5e112df355ac',
    'BVBRANDID': 'd6ee111b-b594-4321-9a38-185660fa2ff0',
    'OptanonAlertBoxClosed': '2026-09-10T07:28:49.674Z',
    '_gcl_au': '1.1.1437494665.1789025330',
    '_ga': 'GA1.1.994945795.1789025324',
    '_nb_sp_ses.4902': '*',
    '_pin_unauth': 'dWlkPU5tWXpOak0wTmpVdE5qVTRZaTAwTW1Sa0xXSTBZelV0WkRKa04yVTNNV1V3T1RoaQ',
    '__kla_session': '%7B%22sessionId%22%3A%220122bab5-a2e1-4cda-8ba1-a9f0cf70e3c3%22%2C%22sentSessionStartedEvent%22%3Afalse%2C%22sentUserIdentifiedEvent%22%3Afalse%7D',
    'BVBRANDSID': '11d4a579-ebe8-4dc8-89dd-2fea9753b513',
    '_ga_ZWDWKYLBY3': 'GS2.1.s1789028219$o2$g1$t1789028292$j55$l0$h0',
    '_nb_sp_id.4902': '2d9c648f-8738-460c-a613-00aae61bcb24.1789025383.1.1789028293.1789025383.dbbb2edf-2945-4dd4-a0be-731bb931d10d',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Thu+Sep+10+2026+16%3A18%3A14+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202601.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d3433e11-0788-4f37-b9e0-aad16f732771&interactionCount=2&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=C0003%3A1%2CC0001%3A1%2CC0002%3A1%2CC0004%3A1%2CSPD_BG%3A1&crTime=1789025330607&AwaitingReconsent=false&intType=1&geolocation=US%3BCA',
    'pxcts': '4m9m3sgz-I49a7NxKtkTT2fShBD/8QR9Qhf7wv2ANOA=:hYqNu9RUBlx/DWcQDd/s7aAWC0E6wQK8-vUVTJzArOYbtDo8S6TdP8qPPNIhO0XbuImt7DILs1Ivnl7UmYxCWHfs04eA1BUR6WcbnpK7PtPELIuktJsF9Tx9abp4up657EvR9oHheHHw3YFePqSrs6DiQkqx4GxqCXd2xerIcT05gOxH2/GFR5zF7Si2MrZS',
    '_px3': '68d4c82775ada3d06b57ace4346669e578764608d47112acfe29abf4451a0f95:cS+GAoZkGUbpjIUJVjlWGl3CidbCmbSvIzN8gdli+P93j1Qgp+jfE4Mt9e9Kivrpcbq1dAfU/hh3lsdnwr5UTw==:1000:IRR/AaunihpAT6rPoJCZmKdGyzAsFVc8q48hzwAwElrRqQ6P1tR50LskPVZm9RPOEtwgQDTawgcKaXu4laXeqHm1xJoXotK/ran0Bj0u5al1dmbv106LgYyULp30gvUrw98NbgwEK1/MWukPmK+gRkCDt+Yofi33vvLYDSYivJVYG0guMu2tMcg3Y0a3J/7FAgEG3NBdoXR5fSjVD0GyG5JfuZv2TrolNcwct7jbhLAfzntX/g39zfjmSIIj2sOgsySBUijCSGIGzWSeUWCwEdyAeZN87saY9+ROYSq/ZyFs7/fR68yEPCGEFHWpH0/V8jo2vlXo7CsM1JmDAo0sj29HT06oUUITKdi3hXPURGRMC+3p93SuxdwfGozMOZrU3DquSLTvXPTzy7k25EFrTRbhW4aIOa89zr+ApzSto8dvetUR9rQ9iqGoxHZveQVeQXo1Rdc1EUsIxTTHsOu3L/jE9T8S4DCcxVsq/QNySOii0iYJ8SnsRbStlSubx1mEBLx1IX0Y3PMJbG8ZPz4CoKuA3/XKGWPFTQsdifhmcTI9qjjKPlTrIzifEKtSqk9L',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.conair.com/dryers-full-size?lang=en_US',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'dwsid=PUeEi89avnu5o_ls0ZaaWWBzzIVQprRdZsJ8EEVO2A3Gj1FRZpaf7NWT4luUaimLMdS-tDyujDyswoRbCtGDvA==; sid=_E25i6MK4ovGTkH8kSmtDKF58YU89uitGS8; dwanonymous_472d7a68ade4fc9505b4fb3556d571a0=abdOPQx49VA5NuPM7jtlNbDo12; _pxhd=98e6aed5222af19aec88bfe6ee18d48f232abb4683df3490052ad6fcd2b38ebd:8a2dc13a-ace1-11f1-af07-8573aadf94f8; __cq_dnt=1; dw_dnt=1; __kla_id=eyJjaWQiOiJZek5sWXpaaE0yUXRNR0k0WmkwME5qY3pMV0U1TURJdE56bGtNREE0TXpoa1l6VXkifQ==; _pxvid=8a2dc13a-ace1-11f1-af07-8573aadf94f8; __pxvid=8c93574f-ace1-11f1-9f74-5e112df355ac; BVBRANDID=d6ee111b-b594-4321-9a38-185660fa2ff0; OptanonAlertBoxClosed=2026-09-10T07:28:49.674Z; _gcl_au=1.1.1437494665.1789025330; _ga=GA1.1.994945795.1789025324; _nb_sp_ses.4902=*; _pin_unauth=dWlkPU5tWXpOak0wTmpVdE5qVTRZaTAwTW1Sa0xXSTBZelV0WkRKa04yVTNNV1V3T1RoaQ; __kla_session=%7B%22sessionId%22%3A%220122bab5-a2e1-4cda-8ba1-a9f0cf70e3c3%22%2C%22sentSessionStartedEvent%22%3Afalse%2C%22sentUserIdentifiedEvent%22%3Afalse%7D; BVBRANDSID=11d4a579-ebe8-4dc8-89dd-2fea9753b513; _ga_ZWDWKYLBY3=GS2.1.s1789028219$o2$g1$t1789028292$j55$l0$h0; _nb_sp_id.4902=2d9c648f-8738-460c-a613-00aae61bcb24.1789025383.1.1789028293.1789025383.dbbb2edf-2945-4dd4-a0be-731bb931d10d; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Sep+10+2026+16%3A18%3A14+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202601.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d3433e11-0788-4f37-b9e0-aad16f732771&interactionCount=2&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=C0003%3A1%2CC0001%3A1%2CC0002%3A1%2CC0004%3A1%2CSPD_BG%3A1&crTime=1789025330607&AwaitingReconsent=false&intType=1&geolocation=US%3BCA; pxcts=4m9m3sgz-I49a7NxKtkTT2fShBD/8QR9Qhf7wv2ANOA=:hYqNu9RUBlx/DWcQDd/s7aAWC0E6wQK8-vUVTJzArOYbtDo8S6TdP8qPPNIhO0XbuImt7DILs1Ivnl7UmYxCWHfs04eA1BUR6WcbnpK7PtPELIuktJsF9Tx9abp4up657EvR9oHheHHw3YFePqSrs6DiQkqx4GxqCXd2xerIcT05gOxH2/GFR5zF7Si2MrZS; _px3=68d4c82775ada3d06b57ace4346669e578764608d47112acfe29abf4451a0f95:cS+GAoZkGUbpjIUJVjlWGl3CidbCmbSvIzN8gdli+P93j1Qgp+jfE4Mt9e9Kivrpcbq1dAfU/hh3lsdnwr5UTw==:1000:IRR/AaunihpAT6rPoJCZmKdGyzAsFVc8q48hzwAwElrRqQ6P1tR50LskPVZm9RPOEtwgQDTawgcKaXu4laXeqHm1xJoXotK/ran0Bj0u5al1dmbv106LgYyULp30gvUrw98NbgwEK1/MWukPmK+gRkCDt+Yofi33vvLYDSYivJVYG0guMu2tMcg3Y0a3J/7FAgEG3NBdoXR5fSjVD0GyG5JfuZv2TrolNcwct7jbhLAfzntX/g39zfjmSIIj2sOgsySBUijCSGIGzWSeUWCwEdyAeZN87saY9+ROYSq/ZyFs7/fR68yEPCGEFHWpH0/V8jo2vlXo7CsM1JmDAo0sj29HT06oUUITKdi3hXPURGRMC+3p93SuxdwfGozMOZrU3DquSLTvXPTzy7k25EFrTRbhW4aIOa89zr+ApzSto8dvetUR9rQ9iqGoxHZveQVeQXo1Rdc1EUsIxTTHsOu3L/jE9T8S4DCcxVsq/QNySOii0iYJ8SnsRbStlSubx1mEBLx1IX0Y3PMJbG8ZPz4CoKuA3/XKGWPFTQsdifhmcTI9qjjKPlTrIzifEKtSqk9L',
}


class Pc(GetDetail):

    @staticmethod
    def _is_denied(html_text, url=''):
        text = (html_text or '').lower()
        return (
            'perimeterx' in text
            or 'access to this page has been denied' in text
            or 'px-show' in text
            or 'px-show' in (url or '').lower()
        )

    @staticmethod
    def _next_url(html):
        hrefs = html.xpath(
            '//a[@rel="next"]/@href | '
            '//li[contains(@class, "next") and not(contains(@class, "disabled"))]//a/@href | '
            '//a[contains(@class, "next") and not(@aria-disabled="true")]/@href | '
            '//a[contains(@aria-label, "Next") and not(@aria-disabled="true")]/@href'
        )
        return Tool.URL.add_site(hrefs[0]) if hrefs else None

    def fetch_page(self, P: PageModel, params):
        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空或等于当前 url 表示停止翻页


        确认结束 p.status = 'end'
        确认失败 p.status = 'fail' 或者set_fail()
        """
        try:
            # Prefer the configured HTTP session. It carries the refreshed
            # request headers and cookies without incurring browser overhead.
            response = Tool.get(P.url, headers=headers, cookies=cookies)
            page_html = response.text if response.status_code == 200 else ''
            if (
                response.status_code != 200
                or self._is_denied(page_html, response.url)
            ):
                Tool.print(
                    f'HTTP category request unavailable (HTTP {response.status_code}); '
                    f'using browser fallback: {P.url}',
                    color='yellow',
                )
                browser_page = self.get_page(P.url)
                page_html = browser_page.content()
                if self._is_denied(page_html, browser_page.url):
                    P.set_fail()
                    Tool.print(f'PerimeterX denied category page: {P.url}', color='red')
                    return [], None

            html = etree.HTML(page_html)
            if html is None:
                raise ValueError('Category page is not valid HTML')

            product_urls = []
            hrefs = html.xpath(
                '//div[contains(@class, "product-tile")]//a[contains(@href, ".html")]/@href'
            )
            for href in hrefs:
                url = Tool.URL.add_site(href)
                if url not in product_urls:
                    product_urls.append(url)

            next_url = self._next_url(html)
            if not product_urls:
                if next_url is None:
                    P.set_end()
                else:
                    P.set_fail()
                    Tool.print(f'No product cards found: {P.url}', color='red')

            return product_urls, next_url
        except Exception as error:
            P.set_fail()
            Tool.print(f'分类分页解析失败：{error}；{P.url}', color='red')
            return [], None

    def build_params(self, page):
        # The server-generated next link already contains the exact SFRA offset.
        return None




if __name__ == '__main__':
    pc = Pc(
       tool=Tool,
       input_path=file_path,
       output_path=save_path,
       catch_path=catch_path,
       index_path=index_path,
       ts_num=ts_num,
       flush=flush,
       skip_input_url_ls=skip_input_url_ls,
       skip_output_url_ls=skip_output_url_ls,
       catch_save_num=catch_save_num
       )
    pc.run()
