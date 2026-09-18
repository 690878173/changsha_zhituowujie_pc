import json
import re

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
    'visid_incap_3320710': 'KPAX1xC4RJ+lO2Y1SaFiL+dElmoAAAAAQUIPAAAAAABkFNQQL1Yyh6/ZulljxtOp',
    '_pxvid': '5363240a-a5b4-11f1-b856-e0f5e8c542e5',
    '_gcl_au': '1.1.1467123164.1788232939',
    '_ga': 'GA1.1.1496659026.1788232939',
    'FPID': 'FPID2.2.k8XvDQeZvUAfEEJTfCxp0CT%2BcBsuwXUl7rM%2FQH8MrAc%3D.1788232939',
    'ty_id': 'd81834d7-6fe2-417a-265a-d185529e2351',
    'OptanonAlertBoxClosed': '2026-09-01T03:23:21.629Z',
    'OnetrustLite': 'C0003',
    'FPAU': '1.1.1467123164.1788232939',
    'ALGOLIA_USER_TOKEN': 'e304883a-6127-40da-a1d6-2730eb1df003',
    'OTConsent': '1',
    '_fbp': 'fb.1.1788234301642.1331596859',
    '_pin_unauth': 'dWlkPU9XSTFabVUxTm1NdE9ERmlOUzAwTURoakxUZ3haak10TWpRMlpqUmpNamRpWW1NNA',
    'BVBRANDID': '5c5a1395-efa2-43b5-9784-e6ccc4450aef',
    'ServerAwinChannelCookie': 'direct',
    '_pxhd': '9e-dNqqSBB4XQNzhjBubJSYXHomVWFYg-PyqKoSiDYWr8FCbf-RZ-9H6M-NAcsTHvAP-hesAt0PZk12B6CaMDw==:uw4DWuauK/yBSdBUq0NxQrgjawVBgqTzRkVEp-P4GDJijpoG6l2duGQxQdGsu6kwnRKDLpAgN1ereiA6T7lM/kAugPzYIzwbTjC/cjPBL2Y=',
    'incap_ses_228_3320710': 'NAgWFIvpLFFOinNxgAUqA/CFm2oAAAAAhlnNMMUBCar5pYmX8EPm6Q==',
    'ALGOLIA_REASON_CODE': 'NOT_LOGGED_IN',
    '_cs_mk_pa': '0.22353468108548047_1788577266804',
    'ALGOLIA_API_KEY': 'MjU2N2ZlZTBkYzJmMzI1YmFiZjY5N2RkZjMzYTI0MjQzMjM4NTJlYjY2ZDhhNmVmZWViYWQzM2U4ZGM3M2UzN2ZpbHRlcnM9Tk9UJTIwbm90VmlzaWJsZUJ5UmVhc29uQ29kZSUzQUQyQyZydWxlQ29udGV4dHM9c3ViU2VnbWVudC1EMkMmdXNlclRva2VuPWUzMDQ4ODNhLTYxMjctNDBkYS1hMWQ2LTI3MzBlYjFkZjAwMyZ2YWxpZFVudGlsPTE3ODg2MjA0Njc=',
    'FPLC': 'Un4E6lpmuTvn%2BsnOS39TWhfxSbGnnvkiSlQ%2FCBZNu9fD4qkDa0sbIh7dhdJJ8CbUe2suCuTECoWv4DF8WS3U7SbHa3u7xucwNgfSVUPHCPHkIqyIo0BbmZ1yPgXAKQ%3D%3D',
    'ty_session': 'true',
    'ty_ead': 'eyJjdXJyZW50Q2FtcGFpZ24iOnsiZGF0ZSI6MTc4ODIzMjk0MDYwNSwicmVmZXJyZXIiOm51bGwsInRhcmdldCI6Imh0dHBzOi8vd3d3LnNhbG9tb24uY29tL2VuLXVzIn0sInJlZmVycmVyIjoiIiwidGFyZ2V0IjoiaHR0cHM6Ly93d3cuc2Fsb21vbi5jb20vZW4tdXMvcHJvZHVjdC9hZXJvLWJsYXplLTQtbGkxNDE3L0w0NTM5NzkwMCJ9',
    'BVBRANDSID': '741bcc2a-6ab5-4bea-9b27-9fb0a83f1b38',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Sat+Sep+05+2026+11%3A07%3A31+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202606.1.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&hosts=&genVendors=V8%3A0%2CV28%3A0%2CV43%3A0%2CV18%3A0%2CV10%3A0%2CV42%3A0%2CV4%3A0%2CV35%3A0%2CV44%3A0%2CV12%3A0%2CV19%3A0%2CV39%3A0%2CV40%3A0%2CV21%3A0%2CV22%3A0%2CV2%3A0%2CV41%3A0%2CV37%3A0%2CV25%3A0%2CV32%3A0%2CV14%3A0%2CV9%3A0%2CV3%3A0%2CV38%3A0%2CV15%3A0%2CV24%3A0%2CV5%3A0%2C&consentId=ba967cf0-3c7a-495c-9381-93e365fef89b&interactionCount=2&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&crTime=1788233002792&fclco=&lastConsentTs=1788233001&intType=9&geolocation=US%3BCA&AwaitingReconsent=false',
    '_ga_XXXXXXX': 'GS2.1.s1788577267$o3$g1$t1788577652$j40$l0$h1957796857',
    '_px3': '05cf14dc348a495e60cd71333e58a73983aa0f1924f78ac7959a270eee1d82e4:PGT6IIE4houcz26dXbkrc9L3hVb0rPk546BPmUHzhF55VTWwsvPyuLCGbnhHgCnSoH8LEg3LguevSLZL1O0pRQ==:1000:OTk/oLDLYjCY6hoh8/2IJfTXpwJTzVH9YjL9yQVjvIPqJFcb0o/MJBAQWo8JF+rfUNOIr9x4QNPGyZ3ruNG3Yh/pMkhBGpWHgRCtJA79DeX3bZmOahrw/OTS72/VgeGaM4wtAavZoWdanL3ASgQ+GZoq6rKZb0CKo7t1X7ySfFgnV/2cTFlaLJVLm0eRTuHJMXlvjAgdiRGZgHupJ5/6KeTqfaGu1+GotE/dxXDvmwiVKwKQY+2uyHu1hPhj8y//lC+gh5Hj5OIcNP61wUTZwMPQsOl95gl7GDhkVAcKeDTnp8cM1gqv2UjicysBDQS0FYxKl9ltSegxlIgR040xKtNteOIfoKK9h6uh5blMqK3rvWIy6i0mxlJL6nRLzjJos3GxLDgMobqJ1SWE50jFFnyuA+tV3dOnGu2BsTVHv3mM7PKkd9b1bWqKFFt03mregUWdgPIXx3WYLAnVqWB11+/22VlULInQJy47PDbDE5n+UTzpJJWMu3Z1xsvRMIg/',
    '_px2': 'eyJ1IjoiZWYwZTg1NTAtYThkNi0xMWYxLWFkYzktMzE0NTRiMGJkMDM4IiwidiI6IjUzNjMyNDBhLWE1YjQtMTFmMS1iODU2LWUwZjVlOGM1NDJlNSIsInQiOjE3ODg1Nzc5NTM3NTYsImgiOiJiZTIwZTllMjA4ZTEwNzkyZjdmNDFmM2NkOWRiYWRmM2ZhYjIyYWYyODU2Y2ViYTZiZDIxMjA2ZDg1MGFiZmM1In0=',
    'pxcts': 'wpnsF1P5-a5xEyg5abueplP6PB2CLRM-iyijKc74bjA=:ktvYZJqNKsCOl5WIu7DAwQenwlSmfNWXSincLh6yUEimVHbQypNP-hqWO1kceb-un5CgOJmNN959PlsQw1lhCASCxOyRDl/K/5skFzFFZEIaaobWmb0qVtwqyW-qm14bZoG7QCeSCefQBc95fV2VzVQHldjnBiYAuCILPSEOqYd/1vNJTLOYgI4fTR3YVyS2',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'visid_incap_3320710=KPAX1xC4RJ+lO2Y1SaFiL+dElmoAAAAAQUIPAAAAAABkFNQQL1Yyh6/ZulljxtOp; _pxvid=5363240a-a5b4-11f1-b856-e0f5e8c542e5; _gcl_au=1.1.1467123164.1788232939; _ga=GA1.1.1496659026.1788232939; FPID=FPID2.2.k8XvDQeZvUAfEEJTfCxp0CT%2BcBsuwXUl7rM%2FQH8MrAc%3D.1788232939; ty_id=d81834d7-6fe2-417a-265a-d185529e2351; OptanonAlertBoxClosed=2026-09-01T03:23:21.629Z; OnetrustLite=C0003; FPAU=1.1.1467123164.1788232939; ALGOLIA_USER_TOKEN=e304883a-6127-40da-a1d6-2730eb1df003; OTConsent=1; _fbp=fb.1.1788234301642.1331596859; _pin_unauth=dWlkPU9XSTFabVUxTm1NdE9ERmlOUzAwTURoakxUZ3haak10TWpRMlpqUmpNamRpWW1NNA; BVBRANDID=5c5a1395-efa2-43b5-9784-e6ccc4450aef; ServerAwinChannelCookie=direct; _pxhd=9e-dNqqSBB4XQNzhjBubJSYXHomVWFYg-PyqKoSiDYWr8FCbf-RZ-9H6M-NAcsTHvAP-hesAt0PZk12B6CaMDw==:uw4DWuauK/yBSdBUq0NxQrgjawVBgqTzRkVEp-P4GDJijpoG6l2duGQxQdGsu6kwnRKDLpAgN1ereiA6T7lM/kAugPzYIzwbTjC/cjPBL2Y=; incap_ses_228_3320710=NAgWFIvpLFFOinNxgAUqA/CFm2oAAAAAhlnNMMUBCar5pYmX8EPm6Q==; ALGOLIA_REASON_CODE=NOT_LOGGED_IN; _cs_mk_pa=0.22353468108548047_1788577266804; ALGOLIA_API_KEY=MjU2N2ZlZTBkYzJmMzI1YmFiZjY5N2RkZjMzYTI0MjQzMjM4NTJlYjY2ZDhhNmVmZWViYWQzM2U4ZGM3M2UzN2ZpbHRlcnM9Tk9UJTIwbm90VmlzaWJsZUJ5UmVhc29uQ29kZSUzQUQyQyZydWxlQ29udGV4dHM9c3ViU2VnbWVudC1EMkMmdXNlclRva2VuPWUzMDQ4ODNhLTYxMjctNDBkYS1hMWQ2LTI3MzBlYjFkZjAwMyZ2YWxpZFVudGlsPTE3ODg2MjA0Njc=; FPLC=Un4E6lpmuTvn%2BsnOS39TWhfxSbGnnvkiSlQ%2FCBZNu9fD4qkDa0sbIh7dhdJJ8CbUe2suCuTECoWv4DF8WS3U7SbHa3u7xucwNgfSVUPHCPHkIqyIo0BbmZ1yPgXAKQ%3D%3D; ty_session=true; ty_ead=eyJjdXJyZW50Q2FtcGFpZ24iOnsiZGF0ZSI6MTc4ODIzMjk0MDYwNSwicmVmZXJyZXIiOm51bGwsInRhcmdldCI6Imh0dHBzOi8vd3d3LnNhbG9tb24uY29tL2VuLXVzIn0sInJlZmVycmVyIjoiIiwidGFyZ2V0IjoiaHR0cHM6Ly93d3cuc2Fsb21vbi5jb20vZW4tdXMvcHJvZHVjdC9hZXJvLWJsYXplLTQtbGkxNDE3L0w0NTM5NzkwMCJ9; BVBRANDSID=741bcc2a-6ab5-4bea-9b27-9fb0a83f1b38; OptanonConsent=isGpcEnabled=0&datestamp=Sat+Sep+05+2026+11%3A07%3A31+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202606.1.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&hosts=&genVendors=V8%3A0%2CV28%3A0%2CV43%3A0%2CV18%3A0%2CV10%3A0%2CV42%3A0%2CV4%3A0%2CV35%3A0%2CV44%3A0%2CV12%3A0%2CV19%3A0%2CV39%3A0%2CV40%3A0%2CV21%3A0%2CV22%3A0%2CV2%3A0%2CV41%3A0%2CV37%3A0%2CV25%3A0%2CV32%3A0%2CV14%3A0%2CV9%3A0%2CV3%3A0%2CV38%3A0%2CV15%3A0%2CV24%3A0%2CV5%3A0%2C&consentId=ba967cf0-3c7a-495c-9381-93e365fef89b&interactionCount=2&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&crTime=1788233002792&fclco=&lastConsentTs=1788233001&intType=9&geolocation=US%3BCA&AwaitingReconsent=false; _ga_XXXXXXX=GS2.1.s1788577267$o3$g1$t1788577652$j40$l0$h1957796857; _px3=05cf14dc348a495e60cd71333e58a73983aa0f1924f78ac7959a270eee1d82e4:PGT6IIE4houcz26dXbkrc9L3hVb0rPk546BPmUHzhF55VTWwsvPyuLCGbnhHgCnSoH8LEg3LguevSLZL1O0pRQ==:1000:OTk/oLDLYjCY6hoh8/2IJfTXpwJTzVH9YjL9yQVjvIPqJFcb0o/MJBAQWo8JF+rfUNOIr9x4QNPGyZ3ruNG3Yh/pMkhBGpWHgRCtJA79DeX3bZmOahrw/OTS72/VgeGaM4wtAavZoWdanL3ASgQ+GZoq6rKZb0CKo7t1X7ySfFgnV/2cTFlaLJVLm0eRTuHJMXlvjAgdiRGZgHupJ5/6KeTqfaGu1+GotE/dxXDvmwiVKwKQY+2uyHu1hPhj8y//lC+gh5Hj5OIcNP61wUTZwMPQsOl95gl7GDhkVAcKeDTnp8cM1gqv2UjicysBDQS0FYxKl9ltSegxlIgR040xKtNteOIfoKK9h6uh5blMqK3rvWIy6i0mxlJL6nRLzjJos3GxLDgMobqJ1SWE50jFFnyuA+tV3dOnGu2BsTVHv3mM7PKkd9b1bWqKFFt03mregUWdgPIXx3WYLAnVqWB11+/22VlULInQJy47PDbDE5n+UTzpJJWMu3Z1xsvRMIg/; _px2=eyJ1IjoiZWYwZTg1NTAtYThkNi0xMWYxLWFkYzktMzE0NTRiMGJkMDM4IiwidiI6IjUzNjMyNDBhLWE1YjQtMTFmMS1iODU2LWUwZjVlOGM1NDJlNSIsInQiOjE3ODg1Nzc5NTM3NTYsImgiOiJiZTIwZTllMjA4ZTEwNzkyZjdmNDFmM2NkOWRiYWRmM2ZhYjIyYWYyODU2Y2ViYTZiZDIxMjA2ZDg1MGFiZmM1In0=; pxcts=wpnsF1P5-a5xEyg5abueplP6PB2CLRM-iyijKc74bjA=:ktvYZJqNKsCOl5WIu7DAwQenwlSmfNWXSincLh6yUEimVHbQypNP-hqWO1kceb-un5CgOJmNN959PlsQw1lhCASCxOyRDl/K/5skFzFFZEIaaobWmb0qVtwqyW-qm14bZoG7QCeSCefQBc95fV2VzVQHldjnBiYAuCILPSEOqYd/1vNJTLOYgI4fTR3YVyS2',
}

