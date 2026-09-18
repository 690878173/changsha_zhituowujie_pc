import asyncio
import json
import re
import threading
import time
import uuid
from queue import Queue, Empty
from lxml import etree

from config import Tool

print(Tool.session._session)

# 文件路径配置
input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site("res/result.csv")
fail_file = Tool.File.path_add_site('data/fail.json')
catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
# 输出带url地址的res文件
output_ts_file = Tool.File.path_add_site('hc/result_ts.csv')

# 测试数据条数 (None = 全部抓取)
ts_num = None


input_url_no_ls = []
output_url_no_ls = []


fieldnames = None
cookies = {
    'device-id': 'fd1f440a-0948-4d9e-933f-6d3922117a19',
    'pid': 'NoEFWgvUQpCvC6FBuKxH6Q',
    'abTestingAnonymousPID': 'NoEFWgvUQpCvC6FBuKxH6Q',
    '_ga': 'GA1.1.1719990769.1786688366',
    'ajs_anonymous_id': 'be583619-fa8e-4ab6-804e-7e521d505c05',
    '_pin_unauth': 'dWlkPVlqSm1abVJsTkRZdFltRmpaUzAwTXpCa0xUaG1ObUV0WVRSaFpqRTVZV0kyWkdGag',
    '__obref': '025f3d5d-8514-48f5-ac10-d30dd5f20561',
    'experiment_': '',
    'fpGetInitStatus': 'SuccessfulResponse',
    '_iidt': 'tviApULclRI+qIJ7CDeKqOv6aZim9ED1JJtmDyGjx+l1PhK0guYutmq3muLiqWJv33m7mklgmDO2PA==',
    'fpPostInitStatus': 'SuccessfulResponse',
    '_vid_t': 'RidLmRqefk84CEc53XtWlgswc2bOSzhpGMLidfFIVNHnasrwTAiq5w4tdEVBFQo5WZb9dyEfJTObYQ==',
    'fppro_id': '{"rid":"1787120057035.qAF6aT","vid":"Tjwr9NL0253VhNXLhUr9","exp":1787552056810}',
    'sid': '5c7c0dbf-4ec9-4f94-9a25-da5c9015771d',
    'x-feature-preview': 'false',
    'i18next': 'en',
    'KP_UIDz-ssn': '0cUdMfpLhLfGeSgrrFAGzel7GvvgBuh0J4V8gPRP2euEU9atLnWGpwjpDLyjgFkt1J49OXE1jyGhTtTpslegKZnwYjXiEqA63DTNDfCwdtWvT2Z11GpcYtfu6CxC4nBTSnin4tYfmBpfBZ2jYxtZcs0U9QDu2wR1Cb69aeNJfukfGRc',
    'KP_UIDz': '0cUdMfpLhLfGeSgrrFAGzel7GvvgBuh0J4V8gPRP2euEU9atLnWGpwjpDLyjgFkt1J49OXE1jyGhTtTpslegKZnwYjXiEqA63DTNDfCwdtWvT2Z11GpcYtfu6CxC4nBTSnin4tYfmBpfBZ2jYxtZcs0U9QDu2wR1Cb69aeNJfukfGRc',
    'bm_s': 'YAAQDXHKF9wWbhWgAQAARaTcGAVO9fhCilBszcQXozyzIp8iw9bK1w2LthrCALC7RZPY6dazyn49OTXY2lZ6QqRzOAMiY9BeOnoPs8lLUMUcZ1/7OnhN7+aaNTYx6GGPrBfAifhFcbUpL04MKJzLgE6NEvKp+go+ErbIBwzj7Or2DmUPULFfkdu93V2Ci7d0l1QcfhIKCxg4VO66aA9kYez0zQtxglq0v0OHMSKeJOZNZFjPqyhRF+vp6TFWstOD7UsPwaKE9yhwOL10AAj3VIodiG/Jp1GOg88vIMTkI5OA//TrpW3I4kzolYEOxLWhKYb9avN7ZUEI1XLXsOcvv7B7GfuZESQkPQrl+cCAwwULEkXHFUea58M8eQvN5aLQ6txgkJHjMD2XkgnC6G4ES31ZqcWBwNe5CtGYehRHTt/KRwV+A2oWvH2CK4YsM8L+YHV/07Dnlt6qru/l+RTeSqqRY048hArbIPTj9TEOvolLmx+efCiFMLWp4a4iGgyAbPaJfbOajzuj2vG+bx2YPEVau4/GeYvyM/aOq4Eaeiug8If3h42gdaWIHjKJbiLFJrZLQbpEegI5mmpfsXx6bUQYrXeqHxfHgIJFx3X8SbwxTkji7gdY1en8kcyPG7KISZ/AbdT7ejvMDqoaCxuCuAkfYraMNqXyeGhkkzwveH57PrZSC5TcZpU+EvZwj5diV3RcpNotgYzdXx3u8WhjTWvT93Ksz/XQ8q0joBmNJQl9cSDNC/DaGnuqay2tPh3mA8OBUlCYwg02qdZI/Qyq1Om9AnYtYyg5g6KSWmJf7+sOJO3aaGJut/GK+hZBrrgVK7vynptjkpTf2ywQeHDTjGH3W3Eu4z31SVobQunRWsFGcMXR9qh226tOW1ZT5M44u+fHK3mXFhjcqPINQV1TPSk9Xw15pAvQh2zN4AT1eMmTIJXktOybuoJAOD2qW0vYLixmVdB0aTWsUztXdrrhyq+MJNbWAw7B3VzhbXqg30MVpok9R7GDP21J0LGE7jwql17DmRfYy8SUMSNJdiQvwqJ+ZlpnjjV3IacPzLfrfrp0HFhxEATAej8O0VKimHBpf7ZcbOG+Y9C7t2FO1yYTkph4oS/Fdziwzi6PQj5N03FUiKJTOVzwmQ5gHQvp4AtHh1V+MEgHR6j/mgcpfrrL',
    'bm_so': '01D7669311D177DB86B51CC0FB4E896410751C3E312BD3C3F3F5BBF5FAAE374C~YAAQDXHKF90WbhWgAQAARaTcGAjThE4W/fjFxlJQhuOEHssARMWML1NbTUrpiVA9tn2FRVMFXGFDZyXnueWrlwTG6GRIX+ibzYeMJCJ1WT0lwkw+v3mfwNhksSPFVUgDy8TNkrVrsJMtOUCj8mDZPBRxrs+cZK7qO5bvGgZF62otfUP504gIFZc46rOIhDXOfQKgpPgb2tt58/LRIWsMLC+0XI/iQW0/AlR2dIJggMqHqek5g6SMH32ClhWkEeo++xhGNx/EM4xqCT4fHZ+FiWJct/ZirLp6vba4Si7oFwJ6U2h9k0sl+eCatEK0BPodJW2UX1TVyVeLn8RYNPxbSeIkIrrSYsu0RQAz7xkFysQrP4j8iJM2o1xuHugkXUt2HAYmeM3znaZGSocWaGEkOvo7+PiJ48Bqu1chpWrLSH6ImiAuc0kMZOsBaKQzkbVRPw0P7C+3IQ+Oscdmr9INXqtPslUSG5Zn5A==',
    'pageviewCount': '95',
    '_ga_GM4GWYGVKP': 'GS2.1.s1787120050$o15$g1$t1787123513$j55$l0$h2023207734$d7XwqMX0XqhUj6c_2QDA52oMR86ZzrMum2A',
    '_gcl_au': '1.1.961155179.1786688360.-.-.1786688369.709740869.1787120056.1787123514',
    'forterToken': '7d944be9d9fe40f7825fc257c1e0b16e_1787123509321_2559_UDF43-m4_23ck_',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Aug+19+2026+15%3A11%3A56+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202604.2.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=BG36%3A1%2CC0004%3A1%2CC0010%3A1%2CC0011%3A1%2CC0001%3A1%2CC0003%3A1%2CC0002%3A1&AwaitingReconsent=false',
    'pageviewCount30m': '1',
    'bm_lso': '01D7669311D177DB86B51CC0FB4E896410751C3E312BD3C3F3F5BBF5FAAE374C~YAAQDXHKF90WbhWgAQAARaTcGAjThE4W/fjFxlJQhuOEHssARMWML1NbTUrpiVA9tn2FRVMFXGFDZyXnueWrlwTG6GRIX+ibzYeMJCJ1WT0lwkw+v3mfwNhksSPFVUgDy8TNkrVrsJMtOUCj8mDZPBRxrs+cZK7qO5bvGgZF62otfUP504gIFZc46rOIhDXOfQKgpPgb2tt58/LRIWsMLC+0XI/iQW0/AlR2dIJggMqHqek5g6SMH32ClhWkEeo++xhGNx/EM4xqCT4fHZ+FiWJct/ZirLp6vba4Si7oFwJ6U2h9k0sl+eCatEK0BPodJW2UX1TVyVeLn8RYNPxbSeIkIrrSYsu0RQAz7xkFysQrP4j8iJM2o1xuHugkXUt2HAYmeM3znaZGSocWaGEkOvo7+PiJ48Bqu1chpWrLSH6ImiAuc0kMZOsBaKQzkbVRPw0P7C+3IQ+Oscdmr9INXqtPslUSG5Zn5A==~1787123518485',
    'akaalb_chewy_ALB': '1787124119~op=chewy_com_ALB_use2:www-chewy-use2|~rv=56~m=www-chewy-use2:0|~os=43a06daff4514d805d02d3b6b5e79808~id=abb29ef61a4a2ca5b8750a7dc764e006',
}

