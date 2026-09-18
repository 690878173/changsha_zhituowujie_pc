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
cookies = {
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Sat+Aug+29+2026+10%3A33%3A57+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202607.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d92bb841-e4b7-427b-911a-049cd65d2930&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1%2CSPD_BG%3A1&intType=1&isDntEnabled=0&geolocation=US%3BCA&prevHadToken=0&AwaitingReconsent=false',
    'dwac_a727347a0b73166c555e3c5820': 'FzNwzvQwbxoZwaAysBcXtoTAtCHmgRH5cy4%3D|dw-only|||USD|false|Etc%2FUTC|true',
    'cquid': '||',
    'dwanonymous_dee395c8970fc2272ed4e02de3ef745c': 'abNDSC0pTsBtBVT5no1ag30GLr',
    'sid': 'FzNwzvQwbxoZwaAysBcXtoTAtCHmgRH5cy4',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    'dwsid': 'Bhqw_iXF6hqdHymTeJIz5pXpdBE3dJT59_DjZW2Ti0zkIiRRO6FldhsSzuadT5ilXqX2haYovOR3RPKO_3tA0A==',
    'OptanonAlertBoxClosed': '2026-08-29T01:25:53.764Z',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Sat+Aug+29+2026+09%3A25%3A53+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202511.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d92bb841-e4b7-427b-911a-049cd65d2930&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1%2CSPD_BG%3A1&intType=1',
    '_gcl_au': '1.1.531873312.1787966754',
    '_ga': 'GA1.1.735871438.1787966755',
    'FPID': 'FPID2.2.sEDCjjBJwwtkoMYpP42h3KdBtTWIVBz92Vi1Vx5DzH0%3D.1787966755',
    'FPLC': 'gpAzcPyEbcPMCPFtMArFtjH51SeSzvkE3JrT%2FJVbUuTE82qi4lDu8mm0vp4dMApgWj1vU7k%2BBzsgmqN5b7SPq7qxY%2BgmP20L3%2FtQTso656Km0SAq4IZDXar8ju8zjQ%3D%3D',
    'dwac_dd41ae5d1d9f257ffbb54354e5': 'FzNwzvQwbxoZwaAysBcXtoTAtCHmgRH5cy4%3D|dw-only|||USD|false|US%2FEastern|true',
    'cqcid': 'acR1GHAwmKOXhIjUa3OPM0gOeT',
    'cc-nx-g_OCC_US': 'kAmMh7HqxeCQZJY_lW3D27n6gcxYUDMdtHNvnZHTFis',
    'usid_OCC_US': '63b7b718-bd31-4e28-956c-eb94e50b4392',
    'OCC_ABTestInHouseSegment': 'us_aa_engine_validation_2026_0:control',
    'OCC_US_Personalization': '"{\\"segment\\":\\"\\",\\"purchaseProducts\\":\\"\\",\\"collections\\":\\"\\"}"',
    'dwanonymous_ba53c4ee9781407e12f4bf01a897ab37': 'acR1GHAwmKOXhIjUa3OPM0gOeT',
    'og_optins': 'W10=',
    'og_session_id': '3c61058ad29e11e299d20026b93abf5d.964378.1787966777',
    'trustedsite_visit': '1',
    'FPAU': '1.1.531873312.1787966754',
    '_fbp': 'fb.1.1787966779350.1276671414',
    '_gtmeec': 'eyJzdCI6IjY4YWEzYjMwYjE2ZTM0YTc0Nzk2YjY5ODFmMTliYTMzYWY1MTViMzYxZjFmMThlNmRjNzY4NGZiNWFlMWYwZWQifQ%3D%3D',
    '_scid': 'd79418e9-9df4-49f4-40e4-45f1ecc1cd5b',
    '_pin_unauth': 'dWlkPU1URXpOVFJoT1RFdE9EQmhOQzAwTkRWakxUaGtaV1F0WkdSa01tWm1NVFUyTkdVNA',
    'og_site': '3c61058ad29e11e299d20026b93abf5d',
    '__pr.1pka': 'JueiWcxz_I',
    'userId': '816129.1787967904626',
    'FPGSID': '1.1787970826.1787970826.G-WT9SD86FBB.t--jDipRkn1FtEH89YuIWA',
    'forterToken': '6a52318f9182405496ac4ea3a1fedfda_1787970831470__UDF43-m4_27ck_',
    '_ga_WT9SD86FBB': 'GS2.1.s1787966755$o1$g1$t1787970837$j36$l0$h22357680',
    'datadome': 'jnEVmhr7oUTXK8826o93fC6boAbylzNVu~xUlGZy9bFO6_C9pipQSUJ~AU3n2wr~O3vro5TWSNOymO_3GV3K9y0KDm54FKwrvP7p~HlAsfwZ~ygqUNWqQRowC7qIx2~e',
}

catch_save_num = None

from _ljp.mb.zj import GetDetail
from _ljp.mb.model import Base, PageModel


def w():
    from playwright.sync_api import sync_playwright
    from fingerprint_toolkit import FingerprintKit
    from itertools import cycle

    edge = sync_playwright().start()
    browser = edge.chromium.launch(headless=False)

    # 创建4个上下文，保存对应的 fpk
    contexts = [browser.new_context() for _ in range(4)]
    context_fpk = {}
    for ctx in contexts:
        fpk = FingerprintKit()
        context_fpk[ctx] = fpk
        # 可选：创建一个初始页面，但不强制

    context_cycle = cycle(contexts)  # 循环迭代器

    def get():
        ctx = next(context_cycle)
        fpk = context_fpk[ctx]
        page = ctx.new_page()
        fpk.inject(page)
        return page

    return get


class Pc(GetDetail):

    def fetch_page(self, P:PageModel, params):
        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空或等于当前 url 表示停止翻页


        确认结束 p.status = 'end'
        确认失败 p.status = 'fail' 或者set_fail()
        """
        try:
            raw_url = P.url

            res = Tool.get(raw_url,params=params,cookies=cookies)

            if 'There are no products matching the chosen criteria.' in res.text:
                P.set_end()
                return [],False
            html = etree.HTML(res.text)

            ps = Tool.URL.get_params_str(params=params)

            Tool.HTML.save(res.text,f'html/{raw_url.split('/')[-1]}/{ps[1:]}.html')


            lis = html.xpath('//section[@class="search-result-section"]/ul/li')
            ls = []

            one_ls = []
            for li in lis:
                a = li.xpath('.//a[@class="a-product-link"]/@href')

                one_ls = [Tool.URL.add_site(item) for item in a]

                ls.extend(one_ls)

            print(len(ls))

            if P.extra.get('product_urls',[]) == ls:
                print(f'相同的列表')
                P.set_end()
                return [],False
            else:
                P.extra['product_urls'] = ls

            if len(ls) == 0:
                print(f'无商品了')
                P.set_fail()
                return ls,raw_url

            return ls,raw_url

        except Exception as e:
            P.set_fail()
            raise e

    def build_params(self, page):
        """构造参与缓存哈希的请求参数；默认仅包含页码"""
        page_num = int(page.page)

        if page_num == 0:
            print(f'错误的页码')
            params = {}
        elif page_num == 1:
            params = {}
        else:
            params = {
                'sz': '32',
                'start': (int(page.page)-1)*32+1,
                'format': 'ajax',
                'type': 'view-more',
                'context': 'products-list',
                # 'vstart': '63',
                # 'vend': '94',
            }
        return params




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