flush = False

# CSV输出表头,默认就应该为None，表头后续会处理
fieldnames = None

max_threads = 2

from _ljp.mb.zj import Get_Product

import hashlib

def generate_unique_id(str1: str, str2: str) -> str:
    """
    使用 SHA256 生成固定长度的唯一编号。
    相同输入得到相同输出。
    """
    # 用特殊分隔符拼接，避免 "ab"+"c" 和 "a"+"bc" 撞车
    combined = f"{len(str1)}:{str1}|{len(str2)}:{str2}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()



class Pc(Get_Product):


    def fetch_product(self, url, category):
        """请求并解析单个商品。

        返回标准化产品字典列表（每个元素为 Product.to_dic() 结果）。
        """
        res = Tool.get(url, headers=headers, cookies=cookies)
        if res.status_code != 200 or not res.text:
            raise RuntimeError(f'商品页面请求失败（HTTP {res.status_code}）：{url}')

        # 一个输入 URL 只代表当前颜色；页面 RSC 的 swatches 才是完整颜色集合。
        current = SalomonProductParser._product(res.text)
        url_key = str(current.get('urlKey') or '').strip()
        swatches = current.get('swatches') or []
        color_urls = []
        if url_key:
            for swatch in swatches:
                article = str(swatch.get('id') or '').strip() if isinstance(swatch, dict) else ''
                if article:
                    color_urls.append(f'https://www.salomon.com/en-us/product/{url_key}/{article}')
        if not color_urls:
            color_urls = [url]

        rows = []
        for color_url in dict.fromkeys(color_urls):
            if color_url == url:
                page_html = res.text
            else:
                color_res = Tool.get(color_url, headers=headers, cookies=cookies)
                if color_res.status_code != 200 or not color_res.text:
                    Tool.print(
                        f'颜色页面请求失败（HTTP {color_res.status_code}）：{color_url}',
                        color='yellow',
                    )
                    continue
                page_html = color_res.text
            rows.extend(SalomonProductParser(color_url, category, page_html).run())

        if not rows:
            raise ValueError(f'颜色页面均未解析出商品：{url}')
        return rows

