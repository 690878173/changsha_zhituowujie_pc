"""阶段 3：获取产品数据。

标准字段来自 Shopify ``/products/{handle}.json``；商品页 PDP 标签页
（``.pdp-tabs``，由 ``metafield-multi_line_text_field`` 渲染）作为站点自定义
字段，由 ``zdy_zd`` 返回 ``{标签名: 清洗后的内容}`` 交给框架命名。
"""

import time

from lxml import etree

from config import Tool
from _ljp.mb.shopify import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
fail_file = Tool.File.path_add_site('fail/4.json')

# 缓存策略
index_path = Tool.File.path_add_site('hc/4/index.json')
catch_path = Tool.File.path_add_site('hc/4/catch.json')
catch_save_num = None

skip_input_url_ls = []
skip_output_url_ls = []
# fieldnames=None：自动写入 zdy_zd 返回的全部自定义字段
fieldnames = None

# 测试数据条数；小样本验证通过后恢复 None 全量
ts_num = None
# 小样本调试：把商品页原始快照写入 ts/3/
dump_html = False
# 覆盖缓存：True=无视本地缓存强制重新请求
flush = False

if_wp = False
time_sleep = 1


class Pc(Get_Product):
    """nodpod 商品解析：标准字段 + PDP 标签页自定义字段。"""

    tabs_xpath = (
        '//div[contains(concat(" ", normalize-space(@class), " "), " pdp-tabs ")]'
    )
    tab_button_xpath = './/button[starts-with(@id, "Tab-")]'
    tab_panel_xpath = './/div[starts-with(@id, "TabPanel-")]'

    @staticmethod
    def tab_text(node):
        return ' '.join(' '.join(node.xpath('.//text()')).split())

    def zdy_zd(self, url, html_text=None, description=''):
        """返回商品页标签页字段：``{标签名: 清洗后的 HTML}``。

        站点把商品描述也渲染成一个标签页，该标签与 ``Description`` 完全重复，
        因此跳过内容与描述相同的标签。
        """
        Tool = self.tool
        if html_text is None:
            response = Tool.get(url, timeout=15)
            if response.status_code != 200:
                return {}
            html_text = response.text
        clean_description = Tool.HTML.clean_product_desc_str(description)
        html = etree.HTML(html_text)
        dic = {}
        for tabs in html.xpath(self.tabs_xpath):
            titles = {
                button.get('id'): self.tab_text(button)
                for button in tabs.xpath(self.tab_button_xpath)
            }
            for panel in tabs.xpath(self.tab_panel_xpath):
                name = titles.get(panel.get('aria-labelledby'), '')
                if not name:
                    continue
                # 站点标签 "Shipping + Returns" 里的 "+" 会生成非法
                # metafield key，这里按同一语义改写为 and
                name = name.replace(' + ', ' and ')
                if name in dic:
                    continue
                value = Tool.HTML.clean_product_desc(panel)
                if not value or value == clean_description:
                    continue
                dic[name] = value
        return dic

    def fetch_product(self, url, category) -> list:
        Tool = self.tool
        handle = Tool.URL.get_handle(url)
        product_url = Tool.URL.add_site(f'/products/{handle}.json')
        try:
            response = Tool.get(product_url, timeout=15)
            if response.status_code != 200:
                Tool.print(f'[ERROR] 商品 JSON 请求失败 {response.status_code}: {url}')
                return []
            product = response.json().get('product')
            if not product:
                return []

            page = Tool.get(url, timeout=15)
            if page.status_code != 200:
                Tool.print(f'[ERROR] 商品页请求失败 {page.status_code}: {url}')
                return []
            if dump_html:
                Tool.HTML.save(page.text, Tool.File.path_add_site(f'ts/3/{handle}.html'))

            custom_key = Tool.custom_key
            if custom_key:
                product[custom_key] = self.zdy_zd(
                    url,
                    page.text,
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
    Pc(
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
        max_threads=10,
        if_wp=if_wp,
    ).run()
    Tool.close()
