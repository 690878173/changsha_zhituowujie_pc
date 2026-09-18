import json
import re
import runpy
import threading
import time
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError

from config import Tool
from _ljp.mb.base import Get_Product

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
fail_file = Tool.File.path_add_site('data/fail.json')
catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

ts_num = None
skip_input_url_ls = []
skip_output_url_ls = []
fieldnames = None
catch_save_num = 20
verification_wait_seconds = 180
request_interval_seconds = 8
challenge_cooldown_seconds = (180, 480)

class AsicsChallengeError(RuntimeError):
    """The page loaded, but ASICS returned a challenge or denial response."""


class AsicsProductParser:
    """Build product rows from ASICS's server-rendered PDP state."""

    def __init__(self, url, category, page):
        self.url = url
        self.category = category
        self.document = page.content()
        Tool.HTML.save_raw(self.document)
        self.page_product = self._read_page_product()
        self.product_group = self._read_product_group()

    def _read_page_product(self):
        """Read gender, images and size conversions from ``mobify-data``."""
        match = re.search(
            r'<script[^>]+id=["\']mobify-data["\'][^>]*>(.*?)</script>',
            self.document,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return {}
        try:
            state = json.loads(match.group(1))
            return (
                state['__PRELOADED_STATE__']['__STATE_MANAGEMENT_LIBRARY']
                ['store']['productStore']['productsById']
            )
        except (KeyError, TypeError, ValueError):
            return {}

    def _read_product_group(self):
        # React serializes JSON-LD inside an HTML comment, so DOM script
        # selectors do not see it. It is nevertheless part of page.content().
        match = re.search(
            r'<script[^>]+data-test=["\']product-group-json-ld["\'][^>]*>'
            r'(.*?)</script>',
            self.document,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except (TypeError, ValueError):
            return {}

    def _read_product_json_ld(self):
        match = re.search(
            r'<script[^>]+data-test=["\']product-json-ld["\'][^>]*>'
            r'(.*?)</script>',
            self.document,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return {}
        try:
            return json.loads(match.group(1).strip())
        except (TypeError, ValueError):
            return {}

    def _save_missing_variant_diagnostic(self, group, variants):
        """Persist the successful response when its JSON-LD shape is unexpected."""
        sku_match = re.search(r'/p/([^/.]+)\.html', self.url, re.IGNORECASE)
        identifier = sku_match.group(1) if sku_match else re.sub(r'[^A-Za-z0-9._-]+', '_', self.url)
        html_path = Tool.File.path_add_site(
            f'debug/3/missing_product_group/{identifier}.html'
        )
        json_path = Tool.File.path_add_site(
            f'debug/3/missing_product_group/{identifier}.json'
        )
        product_json_ld = self._read_product_json_ld()
        diagnosis = (
            '页面没有 product-group-json-ld 脚本'
            if not group
            else 'product-group-json-ld 中没有 hasVariant 列表'
            if not isinstance(variants, list)
            else 'product-group-json-ld 的 hasVariant 列表为空'
        )
        Tool.HTML.save_raw(self.document, html_path)
        Tool.File.save_json(
            {
                'url': self.url,
                'diagnosis': diagnosis,
                'product_group_type': group.get('@type') if isinstance(group, dict) else None,
                'product_group_keys': sorted(group) if isinstance(group, dict) else [],
                'has_variant_type': type(variants).__name__,
                'has_variant_count': len(variants) if isinstance(variants, list) else None,
                'product_json_ld': product_json_ld,
                'page_product_ids': list(self.page_product) if isinstance(self.page_product, dict) else [],
            },
            json_path,
        )
        return html_path, json_path

    @property
    def current_product(self):
        products = self.page_product
        if not isinstance(products, dict):
            return {}
        sku_match = re.search(r'/p/([^/.]+)\.html', self.url, re.IGNORECASE)
        if sku_match and sku_match.group(1) in products:
            return products[sku_match.group(1)]
        return next(iter(products.values()), {})

    def gender(self):
        return (
            self.current_product.get('c_custom', {})
            .get('productGender', {})
            .get('gender')
            or ''
        )

    def women_size_map(self):
        values = (
            self.current_product.get('c_custom', {})
            .get('attributes', {})
            .get('size', {})
            .get('values', [])
        )
        return {
            str(value.get('value')): str(value['c_womenSize'])
            for value in values
            if value.get('value') is not None and value.get('c_womenSize') not in (None, '')
        }

    def images(self, variant):
        value = variant.get('image') or self.current_product.get('c_custom', {}).get('images', [])
        if isinstance(value, str):
            value = [value]
        return Tool.Product.clean_imgs(value or [])

    @staticmethod
    def is_real_combination(variant):
        """Ignore color swatches only when the group also has sized SKUs."""
        return any(
            str(variant.get(key) or '').strip().upper() not in ('', 'N/A')
            for key in ('size', 'width')
        )

    def attrs(self, variant):
        attrs = {'Color': variant.get('color') or ''}
        size = str(variant.get('size') or '').strip()
        women_size = self.women_size_map().get(size)
        if women_size:
            attrs['Size'] = f"Men's {size} / Women's {women_size}"
        elif size and size.upper() != 'N/A':
            attrs['Size'] = size

        width = str(variant.get('width') or '').strip()
        if width and width.upper() != 'N/A':
            attrs['Width'] = width
        if self.gender():
            attrs['Gender'] = self.gender()
        return attrs

    def single_product_rows(self):
        """Build one simple-product row from PDPs that do not expose a ProductGroup."""
        product = self._read_product_json_ld()
        offer = product.get('offers') if isinstance(product, dict) else None
        if not isinstance(offer, dict) or not offer:
            return []

        sku = product.get('sku') or product.get('mpn')
        name = product.get('name') or self.current_product.get('name')
        if not sku or not name:
            return []

        availability = str(offer.get('availability') or '').lower()
        return [
            Tool.Product.Simple(
                url=offer.get('url') or self.url,
                cat=self.category,
                imgs=self.images(product),
                name=name,
                sku=sku,
                price=Tool.clean_price(offer.get('price') or ''),
                desc=product.get('description') or self.current_product.get('longDescription') or '',
                brand=(product.get('brand') or {}).get('name') or 'ASICS',
                stock=0 if availability.endswith('/outofstock') else 1000,
            ).to_dic()
        ]

    def run(self):
        group = self.product_group
        variants = group.get('hasVariant') if isinstance(group, dict) else None
        if not isinstance(variants, list) or not variants:
            rows = self.single_product_rows()
            if rows:
                return rows
            html_path, json_path = self._save_missing_variant_diagnostic(group, variants)
            raise ValueError(
                'ASICS PDP 未提供可解析的 ProductGroup 或 Product Offer 数据；'
                f'已保存响应：{html_path}；分析摘要：{json_path}'
            )

        has_sized_variants = any(self.is_real_combination(variant) for variant in variants)
        rows = []
        parent = group.get('productGroupID') or self.current_product.get('c_custom', {}).get('masterId')
        name = group.get('name') or self.current_product.get('name') or ''
        description = group.get('description') or self.current_product.get('longDescription') or ''

        for variant in variants:
            if has_sized_variants and not self.is_real_combination(variant):
                continue
            offer = variant.get('offers') or {}
            availability = str(offer.get('availability') or '').lower()
            is_out_of_stock = availability.endswith('/outofstock')
            rows.append(
                Tool.Product.Variation(
                    url=offer.get('url') or self.url,
                    cat=self.category,
                    imgs=self.images(variant),
                    name=variant.get('name') or name,
                    sku=variant.get('sku') or variant.get('mpn'),
                    price=Tool.clean_price(offer.get('price') or ''),
                    desc=variant.get('description') or description,
                    brand=(group.get('brand') or {}).get('name') or 'ASICS',
                    stock=0 if is_out_of_stock else 1000,
                    parent=parent,
                    att=self.attrs(variant),
                ).to_dic()
            )
        return rows


class AsicsProductStep(Get_Product):
    challenge_markers = (
        'access denied', 'captcha', 'verify you are human', 'checking your browser',
    )

    def _init(self):
        # Step4 workers own their browser resources. Each Context retains one
        # page for its whole lifetime, making the Context round-robin explicit.
        self._page_pool = threading.local()
        self._verify_browser_session()

    def _reset_page_pool(self):
        for page in getattr(self._page_pool, 'pages', []):
            try:
                page.close()
            except Exception:
                pass
        self._page_pool.pages = []
        self._page_pool.next_index = 0

    def _ensure_page_pool(self):
        pages = getattr(self._page_pool, 'pages', [])
        if pages:
            return pages

        try:
            pages = [
                self.get_page()
                for _ in range(self.Tool.browser.config.context_count)
            ]
        except Exception:
            for page in pages:
                try:
                    page.close()
                except Exception:
                    pass
            raise
        self._page_pool.pages = pages
        self._page_pool.next_index = 0
        return pages

    def _take_page(self):
        pages = self._ensure_page_pool()
        index = getattr(self._page_pool, 'next_index', 0)
        self._page_pool.next_index = (index + 1) % len(pages)
        return pages[index]

    def _wait_for_request_slot(self):
        """Keep one browser session below ASICS's observed PDP burst limit."""
        next_request_at = getattr(self._page_pool, 'next_request_at', 0.0)
        delay = next_request_at - time.monotonic()
        if delay > 0:
            Tool.print(f'ASICS 请求冷却 {delay:.0f} 秒后继续', color='yellow')
            time.sleep(delay)

    def _schedule_next_request(self, delay_seconds):
        self._page_pool.next_request_at = max(
            getattr(self._page_pool, 'next_request_at', 0.0),
            time.monotonic() + delay_seconds,
        )

    def _verify_browser_session(self):
        """Keep the first visible browser session open for ASICS verification."""
        page = self._take_page()
        response = page.goto(
            self.Tool.base_url,
            wait_until='domcontentloaded',
            timeout=60000,
        )
        deadline = time.monotonic() + verification_wait_seconds
        prompted = False
        while self.page_is_challenge(page, response):
            if not prompted:
                status = response.status if response else 'page marker'
                Tool.print(
                    'ASICS 指纹验证已打开，请在浏览器窗口完成验证；'
                    f'等待最多 {verification_wait_seconds} 秒（当前状态：{status}）',
                    color='yellow',
                )
                prompted = True
            if time.monotonic() >= deadline:
                raise AsicsChallengeError(
                    'ASICS 首页验证未在规定时间内通过；请在已打开的浏览器窗口完成验证后重新运行。'
                )
            page.wait_for_timeout(2000)
            response = None
        if prompted:
            Tool.print('ASICS 指纹验证已通过，开始采集商品页。', color='green')

    def close_playwright(self):
        self._reset_page_pool()
        super().close_playwright()

    @classmethod
    def is_challenge(cls, response, body):
        return (response is not None and response.status >= 400) or any(
            marker in body for marker in cls.challenge_markers
        )

    def page_is_challenge(self, page, response=None):
        """Check the already loaded page without generating another request."""
        try:
            body = page.locator('body').inner_text(timeout=3000).lower()
            return self.is_challenge(response, body)
        except PlaywrightError:
            return True

    def restart_after_challenge(self, page, attempt, exc):
        cooldown = challenge_cooldown_seconds[min(attempt, len(challenge_cooldown_seconds) - 1)]
        self._schedule_next_request(cooldown)
        self._reset_page_pool()
        Tool.print(
            f'商品页受限，第 {attempt + 1}/3 次尝试；'
            f'冷却 {cooldown} 秒后重启浏览器并重试: {exc}',
            color='yellow',
        )
        self.Tool.browser.restart_context(relaunch_browser=True)


    def fetch_product(self, url, category):
        for attempt in range(3):
            page = None
            try:
                page = self._take_page()
                self._wait_for_request_slot()
                response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
                self._schedule_next_request(request_interval_seconds)
                body = page.locator('body').inner_text(timeout=3000).lower()
                if self.is_challenge(response, body):
                    status = response.status if response else 'page marker'
                    raise AsicsChallengeError(
                        f'ASICS verification or access-denied response: {status}'
                    )

                # ``script`` elements are hidden by definition. Waiting for
                # the default visible state caused every valid PDP to time out.
                page.wait_for_selector('#mobify-data', state='attached', timeout=15000)
                page.wait_for_timeout(500)
                return AsicsProductParser(url, category, page).run()
            except AsicsChallengeError as exc:
                if attempt == 2:
                    raise
                self.restart_after_challenge(page, attempt, exc)
            except PlaywrightError as exc:
                if attempt == 2:
                    raise
                Tool.print(
                    f'商品页请求失败，第 {attempt + 1}/3 次重建 context 后重试: {exc}',
                    color='yellow',
                )
                time.sleep(1)
                self._reset_page_pool()
                self.Tool.browser.restart_context(relaunch_browser=attempt >= 1)
            finally:
                # Pages stay open and alternate between Contexts. Context and
                # browser shutdown is handled by close_playwright().
                pass


def post_process_variations():
    """Deduplicate SKU rows, then build one variable parent per ASICS style."""
    script_dir = Path(__file__).resolve().parent
    runpy.run_path(str(script_dir / '4.去重.py'), run_name='__main__')
    runpy.run_path(str(script_dir / '5.生成variable.py'), run_name='__main__')


if __name__ == '__main__':
    AsicsProductStep(
        tool=Tool,
        input_path=input_file,
        output_path=output_file,
        fail_file=fail_file,
        catch_path=catch_path,
        index_path=index_path,
        output_ts_file=output_ts_file,
        ts_num=ts_num,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        fieldnames=fieldnames,
        max_threads=1,
        catch_save_num=catch_save_num,
    ).run()
    post_process_variations()
