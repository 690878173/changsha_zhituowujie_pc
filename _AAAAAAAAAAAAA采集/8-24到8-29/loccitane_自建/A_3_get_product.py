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

headers = None
cookies = {
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Sat+Aug+29+2026+10%3A53%3A13+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202607.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d92bb841-e4b7-427b-911a-049cd65d2930&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1%2CSPD_BG%3A1&intType=1&isDntEnabled=0&geolocation=US%3BCA&prevHadToken=0&AwaitingReconsent=false',
    'dwac_a727347a0b73166c555e3c5820': 'FzNwzvQwbxoZwaAysBcXtoTAtCHmgRH5cy4%3D|dw-only|||USD|false|Etc%2FUTC|true',
    'cquid': '||',
    'dwanonymous_dee395c8970fc2272ed4e02de3ef745c': 'abNDSC0pTsBtBVT5no1ag30GLr',
    'sid': 'FzNwzvQwbxoZwaAysBcXtoTAtCHmgRH5cy4',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    'dwsid': 'Bhqw_iXF6hqdHymTeJIz5pXpdBE3dJT59_DjZW2Ti0zkIiRRO6FldhsSzuadT5ilXqX2haYovOR3RPKO_3tA0A==',
    'OptanonAlertBoxClosed': '2026-08-29T01:25:53.764Z',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Sat+Aug+29+2026+09%3A25%3A53+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202511.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=d92bb841-e4b7-427b-911a-049cd65d2930&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1%2CSPD_BG%3A1&intType=1',
    '_gcl_au': '1.1.531873312.1787966754',
    '_ga': 'GA1.1.735871438.1787966755',
    'FPID': 'FPID2.2.sEDCjjBJwwtkoMYpP42h3KdBtTWIVBz92Vi1Vx5DzH0%3D.1787966755',
    'FPLC': 'gpAzcPyEbcPMCPFtMArFtjH51SeSzvkE3JrT%2FJVbUuTE82qi4lDu8mm0vp4dMApgWj1vU7k%2BBzsgmqN5b7SPq7qxY%2BgmP20L3%2FtQTso656Km0SAq4IZDXar8ju8zjQ%3D%3D',
    'dwac_dd41ae5d1d9f257ffbb54354e5': 'FzNwzvQwbxoZwaAysBcXtoTAtCHmgRH5cy4%3D|dw-only|||USD|false|US%2FEastern|true',
    'cqcid': 'acR1GHAwmKOXhIjUa3OPM0gOeT',
    'cc-nx-g_OCC_US': 'kAmMh7HqxeCQZJY_lW3D27n6gcxYUDMdtHNvnZHTFis',
    'usid_OCC_US': '63b7b718-bd31-4e28-956c-eb94e50b4392',
    'OCC_ABTestInHouseSegment': 'us_aa_engine_validation_2026_0:control',
    'OCC_US_Personalization': '"{\\"segment\\":\\"\\",\\"purchaseProducts\\":\\"\\",\\"collections\\":\\"\\"}"',
    'dwanonymous_ba53c4ee9781407e12f4bf01a897ab37': 'acR1GHAwmKOXhIjUa3OPM0gOeT',
    'og_optins': 'W10=',
    'og_session_id': '3c61058ad29e11e299d20026b93abf5d.964378.1787966777',
    'trustedsite_visit': '1',
    'FPAU': '1.1.531873312.1787966754',
    '_fbp': 'fb.1.1787966779350.1276671414',
    '_gtmeec': 'eyJzdCI6IjY4YWEzYjMwYjE2ZTM0YTc0Nzk2YjY5ODFmMTliYTMzYWY1MTViMzYxZjFmMThlNmRjNzY4NGZiNWFlMWYwZWQifQ%3D%3D',
    '_scid': 'd79418e9-9df4-49f4-40e4-45f1ecc1cd5b',
    '_pin_unauth': 'dWlkPU1URXpOVFJoT1RFdE9EQmhOQzAwTkRWakxUaGtaV1F0WkdSa01tWm1NVFUyTkdVNA',
    'og_site': '3c61058ad29e11e299d20026b93abf5d',
    '__pr.1pka': 'JueiWcxz_I',
    'userId': '816129.1787967904626',
    'forterToken': '6a52318f9182405496ac4ea3a1fedfda_1787971989771__UDF43-m4_27ck_',
    '_ga_WT9SD86FBB': 'GS2.1.s1787966755$o1$g1$t1787972415$j58$l0$h22357680',
    'datadome': '0_DitCnH4j5FC0dMZKaDY~yQy5709sL9Ntjg4zjIVZfcxa7TDqgQUqPCOYWkspCFMphazAsWkYYiCmuv4EhYd3vfcxaIauAtPN3GLMnmwXg2ctOL58ABcUsPuor4x0xv',
}

