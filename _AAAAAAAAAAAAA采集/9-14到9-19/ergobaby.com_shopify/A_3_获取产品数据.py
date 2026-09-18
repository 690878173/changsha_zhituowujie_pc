"""阶段 3：获取产品数据。

商品页和 ``/products/{handle}.json`` 都在 Cloudflare 挑战后面，普通 HTTP 只会
拿到挑战页，因此两次请求都用浏览器导航：文档方式打开 ``.../{handle}.json`` 会直接
返回 JSON 文本，商品页 HTML 则用来解析站点自定义字段。

站点自定义字段来自商品信息栏的折叠面板（``div.product-details`` 下的
``details[data-testid="accordion-details"]``），例如 ``Fit, Carry & Sizing``、
``Fabric & Care``、``Safety Information``。``zdy_zd`` 返回
``{标签名: 清洗后的 HTML}``，由框架命名成
``名称(product.metafields.c_f.xxx)``。与 ``Description`` 完全重复的
``What You'll Love`` 以及通用文案 ``Shipping`` / ``We Think You'll Also Love``
不作为自定义字段。
"""

import json
import time

from lxml import html as lxml_html

from config import Tool
from _ljp.mb.shopify import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
fail_file = Tool.File.path_add_site('fail/4.json')

# NOTE 缓存策略
index_path = Tool.File.path_add_site('hc/4/index.json')
catch_path = Tool.File.path_add_site('hc/4/catch.json')
catch_save_num = None

skip_input_url_ls = []
skip_output_url_ls = []
# 默认使用fieldnames=None,自动写入自定义字段，需要控制字段写入由下游控制，这里保留所有字段
fieldnames = None

# 测试数据条数；小样本验证通过后恢复 None 全量
ts_num = None
# 小样本调试：把商品页原始快照写入 ts/3/
dump_html = False
# 覆盖缓存：True=无视本地缓存强制重新请求
flush = False

if_wp = False
time_sleep = 2
# 每个线程各自持有浏览器实例，线程数不宜和纯 HTTP 站点一样大
max_threads = 3


class Pc(Get_Product):
    """ergobaby 商品解析：标准字段 + 商品信息栏折叠面板自定义字段。"""

    panel_xpath = (
        '//div[contains(concat(" ", normalize-space(@class), " "), " product-details ")]'
        '//details[@data-testid="accordion-details"]'
    )
    # 与 Description 重复的描述块，以及与商品无关的通用文案
    skip_fields = ("What You'll Love", 'Shipping', "We Think You'll Also Love")
    challenge_markers = (
        'Just a moment',
        'challenge-error-text',
        '_cf_chl_opt',
        'Enable JavaScript and cookies to continue',
    )

    @classmethod
    def is_challenge(cls, html):
        return any(marker in html for marker in cls.challenge_markers)

    @staticmethod
    def node_text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @classmethod
    def field_name(cls, label):
        """把面板标题规范成可读且合法的自定义字段名。

        ``build_custom_field_name`` 会直接去掉 ``&`` 并把出现的双空格压缩掉，
        ``Fabric & Care`` 会变成 ``FabricCare``、``Fit, Carry & Sizing`` 的键里还会
        留下逗号。这里按同一语义改成 ``and`` 并去掉逗号。
        """
        return ' '.join(label.replace('&', 'and').replace(',', '').split())

    def load_document(self, url, *, as_json=False):
        """浏览器打开文档；命中 Cloudflare 验证页时换指纹并返回 ``None``。"""
        page = self.get_page(url)
        html = page.content()
        if self.is_challenge(html):
            self.Tool.browser.restart_context()
            return None
        return page.inner_text('body') if as_json else html

    def load_product_json(self, url):
        text = self.load_document(url + '.json', as_json=True)
        if text is None:
            raise RuntimeError(f'商品 JSON 命中 Cloudflare 验证页: {url}')
        try:
            product = json.loads(text).get('product')
        except ValueError as exc:
            raise RuntimeError(f'商品 JSON 解析失败: {url}: {exc}') from exc
        if not product:
            raise RuntimeError(f'商品 JSON 缺少 product: {url}')
        return product

    def zdy_zd(self, url, html_text=None, description=''):
        """返回商品信息栏折叠面板字段：``{标签名: 清洗后的 HTML}``。"""
        Tool = self.tool
        if html_text is None:
            html_text = self.load_document(url)
            if html_text is None:
                return {}
        clean_description = Tool.HTML.clean_product_desc_str(description)
        tree = lxml_html.fromstring(html_text)
        fields = {}
        for details in tree.xpath(self.panel_xpath):
            headers = details.xpath('./summary')
            if not headers:
                continue
            label = self.node_text(headers[0])
            if not label or label in self.skip_fields:
                continue
            name = self.field_name(label)
            if not name or name in fields:
                continue
            contents = [node for node in details if node.tag != 'summary']
            if not contents:
                continue
            value = Tool.HTML.clean_product_desc(contents[0])
            if not value or value == clean_description:
                continue
            fields[name] = value
        return fields

    def fetch_product(self, url, category) -> list:
        Tool = self.tool
        handle = Tool.URL.get_handle(url)
        try:
            product = self.load_product_json(url)

            page_html = self.load_document(url)
            if page_html is None:
                raise RuntimeError(f'商品页命中 Cloudflare 验证页: {url}')
            if dump_html:
                Tool.HTML.save_raw(page_html, Tool.File.path_add_site(f'ts/3/{handle}.html'))

            custom_key = Tool.custom_key
            if custom_key:
                product[custom_key] = self.zdy_zd(
                    url,
                    page_html,
                    product.get('body_html', ''),
                )
            time.sleep(time_sleep)
        except Exception as exc:
            Tool.print(f'[ERROR] 商品解析失败: {url}: {exc}')
            return []

        parent = self.shopify_to_woocommerce(
            product,
            brand=Tool.site,
            custom_categories=category,
        )
        # 内部 url 只出现在 res/ts_res.csv，最终 res/result.csv 会移除
        parent['url'] = url
        rows = [parent]
        rows.extend(self.create_variation_products(product, parent) or [])
        return rows


if __name__ == '__main__':
    pc = Pc(
        tool=Tool,
        input_path=input_file,
        output_path=output_file,
        fail_file=fail_file,
        catch_path=catch_path,
        index_path=index_path,
        output_ts_file=output_ts_file,
        ts_num=ts_num,
        catch_save_num=catch_save_num,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        flush=flush,
        fieldnames=fieldnames,
        max_threads=max_threads,
        if_wp=if_wp,
    )
    pc.run()
    Tool.close()
