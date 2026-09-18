from lxml import etree
from config import Tool

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')

catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

# 先验证两个分类，确认分页与缓存正常后再恢复为 None。
ts_num = None

# 排除某些 URL（输入分类黑名单）
skip_input_url_ls = []
# 输出商品链接黑名单
skip_output_url_ls = []

# 覆盖缓存：True=无视本地缓存强制重新请求
flush = False

catch_save_num = None

from _ljp.mb.zj import GetDetail
from _ljp.mb.model import PageModel

cookies = {
    'dwanonymous_9e217e72155e462deb87a243583f0211': 'abxkrQlPHBqYtBlNjf98UKH7Zs',
    'sid': 'YojCNVytPne7Wm_koGny6ZfvKngqe8Bz-U4',
    '__cq_dnt': '1',
    'dw_dnt': '1',
    'dwsid': 'ldo6PXtN7DTXgfx4rYT5BmC90nANmxIwlZUmMhpSmkMsw9wIKO9MGi0Oec9_cCn-AloqZDbTA6GvnflRChdTzw==',
    '_pxhd': 'vLBjFFJi63YUinwAtacjRakxZVLOw0qL43OHe66nl8-4vIxuHZKHsmTZ0r-678xY1dxF1WMCSRK6nW7FT1H0ow==:f2fA4SU0JAcxACpa5BtOvFyOVfznpAAnXTgcoZQYGB71ivF5a60kRV5RICx1axrDWidr1-wefbvCU1z3iJpl1zK67EcteaKG-bsH3d3ZH7M=',
    '_gcl_au': '1.1.677058698.1789559236',
    '_pxvid': '5aabeb8a-b1c4-11f1-ac58-f466040a152b',
    'BVBRANDID': '026d96d1-04d2-48c9-917d-8cc6832f7aec',
    'BVBRANDSID': 'cfafc035-6e3e-440e-b11c-7194f9581f1f',
    '_ga': 'GA1.1.791139228.1789559238',
    '__pxvid': '5e9f7501-b1c4-11f1-ae7e-8615022b3d2a',
    '__kla_id': 'eyJjaWQiOiJaV1k1WTJFelpUZ3RPVE15TkMwMFpXRXdMV0k1TWpNdFlUQXpZelV4TkRVMll6QXoifQ==',
    '_ga_8J57WZMVZ7': 'GS2.1.s1789559238$o1$g1$t1789559269$j29$l0$h0',
    '_px3': 'cd23773fc9dbfb1d5d49b7dd1877fccf335020e7286d3222c356bc44b2a6275b:jwPM7deSKdO56uEf61Um1GrXixmzetZ56NyOfqh9P2ji71IrYXdoYvN+2uwm0EwESarM+lJIYnHqRG5BzUDlQA==:1000:IASb+VB8y3VvX9XU4stqypTw429CCDOcekoEK9DBDhmBms6a31yMqygfUqe3KKVTOTzco4aCs0veaFRnpUsbAiY4R4kycjf3fa/dmL2PxgGxwwhbyRRQrzP/tYsxCPC+cjsDPdKvm2NkeGSA3/D0WL8hYIOGCahu5RFMV1/+mTevfKf01aSfKrX2DlYToJgttN83fXo2BO4AKkxcLGbojo5OEMlmrNcXHi3pYc3RFaFCuZcTKvxYrpLGDA27GTHq1/v5pbQMXUtkOnIB66pU/wbKxL1AJ1+eO0eGOqQ2wZGvDVthJvHjeNMHskKUrMGGXdgLPmuJI8eF5bs27HKxZvgo9hgU0LvzRjfLBP0e1d6RiE31TY++RdSylxu2U2bzSpklibpbhIidSphcQkzt8ibKE0yHlxHZ2OUWqIzLEu28cDafOoVj3EOLDgFT5cbQz8FRneRkCBRvqb/5GYK2u2a68G099OKy3z5pGukIYfE=',
    '_px2': 'eyJ1IjoiNzBjMDE5NjAtYjFjNC0xMWYxLTk3YTMtOGZmZmYzZjg5NjA2IiwidiI6IjVhYWJlYjhhLWIxYzQtMTFmMS1hYzU4LWY0NjYwNDBhMTUyYiIsInQiOjE3ODk1NTk1NzA3MDksImgiOiIxYTZhZmEzZjMyZDE1NTZlMjBlMGZhNzIwMTA1NTQ1Y2RlODBkMzJmNGEwZDA0MDMwNGFiZWIwMWI1MDg0ZGRjIn0=',
    'pxcts': 'SepcN9C6LCd8l/DhbkYpwSGZv9Y/zFrWrYy1d17nZHU=:2Z3P5P7xWFGvIPMv1Q4GKvK90BE0Jm9bhdfTdhDuSuP3qSteyoj06-aGRY1zT7OXhEawCf2/BsDRXrNdJoUIXjvNCZsgH6FLPAGfAJyFR4TltBpncU9nKq1Y6DnakOtp2QV9l/V0gToODc2X3WQr5CeLBN-L1HPLYmQ7T0-edB7BlL/vHY1zs/vMmoWce6XU',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://shop.samsonite.com/',
    'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
    # 'cookie': 'dwanonymous_9e217e72155e462deb87a243583f0211=abxkrQlPHBqYtBlNjf98UKH7Zs; sid=YojCNVytPne7Wm_koGny6ZfvKngqe8Bz-U4; __cq_dnt=1; dw_dnt=1; dwsid=ldo6PXtN7DTXgfx4rYT5BmC90nANmxIwlZUmMhpSmkMsw9wIKO9MGi0Oec9_cCn-AloqZDbTA6GvnflRChdTzw==; _pxhd=vLBjFFJi63YUinwAtacjRakxZVLOw0qL43OHe66nl8-4vIxuHZKHsmTZ0r-678xY1dxF1WMCSRK6nW7FT1H0ow==:f2fA4SU0JAcxACpa5BtOvFyOVfznpAAnXTgcoZQYGB71ivF5a60kRV5RICx1axrDWidr1-wefbvCU1z3iJpl1zK67EcteaKG-bsH3d3ZH7M=; _gcl_au=1.1.677058698.1789559236; _pxvid=5aabeb8a-b1c4-11f1-ac58-f466040a152b; BVBRANDID=026d96d1-04d2-48c9-917d-8cc6832f7aec; BVBRANDSID=cfafc035-6e3e-440e-b11c-7194f9581f1f; _ga=GA1.1.791139228.1789559238; __pxvid=5e9f7501-b1c4-11f1-ae7e-8615022b3d2a; __kla_id=eyJjaWQiOiJaV1k1WTJFelpUZ3RPVE15TkMwMFpXRXdMV0k1TWpNdFlUQXpZelV4TkRVMll6QXoifQ==; _ga_8J57WZMVZ7=GS2.1.s1789559238$o1$g1$t1789559269$j29$l0$h0; _px3=cd23773fc9dbfb1d5d49b7dd1877fccf335020e7286d3222c356bc44b2a6275b:jwPM7deSKdO56uEf61Um1GrXixmzetZ56NyOfqh9P2ji71IrYXdoYvN+2uwm0EwESarM+lJIYnHqRG5BzUDlQA==:1000:IASb+VB8y3VvX9XU4stqypTw429CCDOcekoEK9DBDhmBms6a31yMqygfUqe3KKVTOTzco4aCs0veaFRnpUsbAiY4R4kycjf3fa/dmL2PxgGxwwhbyRRQrzP/tYsxCPC+cjsDPdKvm2NkeGSA3/D0WL8hYIOGCahu5RFMV1/+mTevfKf01aSfKrX2DlYToJgttN83fXo2BO4AKkxcLGbojo5OEMlmrNcXHi3pYc3RFaFCuZcTKvxYrpLGDA27GTHq1/v5pbQMXUtkOnIB66pU/wbKxL1AJ1+eO0eGOqQ2wZGvDVthJvHjeNMHskKUrMGGXdgLPmuJI8eF5bs27HKxZvgo9hgU0LvzRjfLBP0e1d6RiE31TY++RdSylxu2U2bzSpklibpbhIidSphcQkzt8ibKE0yHlxHZ2OUWqIzLEu28cDafOoVj3EOLDgFT5cbQz8FRneRkCBRvqb/5GYK2u2a68G099OKy3z5pGukIYfE=; _px2=eyJ1IjoiNzBjMDE5NjAtYjFjNC0xMWYxLTk3YTMtOGZmZmYzZjg5NjA2IiwidiI6IjVhYWJlYjhhLWIxYzQtMTFmMS1hYzU4LWY0NjYwNDBhMTUyYiIsInQiOjE3ODk1NTk1NzA3MDksImgiOiIxYTZhZmEzZjMyZDE1NTZlMjBlMGZhNzIwMTA1NTQ1Y2RlODBkMzJmNGEwZDA0MDMwNGFiZWIwMWI1MDg0ZGRjIn0=; pxcts=SepcN9C6LCd8l/DhbkYpwSGZv9Y/zFrWrYy1d17nZHU=:2Z3P5P7xWFGvIPMv1Q4GKvK90BE0Jm9bhdfTdhDuSuP3qSteyoj06-aGRY1zT7OXhEawCf2/BsDRXrNdJoUIXjvNCZsgH6FLPAGfAJyFR4TltBpncU9nKq1Y6DnakOtp2QV9l/V0gToODc2X3WQr5CeLBN-L1HPLYmQ7T0-edB7BlL/vHY1zs/vMmoWce6XU',
}
class SamsoniteDetailUrls(GetDetail):
    """Collect canonical product pages from Samsonite's SFCC product grid."""

    @staticmethod
    def next_url(html):
        hrefs = html.xpath(
            '//div[contains(concat(" ", normalize-space(@class), " "), " grid-footer ")]'
            '//button[contains(concat(" ", normalize-space(@class), " "), " more ")]'
            '[contains(@data-url, "Search-UpdateGrid")]/@data-url'
        )
        return Tool.URL.add_site(hrefs[0]) if hrefs else None

    @staticmethod
    def product_urls(html):
        urls = []
        tiles = html.xpath(
            '//div[contains(concat(" ", normalize-space(@class), " "), " product-tile ")][@data-pid]'
        )
        for tile in tiles:
            hrefs = tile.xpath(
                './/a[contains(concat(" ", normalize-space(@class), " "), '
                '" product-tile-image-link ")][@href][1]/@href'
            )
            if not hrefs:
                continue

            url = Tool.URL.del_par(Tool.URL.add_site(hrefs[0]))
            if url not in urls:
                urls.append(url)
        return urls

    def fetch_page(self, page: PageModel, params):
        response = Tool.get(page.url, headers=headers, cookies=cookies)
        if response.status_code != 200:
            Tool.print(
                f'分类页请求失败: HTTP {response.status_code}; {page.url}',
                color='red',
            )
            page.set_fail()
            return [], None

        try:
            html = etree.HTML(response.text)
            if html is None:
                raise ValueError('页面不是有效 HTML')
            product_urls = self.product_urls(html)
            next_url = self.next_url(html)
        except (TypeError, ValueError, etree.ParserError) as error:
            Tool.print(f'分类页解析失败: {error}; {page.url}', color='red')
            page.set_fail()
            return [], None

        if not product_urls:
            if next_url:
                Tool.print(f'分类页没有商品卡片: {page.url}', color='red')
                page.set_fail()
            else:
                page.set_end()
            return [], None

        if not next_url or next_url == page.url:
            page.set_end()
            return product_urls, None

        return product_urls, next_url

    def build_params(self, page):
        return None




if __name__ == '__main__':
    pc = SamsoniteDetailUrls(
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
