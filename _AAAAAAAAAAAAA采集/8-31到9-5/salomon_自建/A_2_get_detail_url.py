import json

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
headers = {
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Origin': 'https://www.salomon.com',
    'Pragma': 'no-cache',
    'Referer': 'https://www.salomon.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    'accept': 'application/json',
    'content-type': 'text/plain',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

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


            params.pop('占位用于生成不同id')




            cat_id_ls = raw_url.replace('https://www.salomon.com/en-us/c/','').split("/")


            cat_id = ' > '.join(cat_id_ls)
            # print(cat_id)
            # cat_id = 'new > inspiration > new-arrivals'
            import uuid
            # 搜索参数（可动态修改）
            search_params = {
                "indexName": "prod_en-US_products",
                "clickAnalytics": True,
                "distinct": True,
                "facets": ["*"],
                "filters": f"categoryPageId:\"{cat_id}\"",  # 修改此值即可改变筛选条件
                "getRankingInfo": True,
                "highlightPostTag": "__/ais-highlight__",
                "highlightPreTag": "__ais-highlight__",
                "hitsPerPage": 24,  # 每页数量
                "maxValuesPerFacet": 100,
                "page": P.page-1,  # 页码（从0开始）
                "relevancyStrictness": 0,
                "userToken": str(uuid.uuid4())  # 每次请求生成新 token（或固定）
            }
            # 构建请求体
            payload = {
                "requests": [search_params]
            }

            response = Tool.post(
                'https://k1n6gb06ip-dsn.algolia.net/1/indexes/*/queries',
                params=params,  # 自动拼接到 URL 后
                headers=headers,  # 使用原有的 headers（也可参数化）
                data=json.dumps(payload)  # 确保是 JSON 字符串
            )
            # print(response.text)

            data = response.json()

            data = data["results"][0]["hits"]
            ls = []
            for item in data:
                url = item['url']
                ls.append(url)


            if len(ls) == 0:
                print(f'无产品')
                P.set_fail()
                return ls,False

            elif 0<=len(ls)< 24:
                print('产品小于24')
                P.set_end()
                return ls,False

            else:
                return ls,raw_url


        except Exception as e:
            P.set_fail()
            raise e





        raise NotImplementedError("请在 fetch_page 中实现具体站点的翻页解析逻辑，返回 (product_urls, next_url)")

    def build_params(self, p_model:PageModel):
        APPLICATION_ID = "K1N6GB06IP"
        API_KEY = "OGY0MDU4MGY0YjM2OWM4MWRlZjQxZGM0YjBkZjc2ZTRhY2JhMmNjZDU3YjExOTk4ODFlYjRkNmUzOGE3NTVhYWZpbHRlcnM9Tk9UJTIwbm90VmlzaWJsZUJ5UmVhc29uQ29kZSUzQUQyQyZydWxlQ29udGV4dHM9c3ViU2VnbWVudC1EMkMmdXNlclRva2VuPWUzMDQ4ODNhLTYxMjctNDBkYS1hMWQ2LTI3MzBlYjFkZjAwMyZ2YWxpZFVudGlsPTE3ODgyODQ2NTY="
        AGENT = "Algolia for JavaScript (5.50.1); Lite (5.50.1); Browser; instantsearch.js (4.93.0); react (19.3.0-canary-cbb046ab-20260731); react-instantsearch (7.29.0); react-instantsearch-core (7.29.0); next.js (16.3.0); JS Helper (3.28.1)"
        params = {
            'x-algolia-application-id': APPLICATION_ID,
            'x-algolia-api-key': API_KEY,
            'x-algolia-agent': AGENT,
            '占位用于生成不同id':p_model.page
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