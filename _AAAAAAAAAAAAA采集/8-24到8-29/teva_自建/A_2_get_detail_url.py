import json

from lxml import etree
from pandas._libs.tslibs import offsets

from config import Tool

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

catch_save_num = None

from _ljp.mb.zj import GetDetail
from _ljp.mb.model import Base, PageModel
cookies = {
    'deckersPreviousPage': 'category',
    'deckersSID': 'e5c6e6fe-459b-4e7b-a59a-031f787a732e',
    'deckersUserID': '49304fa3-eeaf-4349-888b-3c5886b2238c',
    'csrfToken': 'f7cd3d18a94c34cd0479cf689dfcb5a1caf66d39dc3ff7713bbcda94ea3d2e12',
    '_dyid_server': '6115888553455153550',
    '_dyjsession': 'odk8ucrsremjachkqepi9zdwr3pmjhzf',
    'auth_refresh_token': 'F-vq7sickAAk9iwozpK2yUS2zN-Wu5D9ELdWo-GNKPU',
    'auth_expires_in': '1800',
    'auth_guest_id': 'ablbIXkbpKwrkRxutFxGYYkXo3',
    'builderSessionId': '462fb9c323cd4503bbafc6a67af10a3b',
    'deckersSessionCartID': 'dsl3fbxyvtui50aqcapztb33',
    'kampyle_userid': 'a950-1a5e-5469-8236-2fcd-2b37-b25d-5bda',
    '__attn_eat_id': '0127d98cf2b649ef9c118f56efe75e0f',
    'osano_consentmanager_uuid': 'c07e6d88-acd8-41ee-9689-21d52704dab5',
    'osano_consentmanager': '5UxXKcRWQU20820AJNvMhNqMSsPtyfcPPeBoj2BdUk-Id6QOoLMCm7jH9QC7eByxrG3mrv-yzkydIKCWl6knfX0QfwctlRUcYFn_YcolYq89CpJZLXnn3KquoYYATIxsEpqxc5QA97TwLU7LTLb0qM-kxVQhcygr1rh-t0KXnJ-Zi547fQ6sDiOzrInHFY2yBZRXh7t1XJXTTOzgki1IHIAKhALkTGoNUhxkSvAoCCk71fABStizO3GfKNJbbfk1dM1zoSS6ZOwq9mwUUnDCCHmYMkZ-waADOCSA7u02IP9WrYf2M9oAgqNPXea3V-rA9YMpqjd6qRE=',
    '__attentive_session_id': 'bc3a8ae326224511b8eb096ad1c22ed6',
    '__attentive_cco': '1787982715108',
    '_attn_bopd_': 'browser',
    '__attentive_dv': '1',
    '_gcl_au': '1.1.1915843092.1787982721',
    '_ga': 'GA1.1.980579987.1787982723',
    '__attentive_id': 'cc461f8172c0477c8119e8979cf6753a',
    'pixlee_analytics_cookie': '%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2294c2198f-3d0d-4341-743e-5995ea248517%22%7D',
    'pixlee_analytics_cookie_legacy': '%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2294c2198f-3d0d-4341-743e-5995ea248517%22%7D',
    'tf-version': 'v2',
    '_pin_unauth': 'dWlkPU1ESTBZakl3TjJVdE4yVTROaTAwT0dJd0xXRXdPRE10TXpCa1lqbGxZbVZrWlRZdw',
    '_sp_ses.aeb7': '*',
    'kampyleUserSession': '1787984118690',
    'kampyleUserSessionsCount': '4',
    'kampyleUserPercentile': '79.12414373003132',
    'kampyleSessionPageCounter': '1',
    '_attn_': 'eyJ1Ijoie1wiY29cIjoxNzg3OTgyNzE1MTA0LFwidW9cIjoxNzg3OTgyNzIzNTAyLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcImNjNDYxZjgxNzJjMDQ3N2M4MTE5ZTg5NzljZjY3NTNhXCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg3OTg0MTE5NjQzLFwidW9cIjoxNzg3OTg0MTE5NjQzLFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL3FqbmhzLnRldmEuY29tXCJ9In0=',
    'deckers-forter-token': 'b412b5500f814c05b920f01f871c34ce_1787984114523__UDF43-mnf-a4_17ck__tt',
    'amp_f24a38': 'AxMQgmq5nC0eQeb95eINdd...1k161bci0.1k162h9pd.0.0.0',
    '_sp_id.aeb7': '473b964f-4d8d-4350-b24f-8657b2821cfa.1787983993.1.1787984512.1787983993.45c101e8-5654-4f7c-b830-3b533d0c2eb6',
    'apt_pixel': 'eyJkZXZpY2VJZCI6Ijc1ZmEwYWU5LTljNTYtNDU3Mi05MDJkLWQ5YmM3MGNhNjhlZSIsInVzZXJJZCI6bnVsbCwiZXZlbnRJZCI6NywibGFzdEV2ZW50VGltZSI6MTc4Nzk4NDUxMTY5MCwiY2hlY2tvdXQiOnsiYnJhbmQiOiJjYXNoYXBwYWZ0ZXJwYXkifX0=',
    '_ga_DH3D3PZHRX': 'GS2.1.s1787982882$o1$g1$t1787984512$j60$l0$h0',
    'auth_access_token': 'eyJ2ZXIiOiIxLjAiLCJqa3UiOiJzbGFzL3Byb2QvYmRqZF9wcmQiLCJraWQiOiJjMjRkNmVhZS0xYjhkLTQxZjctYjgyOC1kMGFhMmMxOTk2NzAiLCJ0eXAiOiJqd3QiLCJjbHYiOiJKMi4zLjQiLCJhbGciOiJFUzI1NiJ9.eyJhdXQiOiJHVUlEIiwic2NwIjoic2ZjYy5zaG9wcGVyLW15YWNjb3VudC5iYXNrZXRzIHNmY2Muc2hvcHBlci1wcm9kdWN0cyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnJ3IHNmY2Muc2hvcHBlci1jdXN0b21lcnMubG9naW4gc2ZjYy5zaG9wcGVyLWNvbnRleHQucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5vcmRlcnMgc2ZjYy5zaG9wcGVyLWN1c3RvbWVycy5yZWdpc3RlciBzZmNjLnNob3BwZXItbXlhY2NvdW50LmFkZHJlc3Nlcy5ydyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnByb2R1Y3RsaXN0cy5ydyBzZmNjLnNob3BwZXItcHJvbW90aW9ucyBzZmNjLnNob3BwZXItY3VzdG9tLW9iamVjdHMuc3VwZXJHcm91cCBjX2Z1bGxQcm9kdWN0X3Igc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wYXltZW50aW5zdHJ1bWVudHMucncgc2ZjYy5zaG9wcGVyLXByb2R1Y3Qtc2VhcmNoIGNfc2hpcHBpbmdNZXRob2RzX3Igc2ZjYy5zaG9wcGVyLXNlbyBzZmNjLnNob3BwZXItY2F0ZWdvcmllcyIsInN1YiI6ImNjLXNsYXM6OmJkamRfcHJkOjpzY2lkOjg4YzQzYTQ1LWFjMTMtNDUxZC05Y2ZlLTU0MDZlMmIzZGE0YTo6dXNpZDo0OTMwNGZhMy1lZWFmLTQzNDktODg4Yi0zYzU4ODZiMjIzOGMiLCJjdHgiOiJzbGFzIiwiaXNzIjoic2xhcy9wcm9kL2JkamRfcHJkIiwiaXN0IjoxLCJkbnQiOiIwIiwiYXVkIjoiY29tbWVyY2VjbG91ZC9wcm9kL2JkamRfcHJkIiwibmJmIjoxNzg3OTg0MzU3LCJzdHkiOiJVc2VyIiwiaXNiIjoidWlkbzpzbGFzOjp1cG46R3Vlc3Q6OnVpZG46R3Vlc3QgVXNlcjo6Z2NpZDphYmxiSVhrYnBLd3JrUnh1dEZ4R1lZa1hvMzo6Y2hpZDpURVZBLVVTIiwiZXhwIjoxNzg3OTg2MTg3LCJpYXQiOjE3ODc5ODQzODcsImp0aSI6IkMyQy05NjgxODMzNDEwOTUwNDg0ODY2MzAyOTM3ODQ1MzQ1Mjk4NjIifQ.xo4W6525xoXUp9Vmg7Uf97nEuSMBiHTFfmuSvqBE11e0vCF8Q1KLUEwTkVS6lEDLr3npn-gBecrBTH5uYjcYbA',
    'auth_issued_at': '1787984387',
    'auth_refresh_at': '1787985287',
    'forterToken': 'b412b5500f814c05b920f01f871c34ce_1787984538717__UDF43-mnf-a4_17ck',
    'datadome': 'oWYpWJyKZwNWRdIpNvM~AvpQVVMyvt~MAkrVcNwU~P4xaroWl7gR15lvkfYPBqUpJy1ZHMNsv1qbEH6JngRn_osmqIFKlMiT7CLwt4C~wmc3c9M6lrk_FTC4woGOy9Tf',
    '__attentive_pv': '21',
    '__attentive_ss_referrer': 'ORGANIC',
    '_ga_QNKHCBB6H5': 'GS2.1.s1787982723$o1$g1$t1787984618$j60$l0$h0',
    '_dd_s': 'aid=8f6dec8c-540c-425d-9669-780b5ab74951&rum=0&expire=1787985561741',
}