flush = False

# CSV输出表头,默认就应该为None，表头后续会处理
fieldnames = None

max_threads = 2

from _ljp.mb.zj import Get_Product

class Pc(Get_Product):


    def fetch_product(self, url, category):
        """请求并解析单个商品。

        返回标准化产品字典列表（每个元素为 Product.to_dic() 结果）。
        """
        res = Tool.get(url,headers=headers,cookies=cookies)

        tx = res.text
        html = etree.HTML(tx)
        Tool.HTML.save(tx,f'html/product/{url.split('/')[-1]}')
        T = _T(url,category,tx)

        ls = T.run()


        return ls

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
            node = html.xpath('//h1[@id="a-product-name"]/text()')
            name = "".join(node).strip()
            return name
        except Exception as e:
            raise ValueError(f'获取主名称失败:{e}') from e


    def get_main_price(self, html):
        try:
            # TODO 业务xpath
            node = html.xpath('//div[@class="m-product-price-standard"]/p[@class="a-price-sales"]//text()')[0]
            price = ''.join(node).strip()
            return price
        except Exception as e:
            raise ValueError(f'获取价格失败:{e}')
            return ""

    def get_main_sku(self, html):
        try:
            # TODO 业务xpath
            # node = html.xpath('//div[@class="xxx"]')
            sku = self.url.split('/')[-1].replace('.html','')
            return sku
        except Exception as e:
            Tool.print(f'获取sku失败:{e}')
            return ""

    def get_main_desc(self, html):
        try:
            # TODO 业务xpath
            node = html.xpath('//div[@class="a-pdp-hero-description js-limit-length-content"]')[0]
            return node
        except Exception as e:
            Tool.print(f'获取描述失败:{e}')
            return ""

    def get_main_imgs(self, html):
        try:
            # TODO 业务xpath，返回图片列表
            node = html.xpath('//div[@id="product-images"]/div//img/@src')
            return node
        except Exception as e:
            Tool.print(f'获取图片失败:{e}')
            return []

    def get_att(self,html):
        try:
            stys = html.xpath('//div[@class="container side-panel-cta-container"]')
            dic = {}
            for sty in stys:
                name = sty.xpath('./h2//text()')
                name = ''.join(name).strip()

                for i in ['Ingredients','How to apply']:
                    if i in name:
                        dic[i] = Tool.HTML.clean_product_desc(sty)
                        break


            return dic
        except Exception as e:
            Tool.print(f'获取属性失败:{e}')
            return {}

    def check_cob(self, html):
        """判断是否存在变体商品"""
        try:
            # TODO 业务逻辑，返回 True/False

            variations = html.xpath('//div[@class="product-variations"]')
            return False
        except Exception as e:
            Tool.print(f'检测变体失败:{e}')
            return False

    def get_cobs(self, html):
        """抓取所有变体数据"""
        try:
            variations = html.xpath('//div[@class="product-variations"]/ul/li//div[@class="variations-size"]/ul/li')
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
            if 'Please enable JS and disable any ad blocker' in self.res_text:
                Tool.print(f'被反扒，需要执行js')
                return []
            """统一入口：执行解析，返回标准化产品字典列表"""
            main_name = self.get_main_name(self.html)
            main_price = self.get_main_price(self.html)
            main_sku = self.get_main_sku(self.html)
            main_desc = self.get_main_desc(self.html)
            main_imgs_ls = self.get_main_imgs(self.html)
            main_att = self.get_att(self.html)

            if isinstance(main_desc,list):
                raise ValueError(f'描述字段传入列表')

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
