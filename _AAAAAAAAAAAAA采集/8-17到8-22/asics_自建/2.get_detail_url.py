import time

from playwright.sync_api import Error as PlaywrightError

from _ljp.mb.modal import Page
from _ljp.mb.zj import GetDetail
from config import Tool


file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

ts_num = None
skip_input_url_ls = ['https://www.asics.com/us/en-us/releases/']
skip_output_url_ls = []
flush = False


class Pc(GetDetail):
    """Asics category crawler using the shared fingerprinted context pool."""

    def _init(self):
        super()._init()
        self.page = self.get_page()
        self.page.wait_for_timeout(1500)

    def get_one_page(self, relaunch_browser=False):
        """Rotate contexts after a verification or access-denied response."""
        try:
            self.page.close()
        except Exception:
            pass
        self.Tool.browser.restart_context(relaunch_browser=relaunch_browser)
        self.page = self.get_page()
        self.page.wait_for_timeout(1500)

    def after_one_request(self, p: Page):
        self.save_catch()

    @staticmethod
    def _is_challenge(page):
        try:
            title = page.title().lower()
            body = page.locator('body').inner_text(timeout=2500).lower()
        except Exception:
            return True
        markers = (
            'access denied', 'verify you are human', 'security check',
            'checking your browser', 'challenge', 'captcha',
        )
        return any(marker in title or marker in body for marker in markers)

    def _load_category(self, url, params):
        query = '&'.join(f'{key}={value}' for key, value in params.items())
        return f'{url}?{query}' if query and '?' not in url else url

    def fetch_page(self, p, params):
        url = p.url
        if '?' in url:
            params = {}
        request_url = self._load_category(url, params)

        for attempt in range(3):
            page = self.page
            try:
                page.goto(request_url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(1200)
                try:
                    page.wait_for_selector('.productTile__root', timeout=12000)
                except Exception:
                    if self._is_challenge(page):
                        Tool.print(
                            f'检测到验证页面，第 {attempt + 1}/3 次重建 context 后重试',
                            color='yellow',
                        )
                        self.get_one_page(relaunch_browser=attempt >= 1)
                        continue
                    raise

                links = page.locator('.productTile__root a').all()
                urls = [
                    Tool.URL.add_site(href.replace('\\', '/'))
                    for href in (link.get_attribute('href') for link in links)
                    if href
                ]
                urls = list(dict.fromkeys(urls))
                if not urls:
                    p.status = 'end'
                    return [], None

                if p.extra.get('data') == urls:
                    p.status = 'end'
                    return [], None
                p.extra['data'] = urls

                try:
                    total_text = page.locator('[data-test="total-hit-count"]').inner_text(timeout=2000)
                    p.extra['total'] = int(total_text.replace(',', '').replace('(', '').replace(')', '').strip())
                except Exception:
                    pass

                if request_url == url or len(urls) < 24:
                    return urls, None
                self.save_catch()
                return urls, url
            except PlaywrightError as exc:
                if 'ERR_TOO_MANY_REDIRECTS' in str(exc):
                    p.status = 'end'
                    return [], None
                Tool.print(f'分类页导航失败，第 {attempt + 1}/3 次重试: {exc}')
                self.get_one_page(relaunch_browser=attempt >= 1)
            except Exception as exc:
                Tool.print(f'分类页解析失败，第 {attempt + 1}/3 次重试: {exc}')
                self.get_one_page(relaunch_browser=attempt >= 1)

        p.status = 'fail'
        return [], None

    def build_params(self, page):
        return {'page': str(page.page)}


if __name__ == '__main__':
    Pc(
        tool=Tool,
        file_path=file_path,
        output_path=save_path,
        catch_path=catch_path,
        index_path=index_path,
        ts_num=ts_num,
        flush=flush,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
    ).run()
