
from lxml import etree
from urllib.parse import urlsplit, urlunsplit

from config import Tool

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')

catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

# 测试数据条数,以初始url数量计数；正式运行不限制分类数
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

    @staticmethod
    def _is_shop_all(url):
        """Shop All 使用 /collections 根路径，页面结构与普通集合不同。"""
        return urlsplit(url).path.rstrip('/') == '/collections'

    def _canonical_product_url(self, href):
        """仅保留商品路径，避免响应式副本和颜色参数造成重复请求。"""
        parsed = urlsplit(href)
        path = parsed.path.rstrip('/')
        if not path.startswith('/products/'):
            return None
        handle = path[len('/products/'):].strip('/')
        if not handle or '/' in handle:
            return None
        base = urlsplit(Tool.base_url)
        return urlunsplit((base.scheme or 'https', base.netloc, f'/products/{handle}', '', ''))

    def extract_product_urls(self, html):
        """从当前集合页 HTML 提取商品链接，并按首次出现顺序去重。"""
        tree = etree.HTML(html)
        if tree is None:
            return []

        # 两种页面都以 href 为实际数据源，不能依赖易变的 CSS 类名。
        # Shop All 可能没有普通集合页的商品网格容器，因此直接扫描整棵文档。
        anchors = tree.xpath('//a[@href]')
        result = []
        seen = set()
        for anchor in anchors:
            href = anchor.get('href', '').strip()
            if not href:
                continue
            absolute = Tool.URL.add_site(href)
            parsed = urlsplit(absolute)
            if parsed.netloc and parsed.netloc.lower() != urlsplit(Tool.base_url).netloc.lower():
                continue
            product_url = self._canonical_product_url(absolute)
            if product_url and product_url not in seen:
                seen.add(product_url)
                result.append(product_url)
        return result

    def fetch_page(self, P:PageModel, params):
        """请求集合页并返回商品链接；站点确认没有分页，因此只处理一页。"""
        try:
            res = Tool.get(P.url)
            if res.status_code == 404:
                P.set_end()
                return [], None
            if res.status_code != 200 or not res.text:
                P.set_fail()
                return [], None

            handle = Tool.URL.get_handle(P.url) or 'collections'
            Tool.HTML.save_handle(res.text, handle)
            ls = self.extract_product_urls(res.text)
            P.set_end()
            Tool.print(
                f"  {'Shop All' if self._is_shop_all(P.url) else '集合'}页面提取商品 {len(ls)} 条",
                color='cyan',
            )
            return ls, None
        except Exception as exc:
            Tool.print(f'集合页解析失败：{P.url}，{exc}', color='yellow')
            P.set_fail()
            return [], None

    def build_params(self, page):
        """使旧的 HTML 首页缓存不与 collection-filter 结果混用。"""
        return {}




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
