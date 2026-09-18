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

# URL黑名单
skip_input_url_ls = []
# 未实现字段
skip_output_url_ls = []

cookies = {
    '_sfid_53a6': '{%22anonymousId%22:%2261782d3d8692daf5%22%2C%22consents%22:[]}',
    'dwanonymous_a8791599438c3ddc3eff5af11a31de6e': 'adSdSH3SwXpdHsOjaCr97H1NMb',
    '_evga_bf0d': '{%22uuid%22:%2261782d3d8692daf5%22}',
    '_gcl_au': '1.1.1155669381.1786956544',
    'og_session_id': '31755be21f9b11eb85ff7697056c1efa.243459.1786956544',
    '_ga': 'GA1.1.985251611.1786956544',
    'FPID': 'FPID2.2.2kS%2FbgbRtG5IqqqpnL5dgGdjC6%2FVWgGIoWqjwjODyho%3D.1786956544',
    '_scid': 'b0b9a493-f302-48c2-9d13-f3941d99c2a2',
    '_gtmeec': 'eyJjb3VudHJ5IjoiOWIyMDJlY2JjNmQ0NWM2ZDg5MDFkOTg5YTkxODg3ODM5N2EzZWI5ZDAwZThmNDgwMjJmYzA1MWIxOWQyMWExZCJ9',
    '_pin_unauth': 'dWlkPVltRmtZek00TXpRdFlUWXlNQzAwWWpJekxUZzVOMkl0TWpJMU4yUTVNbU00WVRCaA',
    'BVBRANDID': '22a688dd-219d-4c80-87ee-5bdc14ac907e',
    'apt-visitor-id': 'eb8bd3a7-4712-43b5-b4f4-949eb49f0d70',
    '__gtm_referrer': 'http%3A%2F%2Flocalhost%3A63342%2F',
    'gaFlags': 'ecs%3Aviewer',
    'dwac_c13e8a04b3bca6f72ab77dbed6': 'wWcjqi0wFel7dktV0kC28rVSiNMyRCRlP3s%3D|dw-only|||USD|false|America%2FNew%5FYork|true',
    'cqcid': 'adSdSH3SwXpdHsOjaCr97H1NMb',
    'cquid': '||',
    'sid': 'wWcjqi0wFel7dktV0kC28rVSiNMyRCRlP3s',
    'customer-info-reminder': '1787042926144',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    'dwsid': 'OjFHXB5H81_6zluCTnPe9k4E7CUBM8LTvsN-uKlIZ8DCbYLcs0hspogEKTNjjIyL77B-JOj9Oe1DLizOJIDwSg==',
    '_cfuvid': 'FlX5q15BMVqVbaZt2TmF3TdxRwbnVSxkFqCkSpb3UYA-1787042931.5573204-1.0.1.1-3O1v9028Glcdf3OjWplGZLzLEQj8iCq9SsH7KZkM_CE',
    'ga4_list_smooth-gloss-treatment-mask-anti-frizz-hair-smoothing': '3%2F%2Flist-result-range%2F%2F',
    'FPLC': 'xyUHnA%2FU6zFFM5HgQArHYq5VHzfeg3Tq%2BQb1GEAWrs%2FH%2FznhtiMROWrqIryIdzO0%2BD0oWAgk%2BNcUHZce8w44wWcBiczbXLFH0F5KqlvKZOPgn76Xq3pDPY%2BORUmacg%3D%3D',
    '_aqv': 'true',
    'cf_clearance': 'bK6Wor7eYi.de47MlKd4i35z6ab9Hjca0cuE.T_XJTs-1787048919-1.2.1.1-IJ41_4KSS5g9OsW3Zz4dEep6m7iPYfOx3G1x9_FDTNoXX4OPuQwukAYd_tFYEqmS9DGe2wDORir1zPTfP715vEzTOWw2ruuiqR3BBoneDjn0sHB3lPNS7baTxGvl1vaQIDIfV_NYw3j51gix7XvyK7J12hsApz0R3TEBuvVHYuy5y3vxBxNGN69A4F60mKWeFSEteoToaItMhTxm8_tNuAPDTKmj84EVEnoAQmUmcDtJl5d2NhPkOXmaEe5G8IijjHufp.GUdwI2YWvOAl1MdxPM8hWwGFdWNhZ1Ai4OZ7tCwggzILXSC2at1TM0JEq.TCbFF4C4gpGlP8xL3OxXKUL1JdTxhlHdVK7LFc_9zLBlgb5oImXNGSp5ma_ZXjsqQaCc5c1OzeJzt33Vk0d7Oo0hAe.vT5BQYuN.E7B1nefGj7D_umrJLP2JpDsVTm3w',
    '__cf_bm': 'HZjKOC8hqAijfxs_A376cfkGmLu2LaLfA3Tk9gca6YM-1787048919.2655733-1.0.1.1-jVsBQBjV427WRK5GTizxfTFun8JUSbe7xOOE0sysTbAIJisOPBzFTJOHIT6KaT2jtS4Vr66Oh3qSZTh8A705piN1JYaKA5q6RoTBLKEVd78QUmGprpS5c.WA0fOnMwhp',
    'fw_se': '{%22value%22:%22fws2.941aca16-39a0-442e-b2bf-7ea24e7c53b5.7.1787049183282%22%2C%22createTime%22:%222026-08-18T10:33:03.282Z%22}',
    'BVBRANDSID': '234b7610-fd96-4e27-bb93-43c070d878a5',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Tue+Aug+18+2026+18%3A38%3A03+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202605.1.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&hosts=&consentId=8b4d80f0-8a63-4c1d-92f6-2519c4e8b568&interactionCount=1&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=3%3A1%2C9%3A0%2CBG1243%3A1%2C1%3A1%2CBG1244%3A1%2C2%3A1%2C4%3A1&crTime=1786956163756&AwaitingReconsent=false',
    'fw_uid': '{%22value%22:%227af772c2-eeff-470e-a4b1-6e3e17463e4b%22%2C%22createTime%22:%222026-08-18T10:38:05.087Z%22}',
    'FPGSID': '1.1787049183.1787049486.G-QC89V5Y8L2.8_M2BK2YNFA68TBJ53kHrQ.G-50B660WM08.5wju-nIDbm6fka4_q7TC5A',
    'forterToken': '6560b5e542b5415eb1ee4232ad6beec6_1787049482310__UDF43-mnf-anf-dnf-nnf_27ck_',
    '_ga_QC89V5Y8L2': 'GS2.1.s1787045228$o4$g1$t1787049526$j13$l0$h109317262',
}