class SalomonProductParser:
    """解析 Salomon Next.js 服务端渲染的产品数据。"""

    def __init__(self, url, category, html):
        self.url = url
        self.category = category
        self.html = html

    @staticmethod
    def _rsc_payload(html):
        """还原 Next.js ``self.__next_f`` 内嵌的 JSON 文本片段。"""
        chunks = re.findall(
            r'self\.__next_f\.push\(\[1,("(?:\\.|[^"\\])*")\]\)', html
        )
        if not chunks:
            raise ValueError('页面未包含 Next.js 产品数据')
        return ''.join(json.loads(chunk) for chunk in chunks)

    @classmethod
    def _product(cls, html):
        payload = cls._rsc_payload(html)
        decoder = json.JSONDecoder()
        for match in re.finditer(r'\{"articleCode":', payload):
            try:
                product, _ = decoder.raw_decode(payload, match.start())
            except json.JSONDecodeError:
                continue
            if product.get('name') and product.get('price') and product.get('mediaGallery'):
                return product
        raise ValueError('未在页面 RSC 数据中找到完整产品对象')

    @staticmethod
    def _more_details(product):
        """页面的 More details 分区，优先使用展开后的 moreDetails。"""
        details_data = product.get('details') or {}
        items = details_data.get('moreDetails') or details_data.get('detailsPart') or []
        details = []

        def append_item(item):
            if not isinstance(item, dict):
                return
            name = str(item.get('name') or '').strip()
            value = str(item.get('default') or item.get('converted') or '').strip()
            if name and value:
                details.append(f'<p><strong>{name}:</strong> {value}</p>')

            for child in item.get('children') or []:
                append_item(child)

        for item in items:
            append_item(item)
        return ''.join(details)

    @staticmethod
    def _features(product):
        """页面的 Features & Fabrics 分区。"""
        details = []
        for item in (product.get('details') or {}).get('features') or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get('name') or '').strip()
            values = ', '.join(
                str(value.get('label') or '').strip()
                for value in item.get('values') or []
                if value.get('label')
            )
            if name and values:
                details.append(f'<p><strong>{name}:</strong> {values}</p>')
        return ''.join(details)

    @staticmethod
    def _size_stock(size_ids):
        """查询尺码库存；接口的 true 代表有货但未提供精确数量。"""
        if not size_ids:
            return {}
        response = Tool.get(
            'https://www.salomon.com/api/pdp/stock',
            params={'locale': 'en-us', 'sizeIds': ','.join(size_ids)},
            headers={**headers, 'accept': 'application/json'},
            cookies=cookies,
        )
        if response.status_code != 200:
            Tool.print(f'尺码库存请求失败（HTTP {response.status_code}）', color='yellow')
            return {}
        try:
            payload = response.json()
        except (TypeError, ValueError):
            return {}
        stock = {}
        for item in payload if isinstance(payload, list) else []:
            sku = item.get('sku_code') if isinstance(item, dict) else None
            value = item.get('stock') if isinstance(item, dict) else None
            if sku:
                stock[sku] = 0 if value is False or value == 0 else value
        return stock

    def run(self):
        product = self._product(self.html)
        price = product.get('price') or {}
        regular_price = price.get('basePrice') or price.get('finalPrice')
        if not product.get('articleCode') or not product.get('name') or regular_price is None:
            raise ValueError(f'商品缺少货号、名称或价格：{self.url}')

        images = [
            item.get('url') for item in product.get('mediaGallery') or []
            if isinstance(item, dict) and item.get('type') == 'image' and item.get('url')
        ]
        if not images and product.get('imageUrl'):
            images = [product['imageUrl']]
        if not images:
            raise ValueError(f'商品缺少图片：{self.url}')

        model_code = str(product.get('modelCode') or '').rstrip('$')
        name = str(product['name']).strip()
        if model_code:
            name = re.sub(rf'\s+{re.escape(model_code)}$', '', name, flags=re.IGNORECASE)
        color = product.get('articleName') or product.get('colorGroup1Label') or 'Default'
        sizes = [
            size for size in product.get('sizes') or []
            if isinstance(size, dict) and size.get('id')
        ]
        if not sizes:
            sizes = [{'id': product['articleCode'], 'name': ''}]
        stock_by_size = self._size_stock([size['id'] for size in sizes])

        rows = []

        parent_id = generate_unique_id(name,self.url)



        for size in sizes:
            size_name = str(size.get('name') or '').strip()
            attributes = {'Color': color}
            if size_name:
                attributes['Size'] = size_name
            stock = stock_by_size.get(size['id'])
            if stock is None and product.get('inStockPercentage') == 0:
                stock = 0
            rows.append(Tool.Product.Variation(
                url=self.url,
                cat=self.category,
                imgs=Tool.Product.clean_imgs(images),
                name=name,
                sku=size['id'],
                price=regular_price,
                desc=product.get('description') or '',
                att=attributes,
                parent=parent_id,
                brand='Salomon',
                stock=stock,
                **{
                    'Features & Fabrics(product.metafields.c_f.features_fabrics)': self._features(product),
                    'More details': self._more_details(product),
                },
            ).to_dic())
        return rows


