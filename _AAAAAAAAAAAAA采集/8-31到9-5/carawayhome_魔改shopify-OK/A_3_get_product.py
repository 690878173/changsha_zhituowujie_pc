import time
from pathlib import Path

from lxml import etree

from config import Tool

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')

fail_file = Tool.File.path_add_site('fail/4.json')
# NOTE 缓存策略
index_path = Tool.File.path_add_site('hc/4/index.json')
catch_path = Tool.File.path_add_site('hc/4/catch.json')
catch_save_num = None

skip_input_url_ls = ['https://www.turtlebeach.com/products/roccat-kone-pro-mouse',
                     'https://www.turtlebeach.com/products/roccat-burst-pro-air-mouse',
                     'https://www.turtlebeach.com/products/stealth-700-gen-2-max-refurbished-headset',
                     'https://www.turtlebeach.com/products/victrix-pro-bfg-wireless-controller'

                     ]
skip_output_url_ls = []
# 默认使用fieldnames=None,自动写入自定义字段，需要控制字段写入由下游控制，这里保留所有字段
fieldnames = None

ts_num = None
cookies = {
    'ig-fv': '1788256842429',
    'external_fueled_session': '6db5f429-9dc9-4bbf-a325-64e6aef4d286',
    'ig-location': '{%22country%22:%22US%22%2C%22city%22:%22Los%20Angeles%22%2C%22continent%22:%22NA%22%2C%22latitude%22:%2234.05%22%2C%22longitude%22:%22-118.24%22%2C%22region%22:%22California%22%2C%22regionCode%22:%22CA%22}',
    'ig-id': 'ig_25fe7892ece64f3991cf1e06486fc4cf7797',
    'trackingConsent': '%7B%22analytics%22%3Atrue%2C%22preferences%22%3Atrue%2C%22marketing%22%3Atrue%2C%22saleOfData%22%3Atrue%7D',
    '__anon_id': '6db5f429-9dc9-4bbf-a325-64e6aef4d286',
    '_gcl_au': '1.1.1904052675.1788256845',
    '_fbp': 'fb.1.1788256845532.944400706631785293',
    '_ps_session': 'RvwNdBxi3F9kPai_uA1RJ',
    '_ps_site_visit': 'true',
    '_pin_unauth': 'dWlkPU56WXpOV0ptT0RBdE1XVXlOUzAwTVdRMkxXRTFNbVV0WVRWbU1UUXlZMkZoTXpoaQ',
    '_ga': 'GA1.1.1464892185.1788256851',
    'rstr_d': '{"rcid":"07a8930d-9395-42eb-9abe-226c8908bb55"}',
    'FPID': 'FPID2.2.PWg2T0XtAc5WbHVUgViN1upCMq%2F7vC2tPKL72bpB9jU%3D.1788256851',
    'FPLC': 'aomUJUytdVGNKNB7fbC1qkU1p%2FKWKK%2FzBZZowz21Hqi7YSRhcQ2cWi%2F9t8KQCy1N%2FrqZN24KVbR25x17EXWu33ypFYIKGh%2FoANr0s9UCcWCZO7eho2RKr392oAPqtw%3D%3D',
    'FPAU': '1.1.1904052675.1788256845',
    'sp': '5c009daa-4597-49f3-9c6f-1dd3dfda6da4',
    'ig-vars': '{%2254e204dc4474%22:%2237a581dea013%22%2C%22640b0cb09fcf%22:%22c59cf13d38d9%22%2C%22a07dfa34853d%22:%22e4c301f98b81%22%2C%22ad81f7fe85f6%22:%22adadf785da69%22%2C%22c71cd82fd4f3%22:%22233a115076eb%22%2C%22c9518247e305%22:%223ad7aa47064b%22%2C%22cfed92aff1fe%22:%22d9f1b8efd9b0%22%2C%22e6a4efd3a923%22:%221e5f59758860%22%2C%22ee6123228f88%22:%22ec9460c16d65%22}',
    '_nb_sp_ses.9c25': '*',
    'fueled_country_code': 'US',
    'fueled_session_id': '4a2e8630-eb74-478b-96c9-52aa39a50151',
    'fueled_timestamp_session_id': '1788318112089',
    'rrv2ses.dc74': '*',
    '_ga_2VDSM62CM4': 'GS2.1.s1788318143$o4$g1$t1788320071$j60$l0$h0',
    'ig-pv': '35',
    '_ps_session_site_visit': '%7B%22sessionId%22%3A%22a8c44d80-025f-4dc9-8649-81e993e96c8b%22%2C%22startTime%22%3A1788320085228%7D',
    '_tracking_consent': '3.AMPS_USCA_f_f_29CBDcE*Rl2eLBF2cGNNCg',
    '_ga_LV31RDQLDF': 'GS2.1.s1788318348$o4$g1$t1788320088$j60$l0$h1977031587',
    '_ga_PM7T1BG5CC': 'GS2.1.s1788318111$o4$g1$t1788320088$j52$l0$h0',
    'rrv2id.dc74': '39f67ad2-c87c-4cbd-8a33-c1f66d6f4df4.1788256852.3.1788320089.1788314034.240958fe-d4b4-4019-9925-6056fd180925',
    '_ga_C3N3CVTR29': 'GS2.1.s1788318143$o4$g1$t1788320100$j31$l0$h0',
    '_nb_sp_id.9c25': '8353c478-5ba6-4358-bbeb-6d2a6ce6fef6.1788256852.4.1788320565.1788315146.e72b1731-d756-4d3b-8c64-812e126214e0',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.carawayhome.com/collections/kitchen-tools',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'ig-fv=1788256842429; external_fueled_session=6db5f429-9dc9-4bbf-a325-64e6aef4d286; ig-location={%22country%22:%22US%22%2C%22city%22:%22Los%20Angeles%22%2C%22continent%22:%22NA%22%2C%22latitude%22:%2234.05%22%2C%22longitude%22:%22-118.24%22%2C%22region%22:%22California%22%2C%22regionCode%22:%22CA%22}; ig-id=ig_25fe7892ece64f3991cf1e06486fc4cf7797; trackingConsent=%7B%22analytics%22%3Atrue%2C%22preferences%22%3Atrue%2C%22marketing%22%3Atrue%2C%22saleOfData%22%3Atrue%7D; __anon_id=6db5f429-9dc9-4bbf-a325-64e6aef4d286; _gcl_au=1.1.1904052675.1788256845; _fbp=fb.1.1788256845532.944400706631785293; _ps_session=RvwNdBxi3F9kPai_uA1RJ; _ps_site_visit=true; _pin_unauth=dWlkPU56WXpOV0ptT0RBdE1XVXlOUzAwTVdRMkxXRTFNbVV0WVRWbU1UUXlZMkZoTXpoaQ; _ga=GA1.1.1464892185.1788256851; rstr_d={"rcid":"07a8930d-9395-42eb-9abe-226c8908bb55"}; FPID=FPID2.2.PWg2T0XtAc5WbHVUgViN1upCMq%2F7vC2tPKL72bpB9jU%3D.1788256851; FPLC=aomUJUytdVGNKNB7fbC1qkU1p%2FKWKK%2FzBZZowz21Hqi7YSRhcQ2cWi%2F9t8KQCy1N%2FrqZN24KVbR25x17EXWu33ypFYIKGh%2FoANr0s9UCcWCZO7eho2RKr392oAPqtw%3D%3D; FPAU=1.1.1904052675.1788256845; sp=5c009daa-4597-49f3-9c6f-1dd3dfda6da4; ig-vars={%2254e204dc4474%22:%2237a581dea013%22%2C%22640b0cb09fcf%22:%22c59cf13d38d9%22%2C%22a07dfa34853d%22:%22e4c301f98b81%22%2C%22ad81f7fe85f6%22:%22adadf785da69%22%2C%22c71cd82fd4f3%22:%22233a115076eb%22%2C%22c9518247e305%22:%223ad7aa47064b%22%2C%22cfed92aff1fe%22:%22d9f1b8efd9b0%22%2C%22e6a4efd3a923%22:%221e5f59758860%22%2C%22ee6123228f88%22:%22ec9460c16d65%22}; _nb_sp_ses.9c25=*; fueled_country_code=US; fueled_session_id=4a2e8630-eb74-478b-96c9-52aa39a50151; fueled_timestamp_session_id=1788318112089; rrv2ses.dc74=*; _ga_2VDSM62CM4=GS2.1.s1788318143$o4$g1$t1788320071$j60$l0$h0; ig-pv=35; _ps_session_site_visit=%7B%22sessionId%22%3A%22a8c44d80-025f-4dc9-8649-81e993e96c8b%22%2C%22startTime%22%3A1788320085228%7D; _tracking_consent=3.AMPS_USCA_f_f_29CBDcE*Rl2eLBF2cGNNCg; _ga_LV31RDQLDF=GS2.1.s1788318348$o4$g1$t1788320088$j60$l0$h1977031587; _ga_PM7T1BG5CC=GS2.1.s1788318111$o4$g1$t1788320088$j52$l0$h0; rrv2id.dc74=39f67ad2-c87c-4cbd-8a33-c1f66d6f4df4.1788256852.3.1788320089.1788314034.240958fe-d4b4-4019-9925-6056fd180925; _ga_C3N3CVTR29=GS2.1.s1788318143$o4$g1$t1788320100$j31$l0$h0; _nb_sp_id.9c25=8353c478-5ba6-4358-bbeb-6d2a6ce6fef6.1788256852.4.1788320565.1788315146.e72b1731-d756-4d3b-8c64-812e126214e0',
}

