import time
from html import escape
from json import JSONDecodeError
from pathlib import Path
from re import sub
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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
skip_input_url_ls = ['https://shop.samsonite.com/accessories/packing-organization/foldaway-tote/107097XXXX.html',
                     'https://shop.samsonite.com/accessories/foldaway-duffel/107093XXXX.html',
                     'https://shop.samsonite.com/accessories/packing-organization/foldaway-duffel/107093XXXX.html','https://shop.samsonite.com/accessories/foldaway-tote/107097XXXX.html'] # 图片无法下载
# 未实现字段
skip_output_url_ls = []

cookies = {
    'dwanonymous_9e217e72155e462deb87a243583f0211': 'abxkrQlPHBqYtBlNjf98UKH7Zs',
    '_pxvid': '5aabeb8a-b1c4-11f1-ac58-f466040a152b',
    'BVBRANDID': '026d96d1-04d2-48c9-917d-8cc6832f7aec',
    '_ga': 'GA1.1.791139228.1789559238',
    '__pxvid': '5e9f7501-b1c4-11f1-ae7e-8615022b3d2a',
    '__kla_id': 'eyJjaWQiOiJaV1k1WTJFelpUZ3RPVE15TkMwMFpXRXdMV0k1TWpNdFlUQXpZelV4TkRVMll6QXoifQ==',
    '_pin_unauth': 'dWlkPU5qZzFNVEU1WmpFdE1qbGtNaTAwWkdRMUxXSXhabVl0T0RNNU16RXhNV1ZtTW1VMw',
    'tangiblee:widget:user': '7b65f4d5-59d4-40ea-b171-aff0d1bd23c0',
    'tangiblee_widget_container_type': 'OVL%2CEMB',
    '_gcl_au': '1.1.677058698.1789559236.-.-.1789643582.1348748235.1789643583.1789643582',
    '_pxhd': '4IAHGS3WPWmYpVCknQPb/4if/eOOpTTCRWidBEJ43/-vS9c2oSQeDm8Hey3rQcLuvPtoBSCTVRszCNImeheDKQ==:imVdjU-E3/3g3tPZAo0/PhR45TXc1OukNBCGkSVqx0FgUv8uHBNcYVP-Amb0JKWRVVnThxHUspr3Dd9jDid2Gvu5ELQaH9To--XFmpbXMYI=',
    'dwsid': 'z5-FNiN1SN_SYEejx30dnHWLTnfXL2_NTyGujjjdkpuX23hvnfeAT0MS-UHJU-pPHML5Qz7DHwPNxcRnHyeZzw==',
    'sid': 'id9FJLDY1X94KJ-yEQK9gzPLjmVEgvJt5Wk',
    '__cq_dnt': '1',
    'dw_dnt': '1',
    'BVImplmain_site': '17643',
    'tangiblee_widget_open_last_date': '2026-09-18',
    '_px3': '5d6407c7a8bb0652251f6f26267c23cd9407f366f7d7cb2f04c5103df82d5587:NqxnFh/qRj2gnOGZVV0oaetyoM7k4XOnkyZSBbrpJ4GkgzMaHJzqzP0lAKlAZKrDPipvPw7Qd3DjgkP6ugGxEw==:1000:jZ5uwKZKNKUrM3gxUKBYpYgsjt/k+Jk5xvz5Bih2x/INdB3zLRh8BgxEwOkYcCV2dpD8ixU/UwWl7SR5tHb5BtJ67c1P5rdnTYPpzzigE/00FDeLoUnuzFFsLZwSf8Hp9UgXtspxxHrgwKsv0tlEfEjg2sUzQzu31sZ6O/dSySH59RDwwvQWht1uZat0pHiCUwD7VbRuTIFc6capvomodz3eNsgIkXuGDdQFasXllRHhrTMfypRrMwsLmMoZPjxjNcoJbZY+iM80kt8kw21QtVJQJQvUcd58yOg8HfE4FYfqeumfcbugpZAFeK4l55O8bRkl4ZFdIs8BYcAH9qiNJrKYTw1DloKIm3pq6LLSTBtaqxqXIwpjNY6uAkuG5vf4jzMzACQQXVNHGjUn0BVGrhfgBlZgue+f5j4zutyPa76X9aRMrzkIDTPJPCqYLUOwsVfsnPbRAnQk6mwqtvuF/ksWh0BFRtxu39l08Nh0SldaawAQGXfyRZZnNG9RyM7WLk8CT56eHyHNLts4iwC2Nw==',
    '_px2': 'eyJ1IjoiY2VjYzVjZjAtYjMzMy0xMWYxLTg3YjYtYjkzYjAwZThjNWQwIiwidiI6IjVhYWJlYjhhLWIxYzQtMTFmMS1hYzU4LWY0NjYwNDBhMTUyYiIsInQiOjE1NjE1MDcyMDAwMDAsImgiOiJmODhiMGRkM2Q0ZmEwZGNkYWMzNjczOTg3MjJiNDlkYjQ5YzM5NjA3NGY5ZGFlY2M0MjUwZjIwNWRhNDYyMGQyIn0=',
    'BVBRANDSID': '05edb734-c45b-4e68-bec6-8154f8a28653',
    '_ga_8J57WZMVZ7': 'GS2.1.s1789717075$o7$g1$t1789717100$j35$l0$h0',
    '_ga_JQYB8ZRNS5': 'GS2.1.s1789717075$o7$g1$t1789717100$j35$l0$h0',
    'pxcts': 'g7NdcT9AVn/Ija5Wfgyuqaanojtvqa0K25ObGKZsDzw=:tjp3jnRp72bbbY44aDKZScO7LY34-d4NDPZ61M4MjRrYScP9D4IcIiZKore5Nu/1XjlimevHyRW8HKSp1Jl2Wkcqcj74Z4bMmOUN4wmBRFN-5ynsppYCZ7j1gq21MRfkZot0In-dzGB9kO5-3o9KccK22iAgRtsF6VPAte5l2747ctF-aw9ERb-xilMlhZVL',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://shop.samsonite.com/best-sellers/',
    'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
    # 'cookie': 'dwanonymous_9e217e72155e462deb87a243583f0211=abxkrQlPHBqYtBlNjf98UKH7Zs; _pxvid=5aabeb8a-b1c4-11f1-ac58-f466040a152b; BVBRANDID=026d96d1-04d2-48c9-917d-8cc6832f7aec; _ga=GA1.1.791139228.1789559238; __pxvid=5e9f7501-b1c4-11f1-ae7e-8615022b3d2a; __kla_id=eyJjaWQiOiJaV1k1WTJFelpUZ3RPVE15TkMwMFpXRXdMV0k1TWpNdFlUQXpZelV4TkRVMll6QXoifQ==; _pin_unauth=dWlkPU5qZzFNVEU1WmpFdE1qbGtNaTAwWkdRMUxXSXhabVl0T0RNNU16RXhNV1ZtTW1VMw; tangiblee:widget:user=7b65f4d5-59d4-40ea-b171-aff0d1bd23c0; tangiblee_widget_container_type=OVL%2CEMB; _gcl_au=1.1.677058698.1789559236.-.-.1789643582.1348748235.1789643583.1789643582; _pxhd=4IAHGS3WPWmYpVCknQPb/4if/eOOpTTCRWidBEJ43/-vS9c2oSQeDm8Hey3rQcLuvPtoBSCTVRszCNImeheDKQ==:imVdjU-E3/3g3tPZAo0/PhR45TXc1OukNBCGkSVqx0FgUv8uHBNcYVP-Amb0JKWRVVnThxHUspr3Dd9jDid2Gvu5ELQaH9To--XFmpbXMYI=; dwsid=z5-FNiN1SN_SYEejx30dnHWLTnfXL2_NTyGujjjdkpuX23hvnfeAT0MS-UHJU-pPHML5Qz7DHwPNxcRnHyeZzw==; sid=id9FJLDY1X94KJ-yEQK9gzPLjmVEgvJt5Wk; __cq_dnt=1; dw_dnt=1; BVImplmain_site=17643; tangiblee_widget_open_last_date=2026-09-18; _px3=5d6407c7a8bb0652251f6f26267c23cd9407f366f7d7cb2f04c5103df82d5587:NqxnFh/qRj2gnOGZVV0oaetyoM7k4XOnkyZSBbrpJ4GkgzMaHJzqzP0lAKlAZKrDPipvPw7Qd3DjgkP6ugGxEw==:1000:jZ5uwKZKNKUrM3gxUKBYpYgsjt/k+Jk5xvz5Bih2x/INdB3zLRh8BgxEwOkYcCV2dpD8ixU/UwWl7SR5tHb5BtJ67c1P5rdnTYPpzzigE/00FDeLoUnuzFFsLZwSf8Hp9UgXtspxxHrgwKsv0tlEfEjg2sUzQzu31sZ6O/dSySH59RDwwvQWht1uZat0pHiCUwD7VbRuTIFc6capvomodz3eNsgIkXuGDdQFasXllRHhrTMfypRrMwsLmMoZPjxjNcoJbZY+iM80kt8kw21QtVJQJQvUcd58yOg8HfE4FYfqeumfcbugpZAFeK4l55O8bRkl4ZFdIs8BYcAH9qiNJrKYTw1DloKIm3pq6LLSTBtaqxqXIwpjNY6uAkuG5vf4jzMzACQQXVNHGjUn0BVGrhfgBlZgue+f5j4zutyPa76X9aRMrzkIDTPJPCqYLUOwsVfsnPbRAnQk6mwqtvuF/ksWh0BFRtxu39l08Nh0SldaawAQGXfyRZZnNG9RyM7WLk8CT56eHyHNLts4iwC2Nw==; _px2=eyJ1IjoiY2VjYzVjZjAtYjMzMy0xMWYxLTg3YjYtYjkzYjAwZThjNWQwIiwidiI6IjVhYWJlYjhhLWIxYzQtMTFmMS1hYzU4LWY0NjYwNDBhMTUyYiIsInQiOjE1NjE1MDcyMDAwMDAsImgiOiJmODhiMGRkM2Q0ZmEwZGNkYWMzNjczOTg3MjJiNDlkYjQ5YzM5NjA3NGY5ZGFlY2M0MjUwZjIwNWRhNDYyMGQyIn0=; BVBRANDSID=05edb734-c45b-4e68-bec6-8154f8a28653; _ga_8J57WZMVZ7=GS2.1.s1789717075$o7$g1$t1789717100$j35$l0$h0; _ga_JQYB8ZRNS5=GS2.1.s1789717075$o7$g1$t1789717100$j35$l0$h0; pxcts=g7NdcT9AVn/Ija5Wfgyuqaanojtvqa0K25ObGKZsDzw=:tjp3jnRp72bbbY44aDKZScO7LY34-d4NDPZ61M4MjRrYScP9D4IcIiZKore5Nu/1XjlimevHyRW8HKSp1Jl2Wkcqcj74Z4bMmOUN4wmBRFN-5ynsppYCZ7j1gq21MRfkZot0In-dzGB9kO5-3o9KccK22iAgRtsF6VPAte5l2747ctF-aw9ERb-xilMlhZVL',
}
flush = False

