import json
import re
import threading
from html import escape
from urllib.parse import parse_qsl, urlsplit

from lxml import etree

from config import Tool
from _ljp.mb.zj import Get_Product


input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
fail_file = Tool.File.path_add_site('data/fail.json')
catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

ts_num = None
catch_save_num = None
skip_input_url_ls = []
skip_output_url_ls = []
cookies = {
    'dwsid': 'PUeEi89avnu5o_ls0ZaaWWBzzIVQprRdZsJ8EEVO2A3Gj1FRZpaf7NWT4luUaimLMdS-tDyujDyswoRbCtGDvA==',
    'sid': '_E25i6MK4ovGTkH8kSmtDKF58YU89uitGS8',
    'dwanonymous_472d7a68ade4fc9505b4fb3556d571a0': 'abdOPQx49VA5NuPM7jtlNbDo12',
    '_pxhd': '98e6aed5222af19aec88bfe6ee18d48f232abb4683df3490052ad6fcd2b38ebd:8a2dc13a-ace1-11f1-af07-8573aadf94f8',
    '__cq_dnt': '1',
    'dw_dnt': '1',
    '__kla_id': 'eyJjaWQiOiJZek5sWXpaaE0yUXRNR0k0WmkwME5qY3pMV0U1TURJdE56bGtNREE0TXpoa1l6VXkifQ==',
    '_pxvid': '8a2dc13a-ace1-11f1-af07-8573aadf94f8',
    '__pxvid': '8c93574f-ace1-11f1-9f74-5e112df355ac',
    'BVBRANDID': 'd6ee111b-b594-4321-9a38-185660fa2ff0',
    'OptanonAlertBoxClosed': '2026-09-10T07:28:49.674Z',
    '_gcl_au': '1.1.1437494665.1789025330',
    '_ga': 'GA1.1.994945795.1789025324',
    '_nb_sp_ses.4902': '*',
    '_pin_unauth': 'dWlkPU5tWXpOak0wTmpVdE5qVTRZaTAwTW1Sa0xXSTBZelV0WkRKa04yVTNNV1V3T1RoaQ',
    '__kla_session': '%7B%22sessionId%22%3A%220122bab5-a2e1-4cda-8ba1-a9f0cf70e3c3%22%2C%22sentSessionStartedEvent%22%3Afalse%2C%22sentUserIdentifiedEvent%22%3Afalse%7D',
    'BVBRANDSID': '11d4a579-ebe8-4dc8-89dd-2fea9753b513',
    '_ga_ZWDWKYLBY3': 'GS2.1.s1789028219$o2$g1$t1789029573$j37$l0$h0',
    '_px3': '444e06cd8698015869a58ca0c868942e324c1a332ca1dbe0bf6ee3361387e76e:pXtdBELS5nYUGudppQWouXtezbCPUz52lU7KidvSnG+htfDJeVoRpQdYWOQ4MEee61tnWUBWsF+JHW86PLP25g==:1000:UvEteIZQmuUJTAfshuSJR+GpFpOnzrWzxBRUKOfOsk7NlEb6zsdOsb/gn9LrFizOK/BVxQadU0B+fGFHfUY+0dipK9OZkbM6vo4/w1OHn6iTUCVnyShGs39lp7KplLyJUx/kPP8x/3Ggp/OJ8b+Om4wdYc5HokAZB6LZ99uUyHty6q6phmTeDIZI6+do/PWNOE85etB6za/J/674KNMhv/o44eGdYHfqLwBa5LIviXM5Cs8rS5Qs5KwjWe88PIWcgzOPeuOttzh9BgPsiPFDJDTn3GFfqCk5mAZTGznQB0P6fc7KMuLkYOY3PVk1fs+XOWjwX6Qj8Q04B8USqtviQOvuxMrADlnSfiWw5Hrf3/E/E2qYjKAN4nFZXNM/2T1Mo8CDJtS1njhwj1DPHRRy3q4vOZ10BL6jP8/q6jsXcce2UwMNz3FeI67YXUI2QndDw9GDx2cNdGLmIer1sjCf/b3JODoEefOYXh+VOKrr+i8uQWfjqton9nS3jzoo25VgqWccLMrzLS50MHi+QPP0gP93ozX85sv2EOvM6R06yz0ca1eDFyz+cvOYsraLQODQ',
    '_nb_sp_id.4902': '2d9c648f-8738-460c-a613-00aae61bcb24.1789025383.1.1789029575.1789025383.dbbb2edf-2945-4dd4-a0be-731bb931d10d',
    'pxcts': '4m9m3sgz-I49a7NxKtkTT2fShBD/8QR9Qhf7wv2ANOA=:hYqNu9RUBlx/DWcQDd/s7aAWC0E6wQK8-vUVTJzArOYbtDo8S6TdP8qPPNIhO0XbuImt7DILs1Ivnl7UmYxCWHfs04eA1BUR6WcbnpK7PtPELIuktJsF9Tx9abp4up657EvR9oHheHHw3YFePqSrs7Zo71eaHDiqVUVBdhq4BeEbE/ZhgX1qGkxEe99oD7I7',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Thu+Sep+10+2026+16%3A39%3A36+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202601.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d3433e11-0788-4f37-b9e0-aad16f732771&interactionCount=2&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=C0003%3A1%2CC0001%3A1%2CC0002%3A1%2CC0004%3A1%2CSPD_BG%3A1&crTime=1789025330607&AwaitingReconsent=false&intType=1&geolocation=US%3BCA',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.conair.com/on/demandware.store/Sites-us-conair-sfra-Site/en_US/PX-Show?url=aHR0cHM6Ly93d3cuY29uYWlyLmNvbS9vbi9kZW1hbmR3YXJlLnN0b3JlL1NpdGVzLXVzLWNvbmFpci1zZnJhLVNpdGUvZW5fVVMvUHJvZHVjdC1TaG93P3BpZD0xOTAmbGFuZz1lbl9VUw%3d%3d&frame=1789029550333',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'dwsid=PUeEi89avnu5o_ls0ZaaWWBzzIVQprRdZsJ8EEVO2A3Gj1FRZpaf7NWT4luUaimLMdS-tDyujDyswoRbCtGDvA==; sid=_E25i6MK4ovGTkH8kSmtDKF58YU89uitGS8; dwanonymous_472d7a68ade4fc9505b4fb3556d571a0=abdOPQx49VA5NuPM7jtlNbDo12; _pxhd=98e6aed5222af19aec88bfe6ee18d48f232abb4683df3490052ad6fcd2b38ebd:8a2dc13a-ace1-11f1-af07-8573aadf94f8; __cq_dnt=1; dw_dnt=1; __kla_id=eyJjaWQiOiJZek5sWXpaaE0yUXRNR0k0WmkwME5qY3pMV0U1TURJdE56bGtNREE0TXpoa1l6VXkifQ==; _pxvid=8a2dc13a-ace1-11f1-af07-8573aadf94f8; __pxvid=8c93574f-ace1-11f1-9f74-5e112df355ac; BVBRANDID=d6ee111b-b594-4321-9a38-185660fa2ff0; OptanonAlertBoxClosed=2026-09-10T07:28:49.674Z; _gcl_au=1.1.1437494665.1789025330; _ga=GA1.1.994945795.1789025324; _nb_sp_ses.4902=*; _pin_unauth=dWlkPU5tWXpOak0wTmpVdE5qVTRZaTAwTW1Sa0xXSTBZelV0WkRKa04yVTNNV1V3T1RoaQ; __kla_session=%7B%22sessionId%22%3A%220122bab5-a2e1-4cda-8ba1-a9f0cf70e3c3%22%2C%22sentSessionStartedEvent%22%3Afalse%2C%22sentUserIdentifiedEvent%22%3Afalse%7D; BVBRANDSID=11d4a579-ebe8-4dc8-89dd-2fea9753b513; _ga_ZWDWKYLBY3=GS2.1.s1789028219$o2$g1$t1789029573$j37$l0$h0; _px3=444e06cd8698015869a58ca0c868942e324c1a332ca1dbe0bf6ee3361387e76e:pXtdBELS5nYUGudppQWouXtezbCPUz52lU7KidvSnG+htfDJeVoRpQdYWOQ4MEee61tnWUBWsF+JHW86PLP25g==:1000:UvEteIZQmuUJTAfshuSJR+GpFpOnzrWzxBRUKOfOsk7NlEb6zsdOsb/gn9LrFizOK/BVxQadU0B+fGFHfUY+0dipK9OZkbM6vo4/w1OHn6iTUCVnyShGs39lp7KplLyJUx/kPP8x/3Ggp/OJ8b+Om4wdYc5HokAZB6LZ99uUyHty6q6phmTeDIZI6+do/PWNOE85etB6za/J/674KNMhv/o44eGdYHfqLwBa5LIviXM5Cs8rS5Qs5KwjWe88PIWcgzOPeuOttzh9BgPsiPFDJDTn3GFfqCk5mAZTGznQB0P6fc7KMuLkYOY3PVk1fs+XOWjwX6Qj8Q04B8USqtviQOvuxMrADlnSfiWw5Hrf3/E/E2qYjKAN4nFZXNM/2T1Mo8CDJtS1njhwj1DPHRRy3q4vOZ10BL6jP8/q6jsXcce2UwMNz3FeI67YXUI2QndDw9GDx2cNdGLmIer1sjCf/b3JODoEefOYXh+VOKrr+i8uQWfjqton9nS3jzoo25VgqWccLMrzLS50MHi+QPP0gP93ozX85sv2EOvM6R06yz0ca1eDFyz+cvOYsraLQODQ; _nb_sp_id.4902=2d9c648f-8738-460c-a613-00aae61bcb24.1789025383.1.1789029575.1789025383.dbbb2edf-2945-4dd4-a0be-731bb931d10d; pxcts=4m9m3sgz-I49a7NxKtkTT2fShBD/8QR9Qhf7wv2ANOA=:hYqNu9RUBlx/DWcQDd/s7aAWC0E6wQK8-vUVTJzArOYbtDo8S6TdP8qPPNIhO0XbuImt7DILs1Ivnl7UmYxCWHfs04eA1BUR6WcbnpK7PtPELIuktJsF9Tx9abp4up657EvR9oHheHHw3YFePqSrs7Zo71eaHDiqVUVBdhq4BeEbE/ZhgX1qGkxEe99oD7I7; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Sep+10+2026+16%3A39%3A36+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202601.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d3433e11-0788-4f37-b9e0-aad16f732771&interactionCount=2&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=C0003%3A1%2CC0001%3A1%2CC0002%3A1%2CC0004%3A1%2CSPD_BG%3A1&crTime=1789025330607&AwaitingReconsent=false&intType=1&geolocation=US%3BCA',
}
flush = False
fieldnames = None
max_threads = 2

