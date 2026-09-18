"""Use the already verified local Chrome session to collect ASICS products.

Start Chrome with ``--remote-debugging-port=9222`` first, then manually open
an ASICS tab in that browser. This script reuses that tab and never creates a
fresh browser profile or closes the user's Chrome window.
"""

import runpy
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from config import Tool
from _ljp.mb.base import Get_Product




script_dir = Path(__file__).resolve().parent
source_script = script_dir / '3.get_product_data.py'
source_module = runpy.run_path(str(source_script), run_name='asics_product_parser')
AsicsProductParser = source_module['AsicsProductParser']
AsicsChallengeError = source_module['AsicsChallengeError']

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
fail_file = Tool.File.path_add_site('data/fail.json')
catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

cdp_url = 'http://127.0.0.1:9222'
request_interval_seconds = 4


class AttachedChromeAsicsProductStep(Get_Product):
    challenge_markers = (
        'access denied', 'captcha', 'verify you are human', 'checking your browser',
    )

    def _init(self):
        self._browser_local = threading.local()
        self._last_request_at = 0.0
        self._request_lock = threading.Lock()

    @classmethod
    def is_challenge(cls, response, body):
        return (response is not None and response.status >= 400) or any(
            marker in body for marker in cls.challenge_markers
        )

    def _browser_state(self):
        state = getattr(self._browser_local, 'state', None)
        if state:
            return state
        playwright = sync_playwright().start()
        try:
            browser = playwright.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = next(
                (
                    candidate
                    for candidate in context.pages
                    if candidate.url.startswith('https://www.asics.com/')
                ),
                None,
            )
            if page is None:
                raise RuntimeError(
                    '未找到 ASICS 标签页。请先在已启动调试端口的 Chrome 中手动打开 '
                    'https://www.asics.com/us/en-us/，确认页面正常后再运行。'
                )
        except Exception:
            playwright.stop()
            raise
        state = playwright, browser, page
        self._browser_local.state = state
        return state

    def _page(self):
        return self._browser_state()[2]

    def _disconnect(self):
        state = getattr(self._browser_local, 'state', None)
        if not state:
            return
        playwright, _browser, _page = state
        # This tab belongs to the user. Do not close it or its persistent
        # Context; stopping Playwright only disconnects this client.
        playwright.stop()
        self._browser_local.state = None

    def _wait_for_request_slot(self):
        with self._request_lock:
            delay = self._last_request_at + request_interval_seconds - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            self._last_request_at = time.monotonic()

    def close_playwright(self):
        self._disconnect()

    def fetch_product(self, url, category):
        page = self._page()
        self._wait_for_request_slot()
        try:
            response = page.goto(url, wait_until='commit', timeout=30000)
            body = page.locator('body').inner_text(timeout=5000).lower()
            if self.is_challenge(response, body):
                status = response.status if response else 'page marker'
                raise AsicsChallengeError(
                    f'接管的 Chrome 收到 ASICS verification/access-denied: {status}'
                )
            page.wait_for_selector('#mobify-data', state='attached', timeout=15000)
            page.wait_for_timeout(500)
            return AsicsProductParser(url, category, page).run()
        except PlaywrightError as exc:
            raise RuntimeError(f'接管的 Chrome 商品页请求失败：{exc}') from exc


def post_process_variations():
    runpy.run_path(str(script_dir / '4.去重.py'), run_name='__main__')
    runpy.run_path(str(script_dir / '5.生成variable.py'), run_name='__main__')


if __name__ == '__main__':
    AttachedChromeAsicsProductStep(
        tool=Tool,
        input_path=input_file,
        output_path=output_file,
        fail_file=fail_file,
        catch_path=catch_path,
        index_path=index_path,
        output_ts_file=output_ts_file,
        max_threads=1,
        catch_save_num=20,
    ).run()
    post_process_variations()

    # 启动调试浏览器
    # "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\69087\AppData\Local\Chrome-patagonia-debug"