headers = {
    'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'i',
    'referer': 'https://www.pureology.com/hair-care/hydrate-love-luster-set.html',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version': '"151.0.4129.86"',
    'sec-ch-ua-full-version-list': '"Not=A?Brand";v="99.0.0.0", "Microsoft Edge";v="151.0.4129.86", "Chromium";v="151.0.7922.138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"15.0.0"',
    'sec-fetch-dest': 'image',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    # 'cookie': '_sfid_53a6={%22anonymousId%22:%2261782d3d8692daf5%22%2C%22consents%22:[]}; dwanonymous_a8791599438c3ddc3eff5af11a31de6e=adSdSH3SwXpdHsOjaCr97H1NMb; _evga_bf0d={%22uuid%22:%2261782d3d8692daf5%22}; _gcl_au=1.1.1155669381.1786956544; og_session_id=31755be21f9b11eb85ff7697056c1efa.243459.1786956544; _ga=GA1.1.985251611.1786956544; FPID=FPID2.2.2kS%2FbgbRtG5IqqqpnL5dgGdjC6%2FVWgGIoWqjwjODyho%3D.1786956544; _scid=b0b9a493-f302-48c2-9d13-f3941d99c2a2; _gtmeec=eyJjb3VudHJ5IjoiOWIyMDJlY2JjNmQ0NWM2ZDg5MDFkOTg5YTkxODg3ODM5N2EzZWI5ZDAwZThmNDgwMjJmYzA1MWIxOWQyMWExZCJ9; _pin_unauth=dWlkPVltRmtZek00TXpRdFlUWXlNQzAwWWpJekxUZzVOMkl0TWpJMU4yUTVNbU00WVRCaA; BVBRANDID=22a688dd-219d-4c80-87ee-5bdc14ac907e; apt-visitor-id=eb8bd3a7-4712-43b5-b4f4-949eb49f0d70; __gtm_referrer=http%3A%2F%2Flocalhost%3A63342%2F; gaFlags=ecs%3Aviewer; dwac_c13e8a04b3bca6f72ab77dbed6=wWcjqi0wFel7dktV0kC28rVSiNMyRCRlP3s%3D|dw-only|||USD|false|America%2FNew%5FYork|true; cqcid=adSdSH3SwXpdHsOjaCr97H1NMb; cquid=||; sid=wWcjqi0wFel7dktV0kC28rVSiNMyRCRlP3s; customer-info-reminder=1787042926144; __cq_dnt=0; dw_dnt=0; dwsid=OjFHXB5H81_6zluCTnPe9k4E7CUBM8LTvsN-uKlIZ8DCbYLcs0hspogEKTNjjIyL77B-JOj9Oe1DLizOJIDwSg==; _cfuvid=FlX5q15BMVqVbaZt2TmF3TdxRwbnVSxkFqCkSpb3UYA-1787042931.5573204-1.0.1.1-3O1v9028Glcdf3OjWplGZLzLEQj8iCq9SsH7KZkM_CE; ga4_list_smooth-gloss-treatment-mask-anti-frizz-hair-smoothing=3%2F%2Flist-result-range%2F%2F; FPLC=xyUHnA%2FU6zFFM5HgQArHYq5VHzfeg3Tq%2BQb1GEAWrs%2FH%2FznhtiMROWrqIryIdzO0%2BD0oWAgk%2BNcUHZce8w44wWcBiczbXLFH0F5KqlvKZOPgn76Xq3pDPY%2BORUmacg%3D%3D; _aqv=true; cf_clearance=bK6Wor7eYi.de47MlKd4i35z6ab9Hjca0cuE.T_XJTs-1787048919-1.2.1.1-IJ41_4KSS5g9OsW3Zz4dEep6m7iPYfOx3G1x9_FDTNoXX4OPuQwukAYd_tFYEqmS9DGe2wDORir1zPTfP715vEzTOWw2ruuiqR3BBoneDjn0sHB3lPNS7baTxGvl1vaQIDIfV_NYw3j51gix7XvyK7J12hsApz0R3TEBuvVHYuy5y3vxBxNGN69A4F60mKWeFSEteoToaItMhTxm8_tNuAPDTKmj84EVEnoAQmUmcDtJl5d2NhPkOXmaEe5G8IijjHufp.GUdwI2YWvOAl1MdxPM8hWwGFdWNhZ1Ai4OZ7tCwggzILXSC2at1TM0JEq.TCbFF4C4gpGlP8xL3OxXKUL1JdTxhlHdVK7LFc_9zLBlgb5oImXNGSp5ma_ZXjsqQaCc5c1OzeJzt33Vk0d7Oo0hAe.vT5BQYuN.E7B1nefGj7D_umrJLP2JpDsVTm3w; __cf_bm=HZjKOC8hqAijfxs_A376cfkGmLu2LaLfA3Tk9gca6YM-1787048919.2655733-1.0.1.1-jVsBQBjV427WRK5GTizxfTFun8JUSbe7xOOE0sysTbAIJisOPBzFTJOHIT6KaT2jtS4Vr66Oh3qSZTh8A705piN1JYaKA5q6RoTBLKEVd78QUmGprpS5c.WA0fOnMwhp; fw_se={%22value%22:%22fws2.941aca16-39a0-442e-b2bf-7ea24e7c53b5.7.1787049183282%22%2C%22createTime%22:%222026-08-18T10:33:03.282Z%22}; BVBRANDSID=234b7610-fd96-4e27-bb93-43c070d878a5; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Aug+18+2026+18%3A38%3A03+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202605.1.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&hosts=&consentId=8b4d80f0-8a63-4c1d-92f6-2519c4e8b568&interactionCount=1&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=3%3A1%2C9%3A0%2CBG1243%3A1%2C1%3A1%2CBG1244%3A1%2C2%3A1%2C4%3A1&crTime=1786956163756&AwaitingReconsent=false; fw_uid={%22value%22:%227af772c2-eeff-470e-a4b1-6e3e17463e4b%22%2C%22createTime%22:%222026-08-18T10:38:05.087Z%22}; FPGSID=1.1787049183.1787049486.G-QC89V5Y8L2.8_M2BK2YNFA68TBJ53kHrQ.G-50B660WM08.5wju-nIDbm6fka4_q7TC5A; forterToken=6560b5e542b5415eb1ee4232ad6beec6_1787049482310__UDF43-mnf-anf-dnf-nnf_27ck_; _ga_QC89V5Y8L2=GS2.1.s1787045228$o4$g1$t1787049526$j13$l0$h109317262',
}


