from pathlib import Path

from config import Tool, base_url
from _ljp.mb.mg_shopify import CatalogCollector


HTML_PATH = Path(__file__).with_name('1.html')
SAVE_PATH = Tool.File.path_add_site('data/ml.json')


cookies = {
    '__pack': 'eyJzZXNzaW9uX2lkIjoiZGU4YzAwM2EtMzYwNi00YjFmLTE1ZTEtM2Q1NzQyMTAwMDU2In0%3D.BGAqSxuy%2FOiihhSty%2BPMpJZ5CzpB7h9DptLbkY1FKVY',
    'ig-fv': '1788573256295',
    'ig-id': 'ig_0394d2a405ba332fbb4aa377532e72973202',
    'ig-vars': '{}',
    'us_privacy': '1YNN',
    'cart': 'hWNGSnhdmlpad1a98uQtWTgu%3Fkey%3D540e93fe33c45b1ffe54fe33851b5d16',
    '_tracking_consent': '3AMPS._USCA_f_f_3B03J3isR829Ctrs-auQCg_%7B%7D',
    '_shopify_y': '6ac50c85-9100-4527-9478-ada72679f66b',
    '2c.cId': '6a9b764a53f88a4e3d469298',
    'fueledUserToken': 'a3ec68813ec6354094b6fd68516925a8142b4e05cbfdb8d68d3d076c0545236c',
    'trackingConsent': '%7B%22preferences%22%3Atrue%2C%22analytics%22%3Atrue%2C%22marketing%22%3Atrue%2C%22saleOfData%22%3Atrue%7D',
    '__anon_id': '6ac50c85-9100-4527-9478-ada72679f66b',
    '_fbp': 'fb.1.1788573259477.236685899453113598',
    '_gcl_au': '1.1.929158847.1788573260',
    '_ga': 'GA1.1.170415763.1788573260',
    '__obref': 'c35e555e-93b9-495a-a030-bc97a2ab006b',
    '_ps_session': 'Pw6bUEGJ44d8TBm_ga_oP',
    '_ps_site_visit': 'true',
    '__kla_id': 'eyJjaWQiOiJZbU5oTnpBd01UTXRZbU5oTXkwME1qVTVMVGt5T1dJdE1XTXdaakk1TlRVNFl6VmkifQ==',
    'polaris_consent_settings': '{"clientId":"f92352b8-2d58-4afc-9043-3859193f38a0","implicit":false,"analyticsPermitted":true,"personalizationPermitted":true,"adsPermitted":true,"notOptedOut":true,"essentialPermitted":true}',
    '_shopify_analytics': ':AaBvRkfTAAEAaKEgLNMECZz2aWAOiT8sOGvzOxlQWN9xTpCa6VfL0Asf6mskO5m36fvOqPnzjNQ0gBezLssXrcL8kgDxveNNG4tAhCxCPV8PA5qbKjCCh9ytvq4:',
    '_shopify_marketing': ':AaBvRkfYAAEAofYaEkkTbDD9Ft0guw7pkmDU6sWPC0AeUFVLqDkk7-QzCH-5vwwEyTAHLAOz83fHp4_LVhRrAzXRkAosiTcGtGa6iVceUgCAzHXVGxjTl4Vlvms:',
    '_ps_unique_impression_ac0b5c12-da08-4a38-9b41-7b5a6947098e': 'true',
    '_ps_pop_ac0b5c12-da08-4a38-9b41-7b5a6947098e': 'r',
    'ubid_ovr': '4a430e3c-3ff0-4a78-86ac-46795c650cdf',
    'reeview_uid': 'd94ae730-989b-4cc1-89d7-3b8bfaa070b7',
    'ig-pv': '8',
    '_ga_REH23B31XL': 'GS2.1.s1788573260$o1$g1$t1788575620$j4$l0$h877263909',
    'session': 'eyJjdXN0b21lckFjY291bnQiOnsiY29kZVZlcmlmaWVyIjoiZlpwd3RGNWl6emN5c1RCLXlicjhQenBSSHJ6UUFNM1NITnI1UUV3ZzREVSIsInN0YXRlIjoiMTc4ODU3NTYyNjI5NmtwdGpsbzd2NHUiLCJub25jZSI6ImNmNjRkMjlmOTE0NDk5YmJlMzE1MGVmNDU5YTIyNGI3IiwicmVkaXJlY3RQYXRoIjoiaHR0cHM6Ly93d3cuYnJ1bWF0ZS5jb20vZW4tdXMifX0%3D.iD8bgcHKLd5MyzDcYmzG0qKQ%2BVzXUhK8diZfHzq8V5E',
    '_ps_session_site_visit': '%7B%22sessionId%22%3A%224896b421-065f-460e-a5ea-8cfc77d1004e%22%2C%22startTime%22%3A1788575626523%7D',
    '_shopify_essential': ':AaBvRgCkAAEAg9ycnAN03IHTHywefNBXKQJt4mNtsYseyvmDgh2IEqUQ-8ktrweTxtz1A0SQG3W3NRFKJuhYWYWcru-yqrctyuWu3zbat1W56pU_ZS09wUE-dzVsUbzYkN6VINPu8tN2rOfcuDOMDvoFzFKnN_LY31S5IYPaf7kaRmS86YIwUsqmASl_apOi_fInV4mHY3vfyzGvaUroiYGlHZN1snzs7VR49LGoM5z_qaxMSHo4t0bUuSjT4ztztWpkcWs93XGJkvzwJtfPjfKcfb_pzocS0dWswoN2Xxk6mXuU8N56_TQJisopqehP8WaKcjEr-rtc7oqVx20dxJMSzr0jwh7FJCLQYyRq3TthylCJ2ZXniSBeuY3r065H5msXonH1TGZk9AsoLzIQaMw9DNcTwIMgXLIYQK74Rwrhk67P6bsegFsyBS8pD2MZAIwsIuy8iGT7R4Ujx2hFkShJH93ABecI9b2mSO33XcihlSFXThKvVE1FSgXwSyFdLdzOvPB0cKEOAoA8Nw:',
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
    # 'cookie': '__pack=eyJzZXNzaW9uX2lkIjoiZGU4YzAwM2EtMzYwNi00YjFmLTE1ZTEtM2Q1NzQyMTAwMDU2In0%3D.BGAqSxuy%2FOiihhSty%2BPMpJZ5CzpB7h9DptLbkY1FKVY; ig-fv=1788573256295; ig-id=ig_0394d2a405ba332fbb4aa377532e72973202; ig-vars={}; us_privacy=1YNN; cart=hWNGSnhdmlpad1a98uQtWTgu%3Fkey%3D540e93fe33c45b1ffe54fe33851b5d16; _tracking_consent=3AMPS._USCA_f_f_3B03J3isR829Ctrs-auQCg_%7B%7D; _shopify_y=6ac50c85-9100-4527-9478-ada72679f66b; 2c.cId=6a9b764a53f88a4e3d469298; fueledUserToken=a3ec68813ec6354094b6fd68516925a8142b4e05cbfdb8d68d3d076c0545236c; trackingConsent=%7B%22preferences%22%3Atrue%2C%22analytics%22%3Atrue%2C%22marketing%22%3Atrue%2C%22saleOfData%22%3Atrue%7D; __anon_id=6ac50c85-9100-4527-9478-ada72679f66b; _fbp=fb.1.1788573259477.236685899453113598; _gcl_au=1.1.929158847.1788573260; _ga=GA1.1.170415763.1788573260; __obref=c35e555e-93b9-495a-a030-bc97a2ab006b; _ps_session=Pw6bUEGJ44d8TBm_ga_oP; _ps_site_visit=true; __kla_id=eyJjaWQiOiJZbU5oTnpBd01UTXRZbU5oTXkwME1qVTVMVGt5T1dJdE1XTXdaakk1TlRVNFl6VmkifQ==; polaris_consent_settings={"clientId":"f92352b8-2d58-4afc-9043-3859193f38a0","implicit":false,"analyticsPermitted":true,"personalizationPermitted":true,"adsPermitted":true,"notOptedOut":true,"essentialPermitted":true}; _shopify_analytics=:AaBvRkfTAAEAaKEgLNMECZz2aWAOiT8sOGvzOxlQWN9xTpCa6VfL0Asf6mskO5m36fvOqPnzjNQ0gBezLssXrcL8kgDxveNNG4tAhCxCPV8PA5qbKjCCh9ytvq4:; _shopify_marketing=:AaBvRkfYAAEAofYaEkkTbDD9Ft0guw7pkmDU6sWPC0AeUFVLqDkk7-QzCH-5vwwEyTAHLAOz83fHp4_LVhRrAzXRkAosiTcGtGa6iVceUgCAzHXVGxjTl4Vlvms:; _ps_unique_impression_ac0b5c12-da08-4a38-9b41-7b5a6947098e=true; _ps_pop_ac0b5c12-da08-4a38-9b41-7b5a6947098e=r; ubid_ovr=4a430e3c-3ff0-4a78-86ac-46795c650cdf; reeview_uid=d94ae730-989b-4cc1-89d7-3b8bfaa070b7; ig-pv=8; _ga_REH23B31XL=GS2.1.s1788573260$o1$g1$t1788575620$j4$l0$h877263909; session=eyJjdXN0b21lckFjY291bnQiOnsiY29kZVZlcmlmaWVyIjoiZlpwd3RGNWl6emN5c1RCLXlicjhQenBSSHJ6UUFNM1NITnI1UUV3ZzREVSIsInN0YXRlIjoiMTc4ODU3NTYyNjI5NmtwdGpsbzd2NHUiLCJub25jZSI6ImNmNjRkMjlmOTE0NDk5YmJlMzE1MGVmNDU5YTIyNGI3IiwicmVkaXJlY3RQYXRoIjoiaHR0cHM6Ly93d3cuYnJ1bWF0ZS5jb20vZW4tdXMifX0%3D.iD8bgcHKLd5MyzDcYmzG0qKQ%2BVzXUhK8diZfHzq8V5E; _ps_session_site_visit=%7B%22sessionId%22%3A%224896b421-065f-460e-a5ea-8cfc77d1004e%22%2C%22startTime%22%3A1788575626523%7D; _shopify_essential=:AaBvRgCkAAEAg9ycnAN03IHTHywefNBXKQJt4mNtsYseyvmDgh2IEqUQ-8ktrweTxtz1A0SQG3W3NRFKJuhYWYWcru-yqrctyuWu3zbat1W56pU_ZS09wUE-dzVsUbzYkN6VINPu8tN2rOfcuDOMDvoFzFKnN_LY31S5IYPaf7kaRmS86YIwUsqmASl_apOi_fInV4mHY3vfyzGvaUroiYGlHZN1snzs7VR49LGoM5z_qaxMSHo4t0bUuSjT4ztztWpkcWs93XGJkvzwJtfPjfKcfb_pzocS0dWswoN2Xxk6mXuU8N56_TQJisopqehP8WaKcjEr-rtc7oqVx20dxJMSzr0jwh7FJCLQYyRq3TthylCJ2ZXniSBeuY3r065H5msXonH1TGZk9AsoLzIQaMw9DNcTwIMgXLIYQK74Rwrhk67P6bsegFsyBS8pD2MZAIwsIuy8iGT7R4Ujx2hFkShJH93ABecI9b2mSO33XcihlSFXThKvVE1FSgXwSyFdLdzOvPB0cKEOAoA8Nw:',
}