# CSV输出表头,默认就应该为None，表头后续会处理
fieldnames = None

max_threads = 3

from _ljp.mb.zj import Get_Product

class Pc(Get_Product):
    request_interval_seconds = 0.1

    def request(self, url):
        response = Tool.get(url, headers=headers, cookies=cookies, allow_redirects=True)
        time.sleep(Pc.request_interval_seconds)
        return response

    def fetch_product(self, url, category):
        res = self.request(url)
        parser = _T(url, category, res.text)
        if res.status_code != 200:
            parser.save_snapshot(res.text, f'http_{res.status_code}', 'html')
            message = '详情页访问被拒绝，保留待重试' if parser.is_access_denied() else '详情页请求失败'
            Tool.print(f'{message}: HTTP {res.status_code}; {url}', color='red')
            return []

        parser.save_snapshot(res.text, 'page', 'html')
        return parser.run()

class _T:
    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.html = etree.HTML(res_text)
        self.snapshot_dir = Path(__file__).with_name('ts') / '3'

    def get_main_name(self, html):
        names = html.xpath('//h1[contains(@class, "product-name")]//text()')
        name = ' '.join(' '.join(names).split())
        if not name:
            raise ValueError('详情页缺少商品名称')
        return name

    def get_main_prices(self, html):
        sale = html.xpath(
            '//div[contains(@class, "top-prices")]'
            '//span[contains(@class, "sales")]'
            '//span[contains(@class, "value")]/@content'
        )
        if not sale:
            raise ValueError('详情页缺少销售价格')
        regular = html.xpath(
            '//div[contains(@class, "top-prices")]'
            '//span[contains(@class, "comp-value-price")]//text()'
        )
        sale_price = Tool.clean_price(sale[0])
        regular_price = Tool.clean_price(''.join(regular)) if regular else sale_price
        return sale_price, regular_price

    def get_main_sku(self, html):
        skus = html.xpath('//*[@data-pid and @data-pid != "placeholder"]/@data-pid')
        if not skus:
            raise ValueError('详情页缺少商品 SKU')
        return skus[0]

    def get_main_desc(self, html):
        nodes = html.xpath('//*[contains(@class, "product-long-description")]')
        if not nodes:
            nodes = html.xpath('//*[contains(@class, "product-short-description")]')
        return Tool.HTML.clean_product_desc(nodes[0]) if nodes else ''

    def get_main_imgs(self, html):
        images = html.xpath('//img[contains(@alt, "image number")]/@src')
        return list(dict.fromkeys(images))

    def save_snapshot(self, text, kind, extension):
        product_slug = self.get_source_slug()
        parent_sku = self.get_page_parent_sku() or self.get_source_sku()
        filename = f'{product_slug}_{parent_sku}_{kind}.{extension}'
        Tool.HTML.save_raw(text, self.snapshot_dir / filename)

    @staticmethod
    def safe_filename_part(value):
        value = sub(r'[^A-Za-z0-9._-]+', '_', str(value or 'unknown'))
        return value.strip('._') or 'unknown'

    def get_source_slug(self):
        parts = [part for part in urlsplit(self.url).path.split('/') if part]
        slug = parts[-2] if len(parts) >= 2 else Path(urlsplit(self.url).path).stem
        return self.safe_filename_part(slug)

    def get_page_parent_sku(self):
        if self.html is None:
            return ''
        links = self.html.xpath(
            '//*[self::a or self::button]'
            '[contains(@data-url, "Product-Variation")]/@data-url'
        )
        for link in links:
            parent_sku = dict(parse_qsl(urlsplit(link).query)).get('pid')
            if parent_sku:
                return self.safe_filename_part(parent_sku)
        return ''

    def get_source_sku(self):
        try:
            return self.safe_filename_part(self.get_main_sku(self.html))
        except (AttributeError, ValueError):
            return self.safe_filename_part(Path(urlsplit(self.url).path).stem)

    def is_access_denied(self):
        text = self.res_text.lower()
        markers = (
            'access to this page has been denied',
            'access denied',
            'verify you are human',
            'captcha',
            'checking your browser',
        )
        return any(marker in text for marker in markers)

    def get_variation_urls(self):
        urls = []
        parent = None
        selected_sku = self.get_main_sku(self.html)
        links = self.html.xpath(
            '//*[self::a or self::button]'
            '[contains(@data-url, "Product-Variation")]/@data-url'
        )
        for link in links:
            variation_url = Tool.URL.add_site(link)
            parts = urlsplit(variation_url)
            pairs = parse_qsl(parts.query, keep_blank_values=True)
            query = dict(pairs)
            parent = parent or query.get('pid')
            color_keys = [key for key in query if key.lower().endswith('_color')]
            if color_keys:
                selected_pairs = [
                    (key, selected_sku if key in color_keys else value)
                    for key, value in pairs
                ]
                urls.append(urlunsplit((
                    parts.scheme,
                    parts.netloc,
                    parts.path,
                    urlencode(selected_pairs),
                    parts.fragment,
                )))
            urls.append(variation_url)
        return list(dict.fromkeys(urls)), parent

    def request_variation(self, variation_url):
        response = Pc.request(self, variation_url)
        if response.status_code != 200:
            self.save_snapshot(response.text, f'http_{response.status_code}_variation', 'html')
            raise ValueError(f'变体请求失败: HTTP {response.status_code}')
        try:
            product = response.json().get('product')
        except (JSONDecodeError, ValueError, TypeError) as error:
            raise ValueError(f'变体响应不是有效 JSON: {error}') from error
        if not isinstance(product, dict) or not product.get('id'):
            raise ValueError('变体响应缺少 product 数据')
        self.save_snapshot(response.text, f'{product["id"]}_variation', 'json')
        return product

    @staticmethod
    def get_product_prices(product):
        price_data = product.get('price') or {}
        sale = (price_data.get('sales') or {}).get('decimalPrice')
        regular = (price_data.get('list') or {}).get('decimalPrice')
        if sale in (None, ''):
            raise ValueError(f'变体 {product.get("id")} 缺少销售价格')
        sale_price = Tool.clean_price(sale)
        return sale_price, Tool.clean_price(regular) if regular not in (None, '') else sale_price

    @staticmethod
    def get_product_imgs(product):
        image_groups = product.get('images') or {}
        images = image_groups.get('large') or image_groups.get('hi-res') or []
        return list(dict.fromkeys(image.get('url') for image in images if image.get('url')))

    @staticmethod
    def get_product_attributes(product):
        attributes = {}
        for attribute in product.get('variationAttributes') or []:
            values = attribute.get('values') or []
            selected = next((value for value in values if value.get('selected')), None)
            if selected and selected.get('displayValue'):
                name = attribute.get('displayName') or attribute.get('id')
                if name:
                    attributes[name] = selected['displayValue']
        return attributes

    @staticmethod
    def get_product_desc(product):
        for field in ('longDescription', 'shortDescription', 'headlineDescription', 'pageDescription'):
            description = product.get(field)
            if isinstance(description, str) and description.strip():
                return Tool.HTML.clean_product_desc_str(description)
        return ''

    @staticmethod
    def get_custom_fields(product):
        items = []
        for specification in product.get('specifications') or []:
            if not isinstance(specification, dict):
                continue
            name = str(specification.get('specification') or '').strip()
            value = str(specification.get('value') or '').strip()
            if name and value:
                items.append(f'<li><strong>{escape(name)}:</strong> {escape(value)}</li>')
        return {
            'Specifications': Tool.HTML.clean_product_desc_str(
                f'<ul>{"".join(items)}</ul>' if items else ''
            )
        }

    @staticmethod
    def get_parent_sku(product, fallback):
        if fallback:
            return fallback
        selected_url = product.get('selectedProductUrl') or ''
        return Path(urlsplit(selected_url).path).stem or product['id']

    def to_variation(self, product, parent):
        sale_price, regular_price = self.get_product_prices(product)
        row = Tool.Product.Variation(
            url=self.url,
            cat=self.category,
            imgs=self.get_product_imgs(product),
            name=product.get('productName') or self.get_main_name(self.html),
            desc=self.get_product_desc(product) or self.get_main_desc(self.html),
            price=sale_price,
            sku=product['id'],
            parent=self.get_parent_sku(product, parent),
            att=self.get_product_attributes(product),
            stock=None if product.get('available', True) else 0,
            **self.get_custom_fields(product),
        ).to_dic()
        row['Regular price'] = regular_price
        return row

    def to_simple(self):
        sale_price, regular_price = self.get_main_prices(self.html)
        row = Tool.Product.Simple(
            url=self.url,
            cat=self.category,
            imgs=self.get_main_imgs(self.html),
            name=self.get_main_name(self.html),
            desc=self.get_main_desc(self.html),
            sku=self.get_main_sku(self.html),
            price=sale_price,
        ).to_dic()
        row['Regular price'] = regular_price
        return row

    def run(self) -> list:
        try:
            if self.html is None:
                raise ValueError('详情页不是有效 HTML')
            variation_urls, parent = self.get_variation_urls()
            if not variation_urls:
                return [self.to_simple()]

            rows = []
            seen_skus = set()
            for variation_url in variation_urls:
                product = self.request_variation(variation_url)
                if product['id'] in seen_skus:
                    continue
                seen_skus.add(product['id'])
                rows.append(self.to_variation(product, parent))
            if not rows:
                raise ValueError('详情页没有可导出的变体')
            return rows
        except (JSONDecodeError, KeyError, TypeError, ValueError) as error:
            Tool.print(f'详情页解析失败: {error}; {self.url}', color='red')
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