headers = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.chewy.com/chewy-turkey-chicken-recipe-grain/dp/2936774',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    'x-nextjs-data': '1',
    # 'cookie': 'device-id=fd1f440a-0948-4d9e-933f-6d3922117a19; pid=NoEFWgvUQpCvC6FBuKxH6Q; abTestingAnonymousPID=NoEFWgvUQpCvC6FBuKxH6Q; _ga=GA1.1.1719990769.1786688366; ajs_anonymous_id=be583619-fa8e-4ab6-804e-7e521d505c05; _pin_unauth=dWlkPVlqSm1abVJsTkRZdFltRmpaUzAwTXpCa0xUaG1ObUV0WVRSaFpqRTVZV0kyWkdGag; __obref=025f3d5d-8514-48f5-ac10-d30dd5f20561; experiment_=; fpGetInitStatus=SuccessfulResponse; _iidt=tviApULclRI+qIJ7CDeKqOv6aZim9ED1JJtmDyGjx+l1PhK0guYutmq3muLiqWJv33m7mklgmDO2PA==; fpPostInitStatus=SuccessfulResponse; _vid_t=RidLmRqefk84CEc53XtWlgswc2bOSzhpGMLidfFIVNHnasrwTAiq5w4tdEVBFQo5WZb9dyEfJTObYQ==; fppro_id={"rid":"1787120057035.qAF6aT","vid":"Tjwr9NL0253VhNXLhUr9","exp":1787552056810}; sid=5c7c0dbf-4ec9-4f94-9a25-da5c9015771d; x-feature-preview=false; i18next=en; KP_UIDz-ssn=0cUdMfpLhLfGeSgrrFAGzel7GvvgBuh0J4V8gPRP2euEU9atLnWGpwjpDLyjgFkt1J49OXE1jyGhTtTpslegKZnwYjXiEqA63DTNDfCwdtWvT2Z11GpcYtfu6CxC4nBTSnin4tYfmBpfBZ2jYxtZcs0U9QDu2wR1Cb69aeNJfukfGRc; KP_UIDz=0cUdMfpLhLfGeSgrrFAGzel7GvvgBuh0J4V8gPRP2euEU9atLnWGpwjpDLyjgFkt1J49OXE1jyGhTtTpslegKZnwYjXiEqA63DTNDfCwdtWvT2Z11GpcYtfu6CxC4nBTSnin4tYfmBpfBZ2jYxtZcs0U9QDu2wR1Cb69aeNJfukfGRc; bm_s=YAAQDXHKF9wWbhWgAQAARaTcGAVO9fhCilBszcQXozyzIp8iw9bK1w2LthrCALC7RZPY6dazyn49OTXY2lZ6QqRzOAMiY9BeOnoPs8lLUMUcZ1/7OnhN7+aaNTYx6GGPrBfAifhFcbUpL04MKJzLgE6NEvKp+go+ErbIBwzj7Or2DmUPULFfkdu93V2Ci7d0l1QcfhIKCxg4VO66aA9kYez0zQtxglq0v0OHMSKeJOZNZFjPqyhRF+vp6TFWstOD7UsPwaKE9yhwOL10AAj3VIodiG/Jp1GOg88vIMTkI5OA//TrpW3I4kzolYEOxLWhKYb9avN7ZUEI1XLXsOcvv7B7GfuZESQkPQrl+cCAwwULEkXHFUea58M8eQvN5aLQ6txgkJHjMD2XkgnC6G4ES31ZqcWBwNe5CtGYehRHTt/KRwV+A2oWvH2CK4YsM8L+YHV/07Dnlt6qru/l+RTeSqqRY048hArbIPTj9TEOvolLmx+efCiFMLWp4a4iGgyAbPaJfbOajzuj2vG+bx2YPEVau4/GeYvyM/aOq4Eaeiug8If3h42gdaWIHjKJbiLFJrZLQbpEegI5mmpfsXx6bUQYrXeqHxfHgIJFx3X8SbwxTkji7gdY1en8kcyPG7KISZ/AbdT7ejvMDqoaCxuCuAkfYraMNqXyeGhkkzwveH57PrZSC5TcZpU+EvZwj5diV3RcpNotgYzdXx3u8WhjTWvT93Ksz/XQ8q0joBmNJQl9cSDNC/DaGnuqay2tPh3mA8OBUlCYwg02qdZI/Qyq1Om9AnYtYyg5g6KSWmJf7+sOJO3aaGJut/GK+hZBrrgVK7vynptjkpTf2ywQeHDTjGH3W3Eu4z31SVobQunRWsFGcMXR9qh226tOW1ZT5M44u+fHK3mXFhjcqPINQV1TPSk9Xw15pAvQh2zN4AT1eMmTIJXktOybuoJAOD2qW0vYLixmVdB0aTWsUztXdrrhyq+MJNbWAw7B3VzhbXqg30MVpok9R7GDP21J0LGE7jwql17DmRfYy8SUMSNJdiQvwqJ+ZlpnjjV3IacPzLfrfrp0HFhxEATAej8O0VKimHBpf7ZcbOG+Y9C7t2FO1yYTkph4oS/Fdziwzi6PQj5N03FUiKJTOVzwmQ5gHQvp4AtHh1V+MEgHR6j/mgcpfrrL; bm_so=01D7669311D177DB86B51CC0FB4E896410751C3E312BD3C3F3F5BBF5FAAE374C~YAAQDXHKF90WbhWgAQAARaTcGAjThE4W/fjFxlJQhuOEHssARMWML1NbTUrpiVA9tn2FRVMFXGFDZyXnueWrlwTG6GRIX+ibzYeMJCJ1WT0lwkw+v3mfwNhksSPFVUgDy8TNkrVrsJMtOUCj8mDZPBRxrs+cZK7qO5bvGgZF62otfUP504gIFZc46rOIhDXOfQKgpPgb2tt58/LRIWsMLC+0XI/iQW0/AlR2dIJggMqHqek5g6SMH32ClhWkEeo++xhGNx/EM4xqCT4fHZ+FiWJct/ZirLp6vba4Si7oFwJ6U2h9k0sl+eCatEK0BPodJW2UX1TVyVeLn8RYNPxbSeIkIrrSYsu0RQAz7xkFysQrP4j8iJM2o1xuHugkXUt2HAYmeM3znaZGSocWaGEkOvo7+PiJ48Bqu1chpWrLSH6ImiAuc0kMZOsBaKQzkbVRPw0P7C+3IQ+Oscdmr9INXqtPslUSG5Zn5A==; pageviewCount=95; _ga_GM4GWYGVKP=GS2.1.s1787120050$o15$g1$t1787123513$j55$l0$h2023207734$d7XwqMX0XqhUj6c_2QDA52oMR86ZzrMum2A; _gcl_au=1.1.961155179.1786688360.-.-.1786688369.709740869.1787120056.1787123514; forterToken=7d944be9d9fe40f7825fc257c1e0b16e_1787123509321_2559_UDF43-m4_23ck_; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Aug+19+2026+15%3A11%3A56+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202604.2.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=BG36%3A1%2CC0004%3A1%2CC0010%3A1%2CC0011%3A1%2CC0001%3A1%2CC0003%3A1%2CC0002%3A1&AwaitingReconsent=false; pageviewCount30m=1; bm_lso=01D7669311D177DB86B51CC0FB4E896410751C3E312BD3C3F3F5BBF5FAAE374C~YAAQDXHKF90WbhWgAQAARaTcGAjThE4W/fjFxlJQhuOEHssARMWML1NbTUrpiVA9tn2FRVMFXGFDZyXnueWrlwTG6GRIX+ibzYeMJCJ1WT0lwkw+v3mfwNhksSPFVUgDy8TNkrVrsJMtOUCj8mDZPBRxrs+cZK7qO5bvGgZF62otfUP504gIFZc46rOIhDXOfQKgpPgb2tt58/LRIWsMLC+0XI/iQW0/AlR2dIJggMqHqek5g6SMH32ClhWkEeo++xhGNx/EM4xqCT4fHZ+FiWJct/ZirLp6vba4Si7oFwJ6U2h9k0sl+eCatEK0BPodJW2UX1TVyVeLn8RYNPxbSeIkIrrSYsu0RQAz7xkFysQrP4j8iJM2o1xuHugkXUt2HAYmeM3znaZGSocWaGEkOvo7+PiJ48Bqu1chpWrLSH6ImiAuc0kMZOsBaKQzkbVRPw0P7C+3IQ+Oscdmr9INXqtPslUSG5Zn5A==~1787123518485; akaalb_chewy_ALB=1787124119~op=chewy_com_ALB_use2:www-chewy-use2|~rv=56~m=www-chewy-use2:0|~os=43a06daff4514d805d02d3b6b5e79808~id=abb29ef61a4a2ca5b8750a7dc764e006',
}