headers = {
    'accept': 'text/x-component',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'content-type': 'text/plain;charset=UTF-8',
    'next-action': '40296aacca523253fd3fd0c407b0d8c7ad4bea53fe',
    'next-router-state-tree': '%5B%22%22%2C%7B%22children%22%3A%5B%5B%22lang%22%2C%22en-US%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22(main)%22%2C%7B%22children%22%3A%5B%22c%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22women-view-all%22%2C%22c%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D%7D%2Cnull%2Cnull%5D',
    'origin': 'https://www.teva.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.teva.com/c/women-view-all',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'deckersPreviousPage=category; deckersSID=e5c6e6fe-459b-4e7b-a59a-031f787a732e; deckersUserID=49304fa3-eeaf-4349-888b-3c5886b2238c; csrfToken=f7cd3d18a94c34cd0479cf689dfcb5a1caf66d39dc3ff7713bbcda94ea3d2e12; _dyid_server=6115888553455153550; _dyjsession=odk8ucrsremjachkqepi9zdwr3pmjhzf; auth_refresh_token=F-vq7sickAAk9iwozpK2yUS2zN-Wu5D9ELdWo-GNKPU; auth_expires_in=1800; auth_guest_id=ablbIXkbpKwrkRxutFxGYYkXo3; builderSessionId=462fb9c323cd4503bbafc6a67af10a3b; deckersSessionCartID=dsl3fbxyvtui50aqcapztb33; kampyle_userid=a950-1a5e-5469-8236-2fcd-2b37-b25d-5bda; __attn_eat_id=0127d98cf2b649ef9c118f56efe75e0f; osano_consentmanager_uuid=c07e6d88-acd8-41ee-9689-21d52704dab5; osano_consentmanager=5UxXKcRWQU20820AJNvMhNqMSsPtyfcPPeBoj2BdUk-Id6QOoLMCm7jH9QC7eByxrG3mrv-yzkydIKCWl6knfX0QfwctlRUcYFn_YcolYq89CpJZLXnn3KquoYYATIxsEpqxc5QA97TwLU7LTLb0qM-kxVQhcygr1rh-t0KXnJ-Zi547fQ6sDiOzrInHFY2yBZRXh7t1XJXTTOzgki1IHIAKhALkTGoNUhxkSvAoCCk71fABStizO3GfKNJbbfk1dM1zoSS6ZOwq9mwUUnDCCHmYMkZ-waADOCSA7u02IP9WrYf2M9oAgqNPXea3V-rA9YMpqjd6qRE=; __attentive_session_id=bc3a8ae326224511b8eb096ad1c22ed6; __attentive_cco=1787982715108; _attn_bopd_=browser; __attentive_dv=1; _gcl_au=1.1.1915843092.1787982721; _ga=GA1.1.980579987.1787982723; __attentive_id=cc461f8172c0477c8119e8979cf6753a; pixlee_analytics_cookie=%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2294c2198f-3d0d-4341-743e-5995ea248517%22%7D; pixlee_analytics_cookie_legacy=%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2294c2198f-3d0d-4341-743e-5995ea248517%22%7D; tf-version=v2; _pin_unauth=dWlkPU1ESTBZakl3TjJVdE4yVTROaTAwT0dJd0xXRXdPRE10TXpCa1lqbGxZbVZrWlRZdw; _sp_ses.aeb7=*; kampyleUserSession=1787984118690; kampyleUserSessionsCount=4; kampyleUserPercentile=79.12414373003132; kampyleSessionPageCounter=1; _attn_=eyJ1Ijoie1wiY29cIjoxNzg3OTgyNzE1MTA0LFwidW9cIjoxNzg3OTgyNzIzNTAyLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcImNjNDYxZjgxNzJjMDQ3N2M4MTE5ZTg5NzljZjY3NTNhXCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg3OTg0MTE5NjQzLFwidW9cIjoxNzg3OTg0MTE5NjQzLFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL3FqbmhzLnRldmEuY29tXCJ9In0=; deckers-forter-token=b412b5500f814c05b920f01f871c34ce_1787984114523__UDF43-mnf-a4_17ck__tt; amp_f24a38=AxMQgmq5nC0eQeb95eINdd...1k161bci0.1k162h9pd.0.0.0; _sp_id.aeb7=473b964f-4d8d-4350-b24f-8657b2821cfa.1787983993.1.1787984512.1787983993.45c101e8-5654-4f7c-b830-3b533d0c2eb6; apt_pixel=eyJkZXZpY2VJZCI6Ijc1ZmEwYWU5LTljNTYtNDU3Mi05MDJkLWQ5YmM3MGNhNjhlZSIsInVzZXJJZCI6bnVsbCwiZXZlbnRJZCI6NywibGFzdEV2ZW50VGltZSI6MTc4Nzk4NDUxMTY5MCwiY2hlY2tvdXQiOnsiYnJhbmQiOiJjYXNoYXBwYWZ0ZXJwYXkifX0=; _ga_DH3D3PZHRX=GS2.1.s1787982882$o1$g1$t1787984512$j60$l0$h0; auth_access_token=eyJ2ZXIiOiIxLjAiLCJqa3UiOiJzbGFzL3Byb2QvYmRqZF9wcmQiLCJraWQiOiJjMjRkNmVhZS0xYjhkLTQxZjctYjgyOC1kMGFhMmMxOTk2NzAiLCJ0eXAiOiJqd3QiLCJjbHYiOiJKMi4zLjQiLCJhbGciOiJFUzI1NiJ9.eyJhdXQiOiJHVUlEIiwic2NwIjoic2ZjYy5zaG9wcGVyLW15YWNjb3VudC5iYXNrZXRzIHNmY2Muc2hvcHBlci1wcm9kdWN0cyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnJ3IHNmY2Muc2hvcHBlci1jdXN0b21lcnMubG9naW4gc2ZjYy5zaG9wcGVyLWNvbnRleHQucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5vcmRlcnMgc2ZjYy5zaG9wcGVyLWN1c3RvbWVycy5yZWdpc3RlciBzZmNjLnNob3BwZXItbXlhY2NvdW50LmFkZHJlc3Nlcy5ydyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnByb2R1Y3RsaXN0cy5ydyBzZmNjLnNob3BwZXItcHJvbW90aW9ucyBzZmNjLnNob3BwZXItY3VzdG9tLW9iamVjdHMuc3VwZXJHcm91cCBjX2Z1bGxQcm9kdWN0X3Igc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wYXltZW50aW5zdHJ1bWVudHMucncgc2ZjYy5zaG9wcGVyLXByb2R1Y3Qtc2VhcmNoIGNfc2hpcHBpbmdNZXRob2RzX3Igc2ZjYy5zaG9wcGVyLXNlbyBzZmNjLnNob3BwZXItY2F0ZWdvcmllcyIsInN1YiI6ImNjLXNsYXM6OmJkamRfcHJkOjpzY2lkOjg4YzQzYTQ1LWFjMTMtNDUxZC05Y2ZlLTU0MDZlMmIzZGE0YTo6dXNpZDo0OTMwNGZhMy1lZWFmLTQzNDktODg4Yi0zYzU4ODZiMjIzOGMiLCJjdHgiOiJzbGFzIiwiaXNzIjoic2xhcy9wcm9kL2JkamRfcHJkIiwiaXN0IjoxLCJkbnQiOiIwIiwiYXVkIjoiY29tbWVyY2VjbG91ZC9wcm9kL2JkamRfcHJkIiwibmJmIjoxNzg3OTg0MzU3LCJzdHkiOiJVc2VyIiwiaXNiIjoidWlkbzpzbGFzOjp1cG46R3Vlc3Q6OnVpZG46R3Vlc3QgVXNlcjo6Z2NpZDphYmxiSVhrYnBLd3JrUnh1dEZ4R1lZa1hvMzo6Y2hpZDpURVZBLVVTIiwiZXhwIjoxNzg3OTg2MTg3LCJpYXQiOjE3ODc5ODQzODcsImp0aSI6IkMyQy05NjgxODMzNDEwOTUwNDg0ODY2MzAyOTM3ODQ1MzQ1Mjk4NjIifQ.xo4W6525xoXUp9Vmg7Uf97nEuSMBiHTFfmuSvqBE11e0vCF8Q1KLUEwTkVS6lEDLr3npn-gBecrBTH5uYjcYbA; auth_issued_at=1787984387; auth_refresh_at=1787985287; forterToken=b412b5500f814c05b920f01f871c34ce_1787984538717__UDF43-mnf-a4_17ck; datadome=oWYpWJyKZwNWRdIpNvM~AvpQVVMyvt~MAkrVcNwU~P4xaroWl7gR15lvkfYPBqUpJy1ZHMNsv1qbEH6JngRn_osmqIFKlMiT7CLwt4C~wmc3c9M6lrk_FTC4woGOy9Tf; __attentive_pv=21; __attentive_ss_referrer=ORGANIC; _ga_QNKHCBB6H5=GS2.1.s1787982723$o1$g1$t1787984618$j60$l0$h0; _dd_s=aid=8f6dec8c-540c-425d-9669-780b5ab74951&rum=0&expire=1787985561741',
}