if_wp = False
time_sleep = 7
html_dir = Path(__file__).resolve().parent / 'html'
json_dir = Path(__file__).resolve().parent / 'json'

from _ljp.mb.shopify import Get_Product


class Pc(Get_Product):

    @staticmethod
    def save_debug_files(handle, html, api_json):
        html_dir.mkdir(parents=True, exist_ok=True)
        json_dir.mkdir(parents=True, exist_ok=True)

        (html_dir / f'{handle}.html').write_text(html, encoding='utf-8')
        (json_dir / f'{handle}.json').write_text(api_json, encoding='utf-8')

    def zdy_zd(self, url, html_text=None):
        """Extract the product accordion fields that are not in Storefront GraphQL."""
        if html_text is None:
            response = self.Tool.get(url)
            if response.status_code != 200:
                print('请求自定义字段失败')
                return {}
            html_text = response.text

        tree = etree.HTML(html_text)
        if tree is None:
            return {}

        fields = {}
        wanted = {'Features & Benefits', 'Non-Toxic Materials','Care & Cleaning'}
        for section in tree.xpath('//div[@class="xj1urod"]/div'):
            title = ''.join(
                text.strip()
                for text in section.xpath('./details/summary/span/text()')
                if text.strip()
            )
            if title not in wanted:
                continue
            content = section.xpath(
                './div/ul'
            )
            if content:
                value = self.tool.HTML.clean_product_desc(content[0])
                if value:
                    fields[title] = value
        return fields

    def fetch_product(self, url, category) -> list:
        Tool = self.tool
        requested_handle = Tool.URL.get_handle(url)

        _headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "X-Shopify-Storefront-Access-Token": "ced4a53e3be0ed44a4d30d47c692e211"
        }
        query = """
            query ProductByHandle($handle: String!) {
              product(handle: $handle) {
                id
                title
                description
                handle
                availableForSale
                productType
                vendor
                tags
                updatedAt
                seo {
                  title
                  description
                }
                featuredImage {
                  url
                  altText
                  width
                  height
                }
                priceRange {
                  minVariantPrice {
                    amount
                    currencyCode
                  }
                  maxVariantPrice {
                    amount
                    currencyCode
                  }
                }

                metafields(
                    identifiers: [
                      {namespace: "custom", key: "ingredients_description"},
                      {namespace: "custom", key: "product_ingredients"}
                    ]
                  ) {
                    key
                    namespace
                    type
                    value
                  }

                options {
                  id
                  name
                  values
                }
                images(first: 100) {
                  nodes {
                    url
                    altText
                    width
                    height
                  }
                }
                variants(first: 100) {
                  nodes {
                    id
                    sku
                    title
                    availableForSale
                    selectedOptions {
                      name
                      value
                    }
                    price {
                      amount
                      currencyCode
                    }
                    compareAtPrice {
                      amount
                      currencyCode
                    }
                    image {
                      url
                      altText
                      width
                      height
                    }
                    mediaGallery: metafield(namespace: "custom", key: "media_gallery") {
                      references(first: 100) {
                        nodes {
                          ... on MediaImage {
                            image {
                              url
                              altText
                              width
                              height
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """

        payload = {
            "query": query,
            "variables": {
                "handle": requested_handle
            }
        }
        retries = 3
        delay = 2
        request_url = 'https://caraway-home.myshopify.com/api/2024-10/graphql.json'

        try:
            page_response = Tool.get(url,headers=headers)
            if page_response.status_code == 404:
                return []
            if not 200 <= page_response.status_code < 400:
                raise RuntimeError(f'页面请求状态码: {page_response.status_code}')

            # 部分旧商品链接会重定向；接口必须使用最终页面的产品 handle。
            page_url = page_response.url
            handle = Tool.URL.get_handle(page_url)
            payload['variables']['handle'] = handle
            r = Tool.post(request_url, headers=_headers, json=payload, timeout=30)

            if r.status_code == 404:
                return []
            self.save_debug_files(requested_handle, page_response.text, r.text)
            # print(r.json())
            data = r.json()['data']


            #TODO 使用原url还是   p_url.replace('.json', '')

            zdy_data = self.zdy_zd(page_url, page_response.text)

            time.sleep(time_sleep)

            # print(data)
            shopify_product = data.get("product")

            shopify_product[Tool.custom_key] = zdy_data
            shopify_product['__url'] = page_url

        except Exception as e:
            Tool.print(f'[ERROR] 接口请求失败:{url} 未知异常: {e}')
            return []

        woo_product = self.mg_shopify_to_woocommerce(
            shopify_product,
            brand=Tool.site,
            custom_categories=category
        )

        print(woo_product)

        _products = [woo_product]
        variations = self.mg_create_variation_products(shopify_product, woo_product)

        if variations:
            _products.extend(variations)


        return _products


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
        catch_save_num = catch_save_num,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        fieldnames=fieldnames,
        max_threads=10,
        if_wp=if_wp
    )

    pc.run()
