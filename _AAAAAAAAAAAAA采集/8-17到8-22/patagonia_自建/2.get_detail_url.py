import time
from math import ceil
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import Error as PlaywrightError

from config import Tool
from _ljp.mb.model import PageModel
from _ljp.mb.zj import GetDetail


file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

# 测试数据条数，以初始 URL 数量计数。
ts_num = None
skip_input_url_ls = []
skip_output_url_ls = []
flush = False


class Pc(GetDetail):
    """Patagonia 分类页浏览器抓取器。"""

    product_selector = '.product a.link[href*="/product/"]'
    page_size = 36
    max_attempts = 2
    homepage_probe_count = 2
    homepage_probe_interval_ms = 2000

    def _init(self):
        super()._init()
        self.page = self.get_page()

    def after_one_request(self, page: PageModel):
        self.save_catch()

    def _restart_page(self, relaunch_browser=False):
        try:
            self.page.close()
        except Exception:
            pass
        self.Tool.browser.restart_context(relaunch_browser=relaunch_browser)
        self.page = self.get_page()

    @staticmethod
    def _is_challenge(page):
        try:
            text = f'{page.title()}\n{page.locator("body").inner_text(timeout=3000)}'.lower()
        except Exception:
            return True
        markers = (
            'access denied', 'verify you are human', 'security check',
            'checking your browser', 'challenge', 'captcha',
        )
        return any(marker in text for marker in markers)

    @staticmethod
    def _is_not_found(page):
        try:
            title = page.title().strip().lower()
            body = page.locator('body').inner_text(timeout=3000).strip().lower()
        except Exception:
            return False
        return title in {'404', '404 not found', 'not found'} or body in {
            '404', '404 not found', 'not found',
        }

    def _product_urls(self, page):
        hrefs = page.locator(self.product_selector).evaluate_all(
            '(links) => links.map((link) => link.href)'
        )
        return list(dict.fromkeys(Tool.URL.add_site(href) for href in hrefs if href))

    @staticmethod
    def _page_url(url, page_number):
        parsed = urlsplit(url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query['page'] = str(page_number)
        return urlunsplit(parsed._replace(query=urlencode(query)))

    def _total_count(self):
        total_locator = self.page.locator(
            '.shopping-sort-header__result-count[data-count]'
        )
        if not total_locator.count():
            return None
        raw_total = total_locator.first.get_attribute('data-count')
        if not raw_total:
            return None
        return int(raw_total.replace(',', ''))

    def _homepage_is_available(self):
        """确认首页在稳定期内没有被站点改写为 Not found。"""
        try:
            self.page.goto(
                self.Tool.URL.add_site('/'),
                wait_until='domcontentloaded',
                timeout=30000,
            )
            self.page.wait_for_selector('body', timeout=10000)
            for check in range(self.homepage_probe_count):
                if self._is_not_found(self.page):
                    Tool.print(
                        f'首页探活第 {check + 1}/{self.homepage_probe_count} 次检查为 Not found。',
                        color='yellow',
                    )
                    return False
                if check < self.homepage_probe_count - 1:
                    self.page.wait_for_timeout(self.homepage_probe_interval_ms)
            return True
        except Exception:
            return False

    def _recover_after_failure(self, attempt):
        if self._homepage_is_available():
            Tool.print('分类页失败，但首页正常；保留当前浏览器会话后重试。', color='yellow')
            return

        Tool.print('分类页和首页均访问失败，重启浏览器后重试。', color='yellow')
        self._restart_page(relaunch_browser=True)

    def fetch_page(self, page: PageModel, params):
        for attempt in range(self.max_attempts):
            try:
                # Patagonia keeps loading third-party assets after the product grid is ready.
                # Waiting for DOM content and then the product selector avoids load-event timeouts.
                self.page.goto(page.url, wait_until='domcontentloaded', timeout=60000)
                if self._is_not_found(self.page):
                    self.page.wait_for_timeout(1000)
                    if self._is_not_found(self.page):
                        raise RuntimeError('分类页在稳定检查后仍返回 Not found。')

                total_count = self._total_count()
                if total_count is None or total_count <= 0:
                    Tool.print('分类页没有商品总数，判定为无数据并跳过。', color='cyan')
                    page.status = 'end'
                    return [], None

                self.page.wait_for_selector(self.product_selector, timeout=20000)
                self.page.wait_for_timeout(800)
                total_pages = max(1, ceil(total_count / self.page_size))
                request_url = self._page_url(page.url, total_pages)
                Tool.print(f'商品总数：{total_count}，末页参数：{total_pages}', color='cyan')

                self.page.goto(request_url, wait_until='domcontentloaded', timeout=60000)
                if self._is_not_found(self.page):
                    raise RuntimeError('带 page 参数的分类页返回 Not found。')
                self.page.wait_for_selector(self.product_selector, timeout=30000)
                self.page.wait_for_timeout(800)
                urls = self._product_urls(self.page)
                if not urls:
                    page.status = 'end'
                    return [], None
                return urls, None
            except PlaywrightError as exc:
                if self._is_challenge(self.page):
                    Tool.print(
                        f'检测到验证页面，第 {attempt + 1}/{self.max_attempts} 次重建浏览器会话后重试。',
                        color='yellow',
                    )
                else:
                    Tool.print(
                        f'分类页导航失败，第 {attempt + 1}/{self.max_attempts} 次重试：{exc}',
                        color='yellow',
                    )
                self._recover_after_failure(attempt)
            except Exception as exc:
                Tool.print(
                    f'分类页解析失败，第 {attempt + 1}/{self.max_attempts} 次重试：{exc}',
                    color='yellow',
                )
                self._recover_after_failure(attempt)

        page.status = 'fail'
        return [], None

    def build_params(self, page):
        return {'collector': 'browser-v4'}


if __name__ == '__main__':
    Pc(
        tool=Tool,
        input_path=file_path,
        output_path=save_path,
        catch_path=catch_path,
        index_path=index_path,
        ts_num=ts_num,
        flush=flush,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
    ).run()
