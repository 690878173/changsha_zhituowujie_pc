from urllib.parse import parse_qs, urlencode, urlsplit
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


class Pc(GetDetail):

    def fetch_page(self, P:PageModel, params):
        """请求 collection-filter 接口并返回当前页商品和下一页 URL。"""
        try:
            page_url = P.next_url or P.url
            parsed_url = urlsplit(page_url)
            query = parse_qs(parsed_url.query)
            handle = query.get('handle', [parsed_url.path.rstrip('/').split('/')[-1]])[0]
            if not handle:
                P.set_fail()
                return [], None

            api_url = Tool.URL.add_site('/api/collection-filter')
            if parsed_url.path.rstrip('/') == '/api/collection-filter':
                request_url = page_url
            else:
                request_url = f'{api_url}?{urlencode({"handle": handle})}'

            response = Tool.get(request_url)
            if response.status_code != 200:
                P.set_fail()
                return [], None

            payload = response.json()
            product_urls = [
                Tool.URL.add_site(f'/products/{product["handle"]}')
                for product in payload.get('products', [])
                if isinstance(product, dict) and product.get('handle')
            ]

            end_cursor = payload.get('endCursor')
            if payload.get('hasNextPage') and isinstance(end_cursor, str) and end_cursor:
                next_url = f'{api_url}?{urlencode({"handle": handle, "endCursor": end_cursor})}'
            else:
                next_url = None
                P.set_end()

            return product_urls, next_url
        except Exception:
            P.set_fail()
            return [], None

    def build_params(self, page):
        """使旧的 HTML 首页缓存不与 collection-filter 结果混用。"""
        return {
            'source': 'collection-filter-v1',
            'page_url': page.next_url or page.url,
        }




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
