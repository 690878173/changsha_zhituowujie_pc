import json
import re
from idlelib.run import flush_stdout

from lxml import etree
from config import Tool

# 文件路径配置
input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site("res/result.csv")
fail_file = Tool.File.path_add_site('data/fail.json')

catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
# 携带原始url输出文件
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

# 测试数据条数 (None = 全部抓取)
ts_num = None

catch_save_num = None
# URL黑名单
skip_input_url_ls = []
# 未实现字段
skip_output_url_ls = []

cookies = {
    'guest_token': 'eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaEpJaHRIYTFKTmMzaFBSbGhyUzNKVVQwa3hkM2Q0Y1dSM0Jqb0dSVVk9IiwiZXhwIjpudWxsLCJwdXIiOiJjb29raWUuZ3Vlc3RfdG9rZW4ifX0%3D--12aaacad48e2c95f54576a6315888a44cb2ac78e',
    '_session_id': '0d7090400ad1aee07a5cb97124fbb701',
    'FPC': 'f76a1684-4d46-4c2e-b62a-2794f8111675',
    '__attn_eat_id': '92fde8ec7b15475f8fb23c87fbeddaf5',
    '_ga': 'GA1.1.1096728710.1787535863',
    'has_visited_before': 'true',
    'polaris_consent_settings': '{"clientId":"20551361-0179-4fd3-cd46-2fa8423bbcde","implicit":true,"analyticsPermitted":true,"personalizationPermitted":true,"adsPermitted":true,"notOptedOut":true,"essentialPermitted":true}',
    'sms_prompt_last_viewed': '1787535863193',
    '__attentive_id': '6a7572e18b8546859c24b07513719b2c',
    '__attentive_cco': '1787535863540',
    '_attn_bopd_': 'browser',
    'us_privacy': '1YNN',
    'fingerprint-uuid': '6a3c4b5c-f3dd-4be0-9a65-7849a744aaed',
    'gleen-faq-fingerprint-uuid': '6a3c4b5c-f3dd-4be0-9a65-7849a744aaed',
    '_swb': '9d30ae23-bd28-4240-b0ee-4f77135497a3',
    '__ssid': '3ea71818-a04c-4e8e-b603-a6495ca5441d',
    '_ketch_consent_v1_': 'eyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIl19LCJhbmFseXRpY3MiOnsic3RhdHVzIjoiZ3JhbnRlZCIsImNhbm9uaWNhbFB1cnBvc2VzIjpbImFuYWx5dGljcyJdfSwiZXNzZW50aWFsX3NlcnZpY2VzIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJlc3NlbnRpYWxfc2VydmljZXMiXX19',
    'styliticsWidgetSession': '14011f24-19f6-4f6b-8174-93e1ccb9e5b8',
    'yotpo_pixel': 'b0c2b6c9-9afe-4c48-9954-2ecf71e74c0f',
    'signup_exit_intent': 'true',
    'tatari-session-cookie': '7e5fcc21-1c0f-f870-b169-7bfef17ddd9e',
    '__attentive_session_id': '43703b4a305b47f3a088ea1549069a38',
    '__attentive_dv': '1',
    '__attentive_ss_referrer': 'ORGANIC',
    '_sp_ses.accb': '*',
    '_sp_id.accb': 'b9d6a6b74b98d1b3.1787536390.5.1787554576.1787550221',
    'suppress_gate_for_visit': 'true',
    'cf_clearance': 'wdrPTEvlO5wiy_QdC.VxZuJRRXyzi5e7CPRrSscn8TA-1787555095-1.2.1.1-mOLzV.8TPFlTyd6dxFlw8YpE2_zKYadMXGDRFVrslMMnpQSiDqsMalEcxvE9JGWOIqn3pqKEUTx6WixIBhoiaFJHb0.KDD3pLhmQ_NH9l8Y5YrDY4aggee7_l0cOMKiIa5Lcpy1sCI8dA4vSgFoSK_hyKsTXVXwlpiVe8JS0JXcj1xw5K5.1lovr8hmty1st1lC8JlMGkWf2iZI8_f6zrxB5HfPkLJiEDWb.9soMLGUQqRdG3cCIeCKt4Ly3UjtaBplsHuhrO4L1q3k4_dWqdmsP9XSazgKNUp_Kk8MhcmkMZ9otUx1X_IBdtxnEah7vwwI.HumzLPa2UA_02coq4H9uX.JnR9tbnk5GpsWT7EQ',
    '__cf_bm': 'iXkniuInxKUlr8b_NmSIMnbSjNMc4jH7xcKa9PAo7WY-1787555095.1424365-1.0.1.1-ESsllMGGNDYrPkeUuxfCrM3ePYaFOhypk_MeroWu5Z_WCkKCK8l4XRxzWhJaTcJJVlz5xefNJoYDdjC250xyPWWhbxbkoFjgol_3zwvUerQwvkY_QWHCVUwnXlraBmvD',
    '_gcl_au': '1.1.1469880196.1787535861.-.-.1787535862.1524398406.1787535863.1787555412',
    '_ga_59L0QDKBLT': 'GS2.1.s1787553675$o3$g1$t1787555412$j59$l0$h0$drRf_qjtD2W9L-DVRQliP34KnXJ4yjsB0_A',
    '_ga_KDVZE23CS0': 'GS2.1.s1787553675$o3$g1$t1787555412$j59$l0$h675141687$dlDwBIeriiiGSKzj37IIN7lEa2pa1yJaNHw',
    'tatari-cookie-test': '45541386',
    '_attn_': 'eyJ1Ijoie1wiY29cIjoxNzg3NTM1ODYzNTQwLFwidW9cIjoxNzg3NTM1ODYzNTQwLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjZhNzU3MmUxOGI4NTQ2ODU5YzI0YjA3NTEzNzE5YjJjXCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg3NTU1NDE0MzA2LFwidW9cIjoxNzg3NTU1NDE0MzA2LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL3NtYXpuLmh1Y2tiZXJyeS5jb21cIn0ifQ==',
    '__attentive_pv': '10',
    '_swb_consent_': 'eyJjb2xsZWN0ZWRBdCI6MTc4NzUzNTg2NSwiY29udHJvbGxlckNvZGUiOiIiLCJlbnZpcm9ubWVudENvZGUiOiJwcm9kdWN0aW9uIiwiaGFzVW5yZWNvcmRlZE9wdEluQ29uc2VudCI6ZmFsc2UsImlkZW50aXRpZXMiOnsic3diX2h1Y2tiZXJyeSI6IjlkMzBhZTIzLWJkMjgtNDI0MC1iMGVlLTRmNzcxMzU0OTdhMyJ9LCJpbnRlcmFjdGl2ZSI6ZmFsc2UsImp1cmlzZGljdGlvbkNvZGUiOiJjcHJhIiwicHJvcGVydHlDb2RlIjoiaHVja2JlcnJ5IiwicHVycG9zZXMiOnsiYW5hbHl0aWNzIjp7ImFsbG93ZWQiOiJ0cnVlIiwibGVnYWxCYXNpc0NvZGUiOiJjb25zZW50X29wdG91dCJ9LCJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIjp7ImFsbG93ZWQiOiJ0cnVlIiwibGVnYWxCYXNpc0NvZGUiOiJjb25zZW50X29wdG91dCJ9LCJlc3NlbnRpYWxfc2VydmljZXMiOnsiYWxsb3dlZCI6InRydWUiLCJsZWdhbEJhc2lzQ29kZSI6ImRpc2Nsb3N1cmUifX0sInNldENvbnNlbnRSZXF1aXJlZCI6ZmFsc2UsImNhY2hlZEF0IjoxNzg3NTU1NDE1fQ%3D%3D',
    'apt_pixel': 'eyJkZXZpY2VJZCI6IjgwNzUzM2Q5LWQ1OGMtNDFiYi1hNmQzLWNiYTQ4YzVjOGQ2ZiIsInVzZXJJZCI6bnVsbCwiZXZlbnRJZCI6NTcsImxhc3RFdmVudFRpbWUiOjE3ODc1NTU0MTcyOTAsImNoZWNrb3V0Ijp7ImJyYW5kIjoiY2FzaGFwcGFmdGVycGF5In19',
    'amp_f24a38': '0GrpYevfr9mIYm6oMSoK7f...1k0p7vflj.1k0p9m36l.0.0.0',
}

