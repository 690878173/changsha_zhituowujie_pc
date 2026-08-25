import json
import os
import random
import time
import re
from lxml import etree
from curl_cffi import requests



cookies = {
        'csm-sid': '947-6297101-4100033',
        'x-amz-captcha-1': '1772617896796329',
        'x-amz-captcha-2': 'ENqiMdvDOD6erjCJNDUQvA==',
        'session-id': '146-2519463-0563012',
        'session-id-time': '2082787201l',
        'i18n-prefs': 'USD',
        'lc-main': 'en_US',
        'csm-hit': 'tb:s-X51SGBND7GZP0PKQPBB6|1774514280976&t:1774514282660&adb:adblk_no',
        'ubid-main': '134-5778746-9009123',
        'session-token': 'zNnA7dHxx7l4ZjVGNyOfvZmNW1/4oqm7AtcfIvrZex1FVkYuBkTjxnBWL0Re+0CO4PMxulPWM+fjJaeK32dAOvVylRyaEfHIkWYibc+rQ+bS/kebYk7u05J2f93A4ZtvFzm9iel6yDZQdD3fhs+cEEHuI4CsZnqPPUja62QvKa5pkPAeCTmZFKWHWpecNVaKYJDYc7K7+4ZQphfUxMUyyP4W5cLaMf0x',
        'sp-cdn': '"L5Z9:HK"',
    }

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0',
    'Accept': 'text/html, application/json',
    'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,zh-HK;q=0.7,en-US;q=0.6,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    'X-Requested-With': 'XMLHttpRequest',
    'x-amzn-flow-closure-id': '1774513993',
    'Content-Type': 'application/json',
    'x-amz-amabot-click-attributes': 'disable',
    'x-amz-acp-params': 'tok=eJn3v6pjKWmMceOfeA53zwYMDcpMEF04J-v_rI4iCTo;ts=1774514282590;rid=X51SGBND7GZP0PKQPBB6;d1=012;d2=0;tpm=CGHDB.content-id;ref=bmx_dp',
    'Origin': 'https://www.amazon.com',
    'Alt-Used': 'www.amazon.com',
    'Connection': 'keep-alive',
    'Referer': 'https://www.amazon.com/dp/B0DP18NNVB?th=1',
    # 'Cookie': 'csm-sid=947-6297101-4100033; x-amz-captcha-1=1772617896796329; x-amz-captcha-2=ENqiMdvDOD6erjCJNDUQvA==; session-id=146-2519463-0563012; session-id-time=2082787201l; i18n-prefs=USD; lc-main=en_US; csm-hit=tb:s-X51SGBND7GZP0PKQPBB6|1774514280976&t:1774514282660&adb:adblk_no; ubid-main=134-5778746-9009123; session-token=zNnA7dHxx7l4ZjVGNyOfvZmNW1/4oqm7AtcfIvrZex1FVkYuBkTjxnBWL0Re+0CO4PMxulPWM+fjJaeK32dAOvVylRyaEfHIkWYibc+rQ+bS/kebYk7u05J2f93A4ZtvFzm9iel6yDZQdD3fhs+cEEHuI4CsZnqPPUja62QvKa5pkPAeCTmZFKWHWpecNVaKYJDYc7K7+4ZQphfUxMUyyP4W5cLaMf0x; sp-cdn="L5Z9:HK"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

ck = cookies
hd = headers


def update_amazon_asins(input_path, output_path):
    # 使用 chrome110 模拟真实浏览器指纹
    session = requests.Session(impersonate="chrome120")

    # 精简 Header，只保留最关键的

    dir_path = os.path.dirname(output_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            input_data = json.load(f)

        final_result = {}

        for category_id, asins in input_data.items():
            print(f"\n📂 正在处理分类 ID: {category_id}")
            current_category_set = set(asins)

            for asin in asins:
                url = f'https://www.amazon.com/dp/{asin}?th=1&psc=1'
                print(f"  🌐 访问: {url}")

                try:
                    # 关键点：这里不传入复杂的硬编码 Cookie，让 curl_cffi 自动处理
                    resp = session.get(url, headers=headers,cookies=cookies, timeout=20)

                    if "To discuss automated access" in resp.text or resp.status_code == 503:
                        print("    ❌ 触发验证码或被拦截 (Robot Check)！建议更换代理 IP")
                        continue

                    tree = etree.HTML(resp.text)
                    page_title = tree.xpath('//title/text()')
                    print(f"    📄 页面标题: {page_title[0].strip() if page_title else 'Unknown'}")

                    # --- 方案 A: 原始 XPath ---
                    xpath_expr = '//script[contains(@data-a-state,"twister-plus-desktop-inline-twister-collapse-view-asins-data")]/text()'
                    script_content = tree.xpath(xpath_expr)

                    variants = []
                    if script_content:
                        raw_json = json.loads(script_content[0])
                        variants = raw_json.get("asinsInCollapsedView", [])


                    if variants:
                        current_category_set.update(variants)
                        print(f"    ✅ 成功提取到 {len(variants)} 个关联变体")
                    else:
                        print("    ⚠️ 该页面未发现任何变体数据")

                except Exception as e:
                    print(f"    ❌ 发生异常: {e}")

                time.sleep(3)  # 稍微增加延迟，防止被封

            final_result[category_id] = list(current_category_set)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_result, f, indent=4, ensure_ascii=False)
        print(f"\n✨ 任务完成！")

    finally:
        session.close()

from _ljp.mb.base import GetDetail
from _ljp.mb.model import PageModel

class YMXStep2(GetDetail):
    def fetch_page(self, P:PageModel, params):

        url = f'https://www.amazon.com/dp/{P.url}?th=1&psc=1'
        print(f"  🌐 访问: {url}")
        try:
            res = self.Tool.get(url,headers=headers,cookies=cookies,timeout=20)

            if "To discuss automated access" in res.text or res.status_code == 503:
                print("    ❌ 触发验证码或被拦截 (Robot Check)！建议更换代理 IP")
                P.set_fail()
                return [] ,None

            tree = etree.HTML(res.text)
            page_title = tree.xpath('//title/text()')
            print(f"    📄 页面标题: {page_title[0].strip() if page_title else 'Unknown'}")

            # --- 方案 A: 原始 XPath ---
            xpath_expr = '//script[contains(@data-a-state,"twister-plus-desktop-inline-twister-collapse-view-asins-data")]/text()'
            script_content = tree.xpath(xpath_expr)

            variants = []
            if script_content:
                raw_json = json.loads(script_content[0])
                variants = raw_json.get("asinsInCollapsedView", [])

            if variants:
                print(f"    ✅ 成功提取到 {len(variants)} 个关联变体")
            else:
                P.set_end()
                print("    ⚠️ 该页面未发现任何变体数据")

            time.sleep(2)

            return variants, None



        except Exception as e:
            print(f"    ❌ 发生异常: {e}")




Step2 = update_amazon_asins

if __name__ == '__main__':
    INPUT_FILE = r"data/1.json"
    OUTPUT_FILE = r"data/detail_url.json"
    update_amazon_asins(INPUT_FILE, OUTPUT_FILE)