VARIATION_MARKER = '/Product-Variation'
FIELD_TITLES = {
    'features': 'Features',
    'specifications': 'Specs',
    'specs': 'Specs',
}


class PerimeterXBlocked(RuntimeError):
    """Stop this run after Conair rejects the current authenticated session."""


class Pc(Get_Product):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._perimeterx_blocked = threading.Event()

    def should_stop_requests(self):
        return self._perimeterx_blocked.is_set()

    def fetch_product(self, url, category):
        response = Tool.get(url, headers=headers, cookies=cookies)
        if _Parser.is_denied(response):
            self._perimeterx_blocked.set()
            raise PerimeterXBlocked(f'PerimeterX denied product request: {url}')
        if response.status_code != 200 or not response.text:
            raise RuntimeError(
                f'Product request failed (HTTP {response.status_code}): {url}'
            )

        parser = _Parser(url, category, response.text)
        variation_payloads = []
        variation_urls = parser.variation_urls(parser.html)
        for variation_url in variation_urls:
            request_headers = {'X-Requested-With': 'XMLHttpRequest', 'Referer': url}
            variation_response = Tool.get(
                variation_url,
                headers=request_headers,
                cookies=cookies,
            )
            if _Parser.is_denied(variation_response):
                self._perimeterx_blocked.set()
                raise PerimeterXBlocked(
                    f'PerimeterX denied variation request: {variation_url}'
                )
            if variation_response.status_code != 200 or not variation_response.text:
                raise RuntimeError(
                    'Variation request failed '
                    f'(HTTP {variation_response.status_code}): {variation_url}'
                )
            try:
                payload = variation_response.json()
            except (TypeError, ValueError) as error:
                raise RuntimeError(f'Variation JSON is invalid: {variation_url}') from error
            if not isinstance(payload, dict) or not isinstance(payload.get('product'), dict):
                raise RuntimeError(f'Variation response has no product: {variation_url}')
            variation_payloads.append(payload)

        return _Parser(url, category, response.text, variation_payloads, variation_urls).run()