headers = {
    'accept': 'text/css,*/*;q=0.1',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0',
    'referer': 'https://huckberry.com/store/northworks/category/p/99190-murano-dead-stock-beads-necklace',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'style',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    # 'cookie': 'guest_token=eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaEpJaHRIYTFKTmMzaFBSbGhyUzNKVVQwa3hkM2Q0Y1dSM0Jqb0dSVVk9IiwiZXhwIjpudWxsLCJwdXIiOiJjb29raWUuZ3Vlc3RfdG9rZW4ifX0%3D--12aaacad48e2c95f54576a6315888a44cb2ac78e; _session_id=0d7090400ad1aee07a5cb97124fbb701; FPC=f76a1684-4d46-4c2e-b62a-2794f8111675; __attn_eat_id=92fde8ec7b15475f8fb23c87fbeddaf5; _ga=GA1.1.1096728710.1787535863; has_visited_before=true; polaris_consent_settings={"clientId":"20551361-0179-4fd3-cd46-2fa8423bbcde","implicit":true,"analyticsPermitted":true,"personalizationPermitted":true,"adsPermitted":true,"notOptedOut":true,"essentialPermitted":true}; sms_prompt_last_viewed=1787535863193; __attentive_id=6a7572e18b8546859c24b07513719b2c; __attentive_cco=1787535863540; _attn_bopd_=browser; us_privacy=1YNN; fingerprint-uuid=6a3c4b5c-f3dd-4be0-9a65-7849a744aaed; gleen-faq-fingerprint-uuid=6a3c4b5c-f3dd-4be0-9a65-7849a744aaed; _swb=9d30ae23-bd28-4240-b0ee-4f77135497a3; __ssid=3ea71818-a04c-4e8e-b603-a6495ca5441d; _ketch_consent_v1_=eyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIl19LCJhbmFseXRpY3MiOnsic3RhdHVzIjoiZ3JhbnRlZCIsImNhbm9uaWNhbFB1cnBvc2VzIjpbImFuYWx5dGljcyJdfSwiZXNzZW50aWFsX3NlcnZpY2VzIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJlc3NlbnRpYWxfc2VydmljZXMiXX19; styliticsWidgetSession=14011f24-19f6-4f6b-8174-93e1ccb9e5b8; yotpo_pixel=b0c2b6c9-9afe-4c48-9954-2ecf71e74c0f; signup_exit_intent=true; tatari-session-cookie=7e5fcc21-1c0f-f870-b169-7bfef17ddd9e; __attentive_session_id=43703b4a305b47f3a088ea1549069a38; __attentive_dv=1; __attentive_ss_referrer=ORGANIC; _sp_ses.accb=*; _sp_id.accb=b9d6a6b74b98d1b3.1787536390.5.1787554576.1787550221; suppress_gate_for_visit=true; cf_clearance=wdrPTEvlO5wiy_QdC.VxZuJRRXyzi5e7CPRrSscn8TA-1787555095-1.2.1.1-mOLzV.8TPFlTyd6dxFlw8YpE2_zKYadMXGDRFVrslMMnpQSiDqsMalEcxvE9JGWOIqn3pqKEUTx6WixIBhoiaFJHb0.KDD3pLhmQ_NH9l8Y5YrDY4aggee7_l0cOMKiIa5Lcpy1sCI8dA4vSgFoSK_hyKsTXVXwlpiVe8JS0JXcj1xw5K5.1lovr8hmty1st1lC8JlMGkWf2iZI8_f6zrxB5HfPkLJiEDWb.9soMLGUQqRdG3cCIeCKt4Ly3UjtaBplsHuhrO4L1q3k4_dWqdmsP9XSazgKNUp_Kk8MhcmkMZ9otUx1X_IBdtxnEah7vwwI.HumzLPa2UA_02coq4H9uX.JnR9tbnk5GpsWT7EQ; __cf_bm=iXkniuInxKUlr8b_NmSIMnbSjNMc4jH7xcKa9PAo7WY-1787555095.1424365-1.0.1.1-ESsllMGGNDYrPkeUuxfCrM3ePYaFOhypk_MeroWu5Z_WCkKCK8l4XRxzWhJaTcJJVlz5xefNJoYDdjC250xyPWWhbxbkoFjgol_3zwvUerQwvkY_QWHCVUwnXlraBmvD; _gcl_au=1.1.1469880196.1787535861.-.-.1787535862.1524398406.1787535863.1787555412; _ga_59L0QDKBLT=GS2.1.s1787553675$o3$g1$t1787555412$j59$l0$h0$drRf_qjtD2W9L-DVRQliP34KnXJ4yjsB0_A; _ga_KDVZE23CS0=GS2.1.s1787553675$o3$g1$t1787555412$j59$l0$h675141687$dlDwBIeriiiGSKzj37IIN7lEa2pa1yJaNHw; tatari-cookie-test=45541386; _attn_=eyJ1Ijoie1wiY29cIjoxNzg3NTM1ODYzNTQwLFwidW9cIjoxNzg3NTM1ODYzNTQwLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjZhNzU3MmUxOGI4NTQ2ODU5YzI0YjA3NTEzNzE5YjJjXCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg3NTU1NDE0MzA2LFwidW9cIjoxNzg3NTU1NDE0MzA2LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL3NtYXpuLmh1Y2tiZXJyeS5jb21cIn0ifQ==; __attentive_pv=10; _swb_consent_=eyJjb2xsZWN0ZWRBdCI6MTc4NzUzNTg2NSwiY29udHJvbGxlckNvZGUiOiIiLCJlbnZpcm9ubWVudENvZGUiOiJwcm9kdWN0aW9uIiwiaGFzVW5yZWNvcmRlZE9wdEluQ29uc2VudCI6ZmFsc2UsImlkZW50aXRpZXMiOnsic3diX2h1Y2tiZXJyeSI6IjlkMzBhZTIzLWJkMjgtNDI0MC1iMGVlLTRmNzcxMzU0OTdhMyJ9LCJpbnRlcmFjdGl2ZSI6ZmFsc2UsImp1cmlzZGljdGlvbkNvZGUiOiJjcHJhIiwicHJvcGVydHlDb2RlIjoiaHVja2JlcnJ5IiwicHVycG9zZXMiOnsiYW5hbHl0aWNzIjp7ImFsbG93ZWQiOiJ0cnVlIiwibGVnYWxCYXNpc0NvZGUiOiJjb25zZW50X29wdG91dCJ9LCJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIjp7ImFsbG93ZWQiOiJ0cnVlIiwibGVnYWxCYXNpc0NvZGUiOiJjb25zZW50X29wdG91dCJ9LCJlc3NlbnRpYWxfc2VydmljZXMiOnsiYWxsb3dlZCI6InRydWUiLCJsZWdhbEJhc2lzQ29kZSI6ImRpc2Nsb3N1cmUifX0sInNldENvbnNlbnRSZXF1aXJlZCI6ZmFsc2UsImNhY2hlZEF0IjoxNzg3NTU1NDE1fQ%3D%3D; apt_pixel=eyJkZXZpY2VJZCI6IjgwNzUzM2Q5LWQ1OGMtNDFiYi1hNmQzLWNiYTQ4YzVjOGQ2ZiIsInVzZXJJZCI6bnVsbCwiZXZlbnRJZCI6NTcsImxhc3RFdmVudFRpbWUiOjE3ODc1NTU0MTcyOTAsImNoZWNrb3V0Ijp7ImJyYW5kIjoiY2FzaGFwcGFmdGVycGF5In19; amp_f24a38=0GrpYevfr9mIYm6oMSoK7f...1k0p7vflj.1k0p9m36l.0.0.0',
}