class SiteCatalogCollector(CatalogCollector):
    """Site customization points; unchanged hooks delegate to the template."""

    def fetch_html(self):
        print(self.base_url)
        response = self.tool.get(self.base_url,headers=headers,cookies=cookies)
        if response.status_code == 200 and response.text:
            self.tool.HTML.save_raw(response.text, self.html_path)
            return response.text
        if self.html_path.exists():
            self.tool.print(f'首页请求失败（{response.status_code}），使用本地 HTML', color='yellow')
            return self.html_path.read_text(encoding='utf-8')
        raise RuntimeError(f'首页请求失败（{response.status_code}），且本地 HTML 不存在')

    def create_parsers(self):
        return super().create_parsers()

    def select_parser(self, html):
        return super().select_parser(html)

    def parse_html(self, html):
        return super().parse_html(html)

    def normalize_name(self, value):
        return super().normalize_name(value)

    def normalize_url(self, url):
        return super().normalize_url(url)

    def should_keep_url(self, url):
        return super().should_keep_url(url)

    def should_keep_node(self, name, url, child, depth):
        return super().should_keep_node(name, url, child, depth)

    def put_node(self, nodes, name, url='', child=None, depth=0):
        return super().put_node(nodes, name, url, child, depth)

    def after_parse(self, menu):
        return super().after_parse(menu)

    def export_catalog(self, menu):
        return super().export_catalog(menu)


@Tool.zs('数据结构:{title:{url:xxx,child:{title:{url:xxx,child:{...}}}}}')
def f1():
    return SiteCatalogCollector(Tool, base_url, HTML_PATH, SAVE_PATH).run()


def run():
    menu = f1()
    Tool.print(f'已采集 {len(menu)} 个一级目录', color='green')


if __name__ == '__main__':
    run()
