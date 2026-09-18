from lxml import etree
from config import Tool

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')

catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

# Set to None for the user's full run.
ts_num = None

# 排除某些 URL（输入分类黑名单）
skip_input_url_ls = []
# 输出商品链接黑名单
skip_output_url_ls = []

# 覆盖缓存：True=无视本地缓存强制重新请求
flush = False

catch_save_num = None

from _ljp.mb.zj import GetDetail
from _ljp.mb.model import PageModel


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
    """Read the server-rendered product tiles from one Pampers category page."""

    def fetch_page(self, page: PageModel, params):
        response = Tool.get(page.url)
        if response.status_code != 200:
            Tool.print(f"分类页请求失败: {response.status_code} {page.url}", color="red")
            page.set_fail()
            return [], None

        try:
            tree = etree.HTML(response.text)
            hrefs = tree.xpath(
                "//a[contains(concat(' ', normalize-space(@class), ' '), ' product-tile ')]/@href"
            )
        except (TypeError, ValueError, etree.ParserError) as exc:
            Tool.print(f"分类页解析失败: {exc} {page.url}", color="red")
            page.set_fail()
            return [], None

        product_urls = []
        for href in hrefs:
            url = Tool.URL.add_site(href)
            if "/en-us/products/" in url and url not in product_urls:
                product_urls.append(url)

        page.set_end()
        return product_urls, None

    def build_params(self, page):
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