flush = False

# CSV输出表头,默认就应该为None，表头后续会处理
fieldnames = None

max_threads = 2

from _ljp.mb.zj import Step3

class Pc(Step3):


    def fetch_product(self, url, category):
        """请求并解析单个商品。
        """
        if 'gift-card-' in url:
            return []
        res = Tool.get(url,headers=headers,cookies=cookies)

        tx = res.text

        match = re.search(r'__PRELOADED_STATE__\.product\s*=\s*({.*?});', res.text, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            T = _T(url, category, data)

            ls = T.run()

            return ls


        else:
            Tool.HTML.save(tx)
            Tool.print(f'找不到产品数据')

            return []






class _T:
    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.typ = 'simple'
        self.html = self.res_text
        self.data = res_text

    def get_main_name(self, html):
        try:
            # TODO 业务xpath
            data = self.data
            name = data['name']
            self.name = name
            return name
        except Exception as e:
            raise ValueError(f'获取主名称失败:{e}') from e


    def get_main_price(self, html):
        try:
            # TODO 业务xpath
            data = self.data
            price = data['displayPrice']
            self.main_price = price
            return price
        except Exception as e:
            raise ValueError(f'获取价格失败:{e}')
            return ""

    def get_main_sku(self, html):
        try:
            # TODO 业务xpath
            data = self.data
            sku = data['sku']
            self.sku = sku
            return sku
        except Exception as e:
            Tool.print(f'获取sku失败:{e}')
            return ""

    def get_main_desc(self, html):
        try:
            # TODO 业务xpath
            data = self.data
            desc = data['breakoutContent']
            desc_t = data['breakoutTitle']

            desc = f'''
                                <div>
                                        <div>{desc}</div>
                                        <div>{desc_t}</div>
                                    </div>

                                '''

            desc = etree.HTML(desc)
            self.desc = desc
            return self.desc
        except Exception as e:
            Tool.print(f'获取描述失败:{e}')
            return ""

    def get_main_imgs(self, html):
        try:
            # TODO 业务xpath，返回图片列表
            data = self.data
            images = data['images']
            ls = [i['url'] for i in images]
            self.main_imgs = ls
            return ls
        except Exception as e:
            Tool.print(f'获取图片失败:{e}')
            return []

    def get_att(self,html):
        try:
            data = self.data
            descriptionBlocks = data['descriptionBlocks']
            att = {}
            for descriptionBlock in descriptionBlocks:
                title = descriptionBlock['title']
                content = descriptionBlock['content']
                for k in ['Features', 'Sizing', 'Materials']:
                    if k in title:
                        att[k] = f'<div>{content}</div>'
                        break
            self.main_att = att
            return att
        except Exception as e:
            Tool.print(f'获取属性失败:{e}')
            return {}

    def check_cob(self, html):
        """判断是否存在变体商品"""
        try:
            data = self.data
            variants = data['variants']

            return variants
        except Exception as e:
            Tool.print(f'检测变体失败:{e}')
            return False

    def get_cobs(self, html):
        """抓取所有变体数据"""
        try:
            data = self.data
            variants = data['variants']
            att = {}
            for variant in variants:
                att['sku'] = variant['sku']
                att['size'] = variant['size']
                att['color'] = variant['color']
                att['inStock'] = variant['inStock']
            cobs = []
            s_ls = []  # TODO 变体节点列表xpath
            for variant in data['variants']:
                # TODO 提取变体字段
                cob_imgs_ls = self.main_imgs
                cob_name = self.name
                cob_price = self.main_price
                cob_sku = variant['sku']
                cob_att = {
                    'size':variant['size'],
                    'color':variant['color'],
                }

                cob_desc = Tool.HTML.clean_product_desc(self.desc)
                cob_price = Tool.clean_price(cob_price)
                cob_imgs = Tool.Product.clean_imgs(cob_imgs_ls)
                cob = Tool.Product.Variation(
                    url=self.url, cat=self.category, imgs=cob_imgs,
                    name=cob_name, desc=cob_desc, price=cob_price,
                    sku=cob_sku, att=cob_att,parent=self.sku,stock=variant['inStock'],**self.main_att
                ).to_dic()
                cobs.append(cob)
            return cobs
        except Exception as e:
            Tool.print(f'获取变体数据失败:{e}')
            return []

    def run(self) -> list:
        try:
            """统一入口：执行解析，返回标准化产品字典列表"""
            main_name = self.get_main_name(self.html)
            main_price = self.get_main_price(self.html)
            main_sku = self.get_main_sku(self.html)
            main_desc = self.get_main_desc(self.html)
            main_imgs_ls = self.get_main_imgs(self.html)
            main_att = self.get_att(self.html)



            main_desc = Tool.HTML.clean_product_desc(main_desc)
            main_price = Tool.clean_price(main_price)
            main_img = Tool.Product.clean_imgs(main_imgs_ls)

            if self.check_cob(self.html):
                self.typ = 'variation'

            if self.typ == 'simple':
                product = Tool.Product.Simple(
                    url=self.url, cat=self.category, imgs=main_img,
                    name=main_name, sku=main_sku, price=main_price,
                    desc=main_desc,**main_att
                ).to_dic()
                return [product]

            return self.get_cobs(self.html)
        except Exception as e:
            Tool.print(f'run 解析失败:{e}')
            return []






if __name__ == '__main__':
    pc = Pc(tool=Tool,
            input_path=input_file,
            output_path=output_file,
            fail_file=fail_file,
            skip_input_url_ls=skip_input_url_ls,
            skip_output_url_ls=skip_output_url_ls,
            ts_num=ts_num,
            fieldnames=fieldnames,
            catch_path=catch_path,
            index_path=index_path,
            output_ts_file=output_ts_file,
            flush=flush,
            max_threads=max_threads,
            catch_save_num=catch_save_num
            )
    pc.run()