proxies= ['166.88.195.22:5654:lvubieav:7s2gpt3bbruy',
          '50.114.98.234:5718:lvubieav:7s2gpt3bbruy',
          '192.177.103.244:6737:lvubieav:7s2gpt3bbruy',
          '198.20.185.219:5589:lvubieav:7s2gpt3bbruy',
          '23.95.255.211:6795:lvubieav:7s2gpt3bbruy'
          ]

def get_proxy():
    proxy_str = proxies[uuid.uuid4().int % len(proxies)]
    ip, port, user, pwd = proxy_str.split(":")
    # return {}
    return {
        "http": f"http://{user}:{pwd}@{ip}:{port}",
        "https": f"http://{user}:{pwd}@{ip}:{port}",
    }

time_sleep = 10

class _T:
    def __init__(self,url,category,res_text):

        self.url = url
        self.category = category
        self.res_text = res_text
        self.typ = 'simple'
        # self.html = etree.HTML(res_text)
        # Tool.HTML.save(res_text)

        self.data = res_text['pageProps']['__APOLLO_STATE__']
        items = []
        for k,v in self.data.items():
            if v['__typename'] == 'Product':
                self.maim_sku = v['entryID']
                self.main_name = v['name']
                self.main_desc = v['description']
                print(self.maim_sku)
                print(self.main_name)
                print(self.main_desc)

                for _k,_v in v.items():
                    if 'items' in _k:
                        items = [i['__ref'] for i in _v]
                break
        cobs = []
        if items:
            for k, v in self.data.items():
                if k not in items:
                    continue

                cob_sku = v['id']
                cob_name = v['name']
                cob_price = v['advertisedPrice']
                cob_desc = v['description']

                cob_att = {}
                for _k, _v in v.items():
                    if 'attributeValues' in _k:
                        for i in _v:
                            ref_str = i["__ref"]
                            if ref_str.startswith("AttributeValue:"):
                                json_str = ref_str[len("AttributeValue:"):]  # 或者 split(":",1)[1]
                                # 解析json
                                data = json.loads(json_str)
                                if data.get("id"):
                                    cob_att['Size'] = data.get("value")
                                else:
                                    cob_att['Flavor'] = data.get("value")
                img = v['fullImage']
                cob_imgs = []
                for _k,_v in img.items():
                    if 'url' in _k:
                        cob_imgs.append(_v)

                cob = Tool.Product.Variation(
                    url=self.url, cat=self.category, imgs=cob_imgs,
                    name=cob_name, desc=cob_desc, price=cob_price,
                    sku=cob_sku, att=cob_att,parent=self.maim_sku
                ).to_dic()
                cobs.append(cob)
                print(cob_att)

        self.cobs = cobs






    @staticmethod
    def extract_first_price(text: str) -> str | None:
        """
        从文本中提取第一个以货币符号（$、€、£）开头的价格数字。
        支持千位分隔符（逗号）和小数点，自动去除逗号返回纯数字字符串。
        """
        # 匹配模式：
        # [$\u20AC\u00A3] 匹配 $、€ (U+20AC)、£ (U+00A3)
        # \s* 允许货币符号与数字间有任意空白
        # (\d{1,3}(?:,\d{3})*(?:\.\d+)?) 捕获数字部分，支持千位逗号分隔和小数点
        pattern = r'[$\u20AC\u00A3]\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
        match = re.search(pattern, text)
        if match:
            price_str = match.group(1)
            # 移除千位分隔符（逗号）
            price_str_clean = price_str.replace(',', '')
            return price_str_clean
        return None

    def get_main_name(self,html):
        try:
            title = html.xpath('//h1[@data-testid="product-title-heading"]/text()')[0]
            print(f'标题:{title}')
            return title
        except Exception as e:
            Tool.print(f'获取主名称失败:{e},url:{self.url}')
            Tool.HTML.save(self.res_text)

    def get_main_price(self,html):
        try:
            price = html.xpath('//span[@class="kib-product-price__label"]/text()')
            price = ''.join(price)
            price = self.extract_first_price(price)




            print(f'价格:{price}')
            return price
        except Exception as e:
            Tool.print(f'获取价格失败:{e}')

    def get_main_sku(self,html):
        try:
            sku = self.url.rstrip('/').split('/')[-1]
            print(f'sku:{sku}')
            return sku


        except Exception as e:
            Tool.print(f'获取sku失败:{e}')

    def get_main_desc(self,html):
        try:
            self.grop_ls = html.xpath('//div[@class="kib-accordion-new styles_accordion__wQO_e"]/div')

            for grop in self.grop_ls:
                node_name = grop.xpath('.//h3[@class="kib-accordion-new-item__title"]/text()')[0]
                if 'Details' in node_name:
                    desc = grop.xpath('.//div[@class="kib-accordion-new-item__content-transition"]')[0]
                    print(f'描述:{desc}')
                    return desc
        except Exception as e:
            Tool.print(f'获取描述失败:{e}')

    def get_main_imgs(self,html):
        try:
            imgs = html.xpath('//button[@data-testid="image-magnify"]/div/img/@src')
            print(f'图片:{imgs}')
            return imgs
        except Exception as e:
            Tool.print(f'获取图片失败:{e}')

    def get_att(self,html):
        not_zd_dic = ['Details']
        not_flag = False
        try:
            dic = {}
            for grop in self.grop_ls:
                node_name = grop.xpath('.//h3[@class="kib-accordion-new-item__title"]/text()')[0]
                for name in not_zd_dic:
                    if name in node_name:
                        not_flag = True
                        break
                if not_flag:
                    continue

                desc = grop.xpath('.//div[@class="kib-accordion-new-item__content-transition"]')[0]

                dic[node_name] = desc




            print(f'属性:{dic}')
            return dic
        except Exception as e:
            Tool.print(f'获取属性失败:{e}')
            return {}

    def check_cob(self,html):
        try:
            return False
        except Exception as e:
            Tool.print(f'获取cob失败:{e}')

    def get_cobs(self,html):

        try:
            cobs = []
            s_ls = []
            for _ in s_ls:
                # TODO 进行append填充
                cob_imgs_ls = []
                cob_name = ...
                cob_price =...
                cob_desc =...
                cob_sku = None
                cob_att = {}

                # NOTE==============================
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
            Tool.print(f'获取cobs失败:{e}')

    def run(self):

        # main_name = self.get_main_name(self.html)
        # main_price = self.get_main_price(self.html)
        # main_sku = self.get_main_sku(self.html)
        # main_desc = self.get_main_desc(self.html)
        # main_imgs_ls = self.get_main_imgs(self.html)
        # main_desc = Tool.HTML.clean_product_desc(main_desc)
        # main_att = self.get_att(self.html)
        #
        #
        # main_price = Tool.clean_price(main_price)
        # main_img = Tool.Product.clean_imgs(main_imgs_ls)
        #
        #
        # if self.check_cob(self.html):
        #     self.typ = 'variation'
        #
        #
        # if self.typ == 'simple':
        #     product = Tool.Product.Simple(
        #         url=self.url, cat=self.category, imgs=main_img,
        #         name=main_name, sku=main_sku, price=main_price,
        #         desc=main_desc,**main_att
        #     ).to_dic()
        #     return [product]
        #
        # return self.get_cobs(self.html)


        return self.cobs