# CSV输出表头
fieldnames = None

from _ljp.mb.zj import Step3

class _T:
    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.typ = 'simple'
        self.html = etree.HTML(res_text)

    def get_main_name(self, html):
        try:
            name = html.xpath('//div[@class="c-product-main__name-wrapper"]//h1//text()')
            name = ''.join(name).strip()
            return name
        except Exception as e:
            raise ValueError(f'获取主名称失败:{e}') from e


    def get_main_price(self, html):
        try:
            _l = html.xpath('//div[@class="l-column h-margin-bottom-3 m-small-6 m-large-6"]/a')
            for l in _l:
                url = l.get('href')
                if url == self.url:
                    price = l.xpath('.//span[@class="c-product-price__value"]//text()')
                    price = ''.join(price).strip()
                    if not price:
                        price = l.xpath('.//span[@class="c-product-price__value m-old"]//text()')
                        price = ''.join(price).strip()
                    return price


            return ''

        except Exception as e:
            raise ValueError(f'获取价格失败:{e}')


    def get_main_sku(self, html):
        try:
            sku = self.url.split('/')[-1]
            return sku
        except Exception as e:
            Tool.print(f'获取sku失败:{e}')
            return ""

    def get_main_desc(self, html):
        try:
            desc = html.xpath('//h2[@class="c-product-main__subtitle"]')[0]
            return desc
        except Exception as e:
            Tool.print(f'获取描述失败:{e},url:{self.url}')
            raise

    def get_main_imgs(self, html):
        try:
            links = html.xpath("//button[@class='c-product-detail-image__image-link']//img/@src")
            ls = []
            for link in links:
                _l = link.split('?')
                base_url = _l[0] + '?'
                kws = _l[1].split('&')
                for kw in kws:
                    _k = kw.split('=')
                    name = _k[0]
                    val = _k[1]
                    if name == 'sw':
                        base_url += 'sw=' + '1400&'
                    elif name == 'sh':
                        base_url += 'sw=' + '1400&'
                    else:
                        base_url += name + '=' + val + '&'
                    link = base_url[:-1]
                ls.append(link)
            return ls
        except Exception as e:
            Tool.print(f'获取图片失败:{e}')
            raise


    def get_att(self,html):
        try:
            return {}
        except Exception as e:
            Tool.print(f'获取属性失败:{e}')
            return {}

    def _get_cb(self):
        xp = [
              '//div[@class="l-column h-margin-bottom-3 m-small-4 m-large-4"]/a',
              '//div[@class="l-column h-margin-bottom-3 m-small-6 m-large-6"]/a',
              '//div[@class="l-column h-margin-bottom-3 m-small-12 m-large-12"]/a'
              ]
        ls = []
        for i in xp:
            ls.extend(self.html.xpath(i))
        return ls

    def check_cob(self, html):
        """判断是否存在变体商品"""

        try:
            s_ls = self._get_cb()
            if s_ls:
                return True
            else:

                return False
        except Exception as e:
            Tool.print(f'检测变体失败:{e}')
            return False

    def get_cobs(self, html):
        """抓取所有变体数据"""
        try:
            cobs = []
            s_ls = self._get_cb()
            for s in s_ls:
                # TODO 提取变体字段
                cob_imgs_ls = self.main_img
                cob_name = self.main_name
                cob_price =  s.xpath('.//span[@class="c-product-price__value"]//text()')
                cob_price = ''.join(cob_price).strip()
                if not cob_price:
                    cob_price = s.xpath('.//span[@class="c-product-price__value m-old "]//text()')
                    cob_price = ''.join(cob_price).strip()
                v_name = s.get('data-js-value')
                cob_sku = None
                cob_att = {
                    'Size' : v_name
                }


                cob_price = Tool.clean_price(cob_price)
                cob_imgs = Tool.Product.clean_imgs(cob_imgs_ls)
                cob = Tool.Product.Variation(
                    url=self.url, cat=self.category, imgs=cob_imgs,
                    name=cob_name, desc=self.main_desc, price=cob_price,
                    sku=cob_sku, att=cob_att,parent=self.main_sku
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

            self.main_desc = main_desc
            self.main_sku = main_sku
            self.main_price = main_price
            self.main_name = main_name
            self.main_img = main_img
            self.main_att = main_att

            if self.check_cob(self.html):
                self.typ = 'variation'

            if self.typ == 'simple':
                if not self.main_price:
                    price = self.html.xpath('//h2[@class="c-product-main__subtitle"]/p/small/text()')[0][1:-1].replace(
                        'Orig', '').replace('value', '').replace(')', '')
                    self.main_price = Tool.clean_price(price)
                    Tool.print(f'无价格，重新请求后价格:{self.main_price}')
                product = Tool.Product.Simple(
                    url=self.url, cat=self.category, imgs=main_img,
                    name=main_name, sku=main_sku, price=self.main_price,
                    desc=main_desc,**main_att
                ).to_dic()
                return [product]

            return self.get_cobs(self.html)
        except Exception as e:
            Tool.print(f'run 解析失败:{e}')
            return []

class Pc(Step3):


    def fetch_product(self, url, category):
        """请求并解析单个商品。

        返回标准化产品字典列表（每个元素为 Product.to_dic() 结果）。
        """
        res = Tool.get(url,headers=headers,cookies=cookies)

        tx = res.text
        Tool.HTML.save(tx)
        T = _T(url,category,tx)

        ls = T.run()

        return ls




if __name__ == '__main__':
    pc = Pc(tool=Tool, input_path=input_file, output_path=output_file, fail_file=fail_file,
            skip_input_url_ls=skip_input_url_ls, skip_output_url_ls=skip_output_url_ls,
            ts_num=ts_num, fieldnames=fieldnames, catch_path=catch_path, index_path=index_path,
            output_ts_file=output_ts_file)
    pc.run()