class _Parser:
    def __init__(self, url, category, page_html, variants=None, variation_urls=None):
        self.url = url
        self.category = category
        self.page_html = page_html
        self.html = etree.HTML(page_html)
        self.variants = variants or []
        self.variation_urls_on_page = variation_urls or []

    @staticmethod
    def is_denied(response):
        text = (response.text or '').lower()
        return response.status_code in (403, 429) or (
            'perimeterx' in text
            or 'access to this page has been denied' in text
            or 'px-show' in response.url.lower()
        )

    @staticmethod
    def text(value):
        return ' '.join(str(value or '').split()).strip()

    @staticmethod
    def html_fragment(node):
        if node is None:
            return ''
        content = ''.join(
            etree.tostring(child, encoding='unicode', method='html') for child in node
        ).strip()
        if content:
            return content
        text = _Parser.text(''.join(node.itertext()))
        return f'<p>{escape(text, quote=False)}</p>' if text else ''

    @classmethod
    def _find_product_json(cls, value):
        if isinstance(value, dict):
            value_type = value.get('@type')
            types = value_type if isinstance(value_type, list) else [value_type]
            if 'Product' in types:
                return value
            for child in value.values():
                found = cls._find_product_json(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = cls._find_product_json(child)
                if found:
                    return found
        return {}

    @classmethod
    def json_ld_product(cls, html):
        for script in html.xpath('//script[@type="application/ld+json"]'):
            try:
                value = json.loads(''.join(script.itertext()))
            except (TypeError, ValueError):
                continue
            product = cls._find_product_json(value)
            if product:
                return product
        return {}

    @classmethod
    def section_fields(cls, html):
        fields = {'Features': '', 'Specs': ''}
        if html is None:
            return fields

        headings = html.xpath('//button | //h2 | //h3 | //h4')
        for heading in headings:
            normalized = re.sub(
                r'[^a-z]+', '', cls.text(''.join(heading.itertext())).lower()
            )
            field_name = FIELD_TITLES.get(normalized)
            if not field_name or fields[field_name]:
                continue

            containers = heading.xpath(
                'ancestor::*[self::div or self::section or self::li]['
                'contains(@class, "accordion-item") or '
                'contains(@class, "accordion__item") or '
                'contains(@class, "card") or '
                'contains(@class, "product-detail")][1]'
            )
            container = containers[0] if containers else heading.getparent()
            if container is None:
                continue
            body_nodes = container.xpath(
                './/*[contains(@class, "accordion-body") or '
                'contains(@class, "card-body") or '
                'contains(@class, "collapse") or '
                'contains(@class, "content")][not(self::button)]'
            )
            value = cls.html_fragment(body_nodes[-1] if body_nodes else container)
            if value:
                fields[field_name] = value

        return fields

    @classmethod
    def variation_urls(cls, html):
        urls = []
        if html is None:
            return urls
        for raw_url in html.xpath('//*[@data-url]/@data-url'):
            url = cls.text(raw_url)
            if not url or VARIATION_MARKER not in url:
                continue
            url = Tool.URL.add_site(url)
            if url not in urls:
                urls.append(url)
        return urls

    @staticmethod
    def first_value(*values):
        for value in values:
            if value not in (None, '', [], {}):
                return value
        return None

    @classmethod
    def price(cls, product, fallback=None):
        price = product.get('price') if isinstance(product, dict) else None
        if isinstance(price, dict):
            for key in ('sales', 'list'):
                candidate = price.get(key)
                if isinstance(candidate, dict):
                    value = cls.first_value(
                        candidate.get('value'),
                        candidate.get('decimalPrice'),
                        candidate.get('price'),
                    )
                    if value is not None:
                        return Tool.clean_price(value)
            value = cls.first_value(price.get('value'), price.get('price'))
            if value is not None:
                return Tool.clean_price(value)

        offers = product.get('offers') if isinstance(product, dict) else None
        offers = offers if isinstance(offers, list) else [offers]
        for offer in offers:
            if isinstance(offer, dict) and offer.get('price') is not None:
                return Tool.clean_price(offer['price'])
        return Tool.clean_price(fallback) if fallback is not None else None

    @classmethod
    def images(cls, product, fallback=None):
        candidates = []
        if isinstance(product, dict):
            image_data = cls.first_value(product.get('images'), product.get('image'))
            if isinstance(image_data, dict):
                image_data = cls.first_value(
                    image_data.get('large'),
                    image_data.get('hi-res'),
                    image_data.get('thumbnail'),
                )
            if isinstance(image_data, str):
                candidates.append(image_data)
            elif isinstance(image_data, list):
                for item in image_data:
                    if isinstance(item, str):
                        candidates.append(item)
                    elif isinstance(item, dict):
                        value = cls.first_value(item.get('url'), item.get('src'))
                        if value:
                            candidates.append(value)
        if not candidates:
            candidates = list(fallback or [])
        return list(dict.fromkeys(value for value in candidates if value))

    @classmethod
    def attributes(cls, product):
        attributes = {}
        for item in product.get('variationAttributes') or []:
            if not isinstance(item, dict):
                continue
            name = cls.text(item.get('displayName') or item.get('attributeId'))
            value = cls.text(item.get('displayValue'))
            if not value:
                for option in item.get('values') or []:
                    if isinstance(option, dict) and option.get('selected'):
                        value = cls.text(
                            option.get('displayValue') or option.get('value') or option.get('id')
                        )
                        break
            if name and value:
                attributes[name] = value
        return attributes

    @classmethod
    def stock(cls, product, fallback=1):
        if not isinstance(product, dict):
            return fallback
        if 'available' in product:
            return 1 if product['available'] else 0
        if 'isInStock' in product:
            return 1 if product['isInStock'] else 0
        availability = str(product.get('availability') or '')
        if availability:
            return 1 if 'instock' in availability.lower() else 0
        return fallback

    def fallback_product(self):
        product = self.json_ld_product(self.html)
        name = self.text(product.get('name'))
        if not name:
            name = self.text(self.html.xpath('string((//h1)[1])'))
        sku = self.first_value(
            product.get('sku'),
            product.get('mpn'),
            self.text(self.html.xpath('string((//*[contains(@class, "product-id")])[1])')),
            urlsplit(self.url).path.rsplit('/', 1)[-1].replace('.html', ''),
        )
        description = product.get('description') or ''
        if not description:
            nodes = self.html.xpath(
                '//*[contains(@class, "product-description") or @data-product-description][1]'
            )
            description = self.html_fragment(nodes[0]) if nodes else ''
        if description and '<' not in str(description):
            description = f'<p>{escape(self.text(description), quote=False)}</p>'

        image_nodes = self.html.xpath(
            '//*[contains(@class, "product-image") or contains(@class, "pdp-image")]//img/@src | '
            '//*[@data-zoom-image]/@data-zoom-image'
        )
        brand = product.get('brand') or 'Conair'
        if isinstance(brand, dict):
            brand = brand.get('name') or 'Conair'
        return {
            'name': name,
            'sku': str(sku) if sku else None,
            'price': self.price(product),
            'description': description,
            'images': self.images(product, image_nodes),
            'stock': self.stock(product, fallback=1),
            'brand': self.text(brand) or 'Conair',
        }

    @staticmethod
    def parent_id(variation_urls, fallback):
        for url in variation_urls:
            for key, value in parse_qsl(urlsplit(url).query, keep_blank_values=True):
                if key == 'pid' and value:
                    return value
        return fallback

    def run(self):
        if self.html is None:
            raise ValueError(f'Product HTML is invalid: {self.url}')

        fallback = self.fallback_product()
        if not fallback['name'] or fallback['price'] is None:
            raise ValueError(f'Product is missing a title or price: {self.url}')

        details = self.section_fields(self.html)
        if not self.variants:
            return [Tool.Product.Simple(
                url=self.url,
                cat=self.category,
                imgs=Tool.Product.clean_imgs(fallback['images']),
                name=fallback['name'],
                sku=fallback['sku'],
                price=fallback['price'],
                desc=fallback['description'],
                brand=fallback['brand'],
                stock=fallback['stock'],
                **details,
            ).to_dic()]

        parent = self.parent_id(self.variation_urls_on_page, fallback['sku'] or fallback['name'])
        rows = []
        seen_skus = set()
        for payload in self.variants:
            product = payload['product']
            sku = self.first_value(product.get('id'), product.get('sku'))
            sku = str(sku) if sku else None
            if sku and sku in seen_skus:
                continue
            if sku:
                seen_skus.add(sku)
            name = self.text(product.get('productName') or product.get('name') or fallback['name'])
            price = self.price(product, fallback['price'])
            if not name or price is None:
                raise ValueError(f'Variant is missing a title or price: {self.url}')
            rows.append(Tool.Product.Variation(
                url=self.url,
                cat=self.category,
                imgs=Tool.Product.clean_imgs(self.images(product, fallback['images'])),
                name=name,
                sku=sku,
                price=price,
                desc=product.get('longDescription') or fallback['description'],
                att=self.attributes(product),
                parent=parent,
                brand=self.text(product.get('brand') or fallback['brand']) or 'Conair',
                stock=self.stock(product, fallback['stock']),
                **details,
            ).to_dic())
        return rows


if __name__ == '__main__':
    Pc(
        tool=Tool,
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
        catch_save_num=catch_save_num,
    ).run()