def w():
    from playwright.sync_api import sync_playwright
    from fingerprint_toolkit import FingerprintKit
    from itertools import cycle

    edge = sync_playwright().start()
    browser = edge.chromium.launch(headless=False)

    # 创建4个上下文，保存对应的 fpk
    contexts = [browser.new_context() for _ in range(4)]
    context_fpk = {}
    for ctx in contexts:
        fpk = FingerprintKit()
        context_fpk[ctx] = fpk
        # 可选：创建一个初始页面，但不强制

    context_cycle = cycle(contexts)  # 循环迭代器

    def get():
        ctx = next(context_cycle)
        fpk = context_fpk[ctx]
        page = ctx.new_page()
        fpk.inject(page)
        return page

    return get


class Pc(GetDetail):


    def _init(self):
        super()._init()

        self.data = {}

    def fetch_page(self, P:PageModel, params):
        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空或等于当前 url 表示停止翻页


        确认结束 p.status = 'end'
        确认失败 p.status = 'fail' 或者set_fail()
        """
        try:
            raw_url = P.url

            cat_id = raw_url.split('/')[-1]

            params['categoryID'] = cat_id

            data = json.dumps([params])


            res = Tool.post(raw_url,data=data,headers=headers,cookies=cookies)
            # html = etree.HTML(res.text)
            print(res.text)
            ls = []
            for line in res.text.splitlines():
                if ':[{"id":' in line[:20]:
                    line = line.split(':',1)[1]
                    df = json.loads(line)[0]

                    img = df['images']

                    img = [i['src'] for i in img]

                    details = df['details']

                    variationMap = df['variationMap']
                    variationAttributes = df['variationAttributes']
                    var = {}
                    for k,v in variationMap.items():
                        if ':'in k:
                            color,size = k.split(':')


                            size = variationAttributes[size]['name']
                            var[k] = {
                                'color': variationAttributes[color]['name'],
                                'size': size,
                                'sku':v['sku'],
                                'color_map':color.replace('color-','')
                            }
                    d_dic = {
                        'sku':df['sku'],
                        'name':df['name'],
                        'price':df['price']['price']["amount"],
                        'description':f'<div>{details["descriptionShort"]}{details["descriptionLong"]}</div>',
                        'imgs':img,
                        'var':var
                    }


                    ls.append(df['sku'])

                    self.data[df['sku']] = d_dic


            # Tool.File.save_json(dic,'hc/2/数据.json')

            if 0<=len(ls)<=24:
                P.set_end()
                return ls,False

            return ls,raw_url

        except Exception as e:
            P.set_fail()
            raise e


    def run(self):
        super().run()

        Tool.File.save_json(self.data,'hc/2/products.json')


    def build_params(self, page):
        """构造参与缓存哈希的请求参数；默认仅包含页码"""
        offset = int(page.page)-1
        params = {
            "offset":offset*24,
            "limit":24,
            "includeContent":True,
            "locale": "en-US",
            "filters": []
        }
        # data = '[{"categoryID":"kids-view-all","offset":24,"limit":24,"includeContent":true,"filters":[],"locale":"en-US"}]'
        return params




if __name__ == '__main__':
    pc = Pc(
       tool=Tool,
       input_path=file_path,
       output_path=save_path,
       catch_path=catch_path,
       index_path=index_path,
       ts_num=ts_num,
       flush=flush,
       skip_input_url_ls=skip_input_url_ls,
       skip_output_url_ls=skip_output_url_ls,
       catch_save_num=catch_save_num
       )
    pc.run()