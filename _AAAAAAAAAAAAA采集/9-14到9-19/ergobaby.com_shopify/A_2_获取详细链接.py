import time

from lxml import html as lxml_html

from config import Tool
from _ljp.mb.model import PageModel

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
time_sleep = 0.5

catch_save_num = None

from _ljp.mb.shopify import GetDetail


class Pc(GetDetail):
    """分类页和首页一样在 Cloudflare 挑战后面。

    普通 HTTP（含手工复制的 cf_clearance）只会拿到挑战页，所以分页请求改用浏览器
    导航 ``self.get_page``，验证由浏览器自动完成；命中验证页时按指南重启浏览器
    指纹并把本页标记为失败，等下次运行重试。
    """

    # 主题的商品卡是 <product-card>，用它把商品网格与菜单/轮播中的商品链接分开。
    # 不要退回“页面上所有 /products/ 链接”：空列表页也有营销区块指向单品，
    # 那样会让翻页永远结束不了。
    product_xpath = '//product-card//a[contains(@href, "/products/")]'
    # 只匹配 Cloudflare 拦截页自身的内容。注意 'challenge-platform' 会出现在
    # 正常页面里（主题也引了 Cloudflare 脚本），不能拿来判断。
    challenge_markers = (
        'Just a moment',
        'challenge-error-text',
        '_cf_chl_opt',
        'Enable JavaScript and cookies to continue',
    )

    def before_request(self, p: PageModel):
        p.extra['before_request'] = {
            # 分类地址可能带 #newborn 之类的锚点，分页只在干净的 collection 地址上做。
            'collection_url': p.url.split('#')[0].split('?')[0].strip().rstrip('/'),
        }

    @classmethod
    def is_challenge(cls, html):
        return any(marker in html for marker in cls.challenge_markers)

    @staticmethod
    def page_url(collection_url, page):
        return collection_url if page <= 1 else f'{collection_url}?page={page}'

    def fetch_page(self, p: PageModel, params):
        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空 表示停止翻页
        """
        collection_url = p.extra['before_request']['collection_url']
        url = self.page_url(collection_url, p.page)

        try:
            html = self.get_page(url).content()
        except Exception as e:
            Tool.print(f"   [!] 浏览器打开失败: {e}")
            p.set_fail()
            return [], None

        if self.is_challenge(html):
            Tool.print("   [!] 命中 Cloudflare 验证页，重启浏览器指纹，本页下次重试")
            self.Tool.browser.restart_context()
            p.set_fail()
            return [], None

        tree = lxml_html.fromstring(html)
        nodes = tree.xpath(self.product_xpath)

        all_product_urls = []
        seen = set()
        for node in nodes:
            full_url = Tool.URL.add_site((node.get('href') or '').split('?')[0].split('#')[0])
            if '/products/' not in full_url or full_url in seen:
                continue
            if full_url in self.skip_output_url_ls:
                Tool.print(f'在跳过列表::{full_url}')
                continue
            seen.add(full_url)
            all_product_urls.append(full_url)

        if not all_product_urls:
            # 已经是真实页面且没有商品，说明分类翻完了
            Tool.print(f"   第 {p.page} 页没有商品，分类抓取结束")
            p.set_end()
            return [], None

        print(f"   第 {p.page} 页成功：抓取到 {len(all_product_urls)} 个链接")
        time.sleep(time_sleep)
        return all_product_urls, self.page_url(collection_url, p.page + 1)

    def build_params(self, p: PageModel):
        """构造参与缓存哈希的请求参数；分页只看页码"""
        return {'page': p.page}


if __name__ == '__main__':
    pc = Pc(tool=Tool,
            input_path=file_path,
            output_path=save_path,
            catch_path=catch_path,
            index_path=index_path,
            ts_num=ts_num,
            flush=flush,
            skip_input_url_ls=skip_input_url_ls,
            skip_output_url_ls=skip_output_url_ls,
            catch_save_num= catch_save_num

            )
    pc.run()