class _T:
    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.typ = 'simple'
        self.html = etree.HTML(res_text)

    def get_main_name(self, html):
        try:
            # TODO 业务xpath
            node = html.xpath('//div[@class="xxx"]')
            return ""
        except Exception as e:
            raise ValueError(f'获取主名称失败:{e}') from e


    def get_main_price(self, html):
        try:
            # TODO 业务xpath
            node = html.xpath('//div[@class="xxx"]')
            return ""
        except Exception as e:
            raise ValueError(f'获取价格失败:{e}')
            return ""

    def get_main_sku(self, html):
        try:
            # TODO 业务xpath
            node = html.xpath('//div[@class="xxx"]')
            return ""
        except Exception as e:
            Tool.print(f'获取sku失败:{e}')
            return ""

    def get_main_desc(self, html):
        try:
            # TODO 业务xpath
            node = html.xpath('//div[@class="xxx"]')
            return ""
        except Exception as e:
            Tool.print(f'获取描述失败:{e}')
            return ""

    def get_main_imgs(self, html):
        try:
            # TODO 业务xpath，返回图片列表
            node = html.xpath('//div[@class="xxx"]')
            return []
        except Exception as e:
            Tool.print(f'获取图片失败:{e}')
            return []

    def get_att(self,html):
        try:
            sty = html.xpath('//p[@class="chakra-text css-1al38q0"]//span//text()')
            if sty[0] == 'Style:':
                sty = ''.join(sty[-1]).strip()
                dic = {'Style':sty}
                print(dic)
                return dic
            return {}
        except Exception as e:
            Tool.print(f'获取属性失败:{e}')
            return {}

    def check_cob(self, html):
        """判断是否存在变体商品"""
        try:
            # TODO 业务逻辑，返回 True/False
            return False
        except Exception as e:
            Tool.print(f'检测变体失败:{e}')
            return False

    def get_cobs(self, html):
        """抓取所有变体数据"""
        try:
            node = html.xpath('//div[@class="xxx"]')
            cobs = []
            s_ls = []  # TODO 变体节点列表xpath
            for _ in s_ls:
                # TODO 提取变体字段
                cob_imgs_ls = []
                cob_name = ""
                cob_price = ""
                cob_sku = None
                cob_att = {}

                cob_desc = Tool.HTML.clean_product_desc(cob_desc)
                cob_price = Tool.clean_price(cob_price)
                cob_imgs = Tool.Product.clean_imgs(cob_imgs_ls)
                cob = Tool.Product.Variation(
                    url=self.url, cat=self.category, imgs=cob_imgs,
                    name=cob_name, desc=cob_desc, price=cob_price,
                    sku=cob_sku, att=cob_att
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

    # 需要频繁更新cookies