class Crawler:
    def __init__(self, max_threads=10):
        self.input_file = input_file
        self.fail_file = fail_file
        self.max_threads = max_threads

        # 任务队列、结果队列
        self.task_queue = Queue()
        self.result_queue = Queue()

        # 缓存存储
        self.catch_data = dict()  # {seq_id: url} 任务索引
        self.index_data = dict()  # {url: [商品字典]} url -> 解析结果
        self.failures = dict()

        self.total_tasks = 0
        self.finished_count = 0

        # 内存缓存：同一url只请求一次，跨分类复用
        self.url_memory_cache = dict()

        # 线程锁
        self.global_lock = threading.Lock()
        self.cache_lock = threading.Lock()

        self._load_local_cache()


    async def _cf(self,url):
        from ljp_page.request.edge.playwright import Playwright

        edge = Playwright()
        await edge.start()


        page = await edge.new_page()


        await page.goto(url)

        await asyncio.sleep(3)


        ck = await page.cookies

        dic = {}
        for k in ck:
            dic[k['name']] = k['value']


        await edge.close()
        return dic

    def _load_local_cache(self):
        """启动加载本地持久化缓存"""
        self.catch_data = Tool.File.load_json(catch_path)
        self.index_data = Tool.File.load_json(index_path)
        Tool.print(f"本地缓存加载完成，已有任务：{len(self.catch_data)} 条")

    @staticmethod
    def _clone_with_category(rows, category):
        """复用同一url解析结果，替换分类名称，用于多分类共用商品链接场景"""
        result = []
        for row in rows:
            new_row = dict(row)
            new_row['Categories'] = category
            result.append(new_row)
        return result

    def load_tasks(self):
        """加载待抓取任务到队列"""
        data = Tool.File.load_json(self.input_file)
        seq_id = 0
        for category, urls in data.items():
            for url in urls:
                if url in input_url_no_ls:
                    continue
                self.task_queue.put((str(seq_id), category, url))
                seq_id += 1
                # 测试条数限制
                if isinstance(ts_num, int) and seq_id >= ts_num:
                    Tool.print(f'启用测试模式，限制任务数:{ts_num}')
                    self.total_tasks = seq_id
                    return
        self.total_tasks = seq_id

    def request_worker(self):

        ck = cookies
        """请求&解析工作线程"""
        while True:
            try:
                seq_id, category, url = self.task_queue.get_nowait()
            except Empty:
                break

            # 1. 判断本地磁盘缓存是否存在
            if url in self.index_data:
                with self.global_lock:
                    self.catch_data[seq_id] = {'url': url, 'category': category}
                self.result_queue.put((seq_id, category, url, [], False))
                continue

            data = []
            is_failed = False
            try:
                time.sleep(1)


                api_url = url.replace('https://www.chewy.com','https://www.chewy.com/_next/data/chewy-pdp-ui-g7CL7dVbgqWp/en-US') + '.json'

                product_ = url.replace('https://www.chewy.com/','').split('/dp/')
                pro_type = product_[0]
                pro_id = product_[1]
                params = {
                    'id': pro_id,
                    'slug': pro_type,
                }


                res = Tool.get(api_url,headers=headers,cookies=cookies,params=params)
                if not res or not res.text:
                    raise Exception("请求返回空响应")
                #
                # if res.status_code == 429:
                #     c = asyncio.run(self._cf(url))
                #     if c:
                #         ck = c
                #         print(ck)
                #     continue
                # elif res.status_code != 200:
                #     continue
                #     print(f'请求异常')
                # 页面解析
                if len(res.text) < 5000:
                    Tool.print(f'页面内容过短，可能被屏蔽: {url}')


                    continue
                parser = _T(url, category, res.json())

                raw_product_list = parser.run()

                # 标准化清洗结果
                parse_result = []
                for item in raw_product_list:
                    if isinstance(item, dict):
                        parse_result.append(item)
                    elif hasattr(item, "to_dic"):
                        parse_result.append(item.to_dic())

                # 写入内存缓存
                with self.cache_lock:
                    self.url_memory_cache[url] = parse_result
                data = parse_result

            except Exception as e:
                is_failed = True
                Tool.print(f"【任务失败】seq:{seq_id} url:{url} error:{str(e)}")
                with self.global_lock:
                    self.failures.setdefault(category, []).append(url)

            self.result_queue.put((seq_id, category, url, data, is_failed))


            time.sleep(time_sleep)

    def writer_worker(self):
        """统一写入线程：负责缓存落地，避免多线程同时写文件冲突"""
        flush_counter = 0
        flush_interval = 20

        while True:
            item = self.result_queue.get()
            if item is None:
                break

            seq_id, category, url, data, is_failed = item
            self.result_queue.task_done()

            # 成功解析，写入缓存索引
            if not is_failed:
                with self.global_lock:
                    data = data or self.index_data.get(url, [])
                    self.catch_data[seq_id] = {'url': url, 'category': category}
                    self.index_data[url] = data

            # 进度统计
            with self.global_lock:
                self.finished_count += 1
                curr = self.finished_count
                total = self.total_tasks
                status_tag = "[FAILED]" if is_failed else "[OK]"
                print(f"{status_tag} {curr}/{total} | {url}")

            # 定时落地缓存文件
            flush_counter += 1
            if flush_counter >= flush_interval:
                flush_counter = 0
                self._save_all_cache()

        # 队列结束，最终持久化一次
        self._save_all_cache()

    def _save_all_cache(self):
        Tool.File.save_json(self.catch_data, catch_path)
        Tool.File.save_json(self.index_data, index_path)

    def run(self):
        self.load_tasks()
        Tool.print(f"总共待处理任务数量: {self.total_tasks}")

        # 启动写入线程
        writer_thread = threading.Thread(target=self.writer_worker)
        writer_thread.start()

        # 启动请求线程池
        thread_list = []
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.request_worker)
            t.start()
            time.sleep(0.1)
            thread_list.append(t)

        # 等待所有请求线程结束
        for t in thread_list:
            t.join()

        # 通知写入线程退出
        self.result_queue.put(None)
        writer_thread.join()

        # 导出CSV结果
        def iter_all_product_rows():
            for req_id, dc in self.catch_data.items():
                url = dc['url']
                cat = dc['category']

                data = self.index_data[url]

                data = self._clone_with_category(data, cat)

                yield from data

        all_rows = list(iter_all_product_rows())
        # 输出带URL版本CSV
        Tool.File.save_csv(all_rows, output_ts_file, columns=fieldnames)
        # 清理url字段后输出正式文件
        clean_rows = Tool.json_del_url(all_rows)
        Tool.File.save_csv(clean_rows, output_file, columns=fieldnames)

        # 保存失败链接
        Tool.File.save_json(self.failures, fail_file)

        Tool.print("\n====================抓取完成====================")
        Tool.print(f"输出表头: {fieldnames}")
        Tool.print("确认字段是否满足导入需求！")


def main():
    crawler = Crawler(max_threads=5)
    crawler.run()


if __name__ == '__main__':
    main()
