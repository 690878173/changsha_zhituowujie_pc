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
cookies = None

flush = False

# CSV输出表头,默认就应该为None，表头后续会处理
fieldnames = None

max_threads = 2

from _ljp.mb.zj import Get_Product

class Pc(Get_Product):

    def _init(self):
        super()._init()

        self.map_data = Tool.File.load_json('hc/2/teva_products.json')


    def fetch_product(self, url, category):
        """请求并解析单个商品。

        返回标准化产品字典列表（每个元素为 Product.to_dic() 结果）。
        """
        # url = Tool.config.base_url+'/p/' +url
        # res = Tool.get(url,headers=headers,cookies=cookies)
        #
        # tx = res.text
        #
        # T = _T(url,category,tx)
        # ls = T.run()

        tx=''
        T = _T(url,category,self.map_data)
        ls = T.run()


        return ls

class _T:
    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.typ = 'simple'
        self.html = ''

        self.raw_data = res_text
        # Tool.HTML.save(res_text)

        self.data = res_text.get(url)

    def get_main_name(self, html):
        try:
            # TODO 业务xpath
            return self.data['name']
        except Exception as e:
            raise ValueError(f'获取主名称失败:{e}') from e


    def get_main_price(self, html):
        try:
            # TODO 业务xpath

            return self.data['price']
        except Exception as e:
            raise ValueError(f'获取价格失败:{e}')
            return ""

    def get_main_sku(self, html):
        try:
            # TODO 业务xpath

            return self.data['sku']
        except Exception as e:
            Tool.print(f'获取sku失败:{e}')
            return ""

    def get_main_desc(self, html):
        try:
            # TODO 业务xpath
            return self.data['description']
        except Exception as e:
            Tool.print(f'获取描述失败:{e}')
            return ""

    def get_main_imgs(self, html):
        try:
            # TODO 业务xpath，返回图片列表
            return self.data['imgs']
        except Exception as e:
            Tool.print(f'获取图片失败:{e}')
            return []

    def get_att(self,html):
        try:
            # sty = html.xpath('//p[@class="chakra-text css-1al38q0"]//span//text()')
            # if sty[0] == 'Style:':
            #     sty = ''.join(sty[-1]).strip()
            #     dic = {'Style':sty}
            #     print(dic)
            #     return dic
            return {}
        except Exception as e:
            Tool.print(f'获取属性失败:{e}')
            return {}

    def check_cob(self, html):
        """判断是否存在变体商品"""
        try:
            cob = self.data.get('var')
            return cob
        except Exception as e:
            Tool.print(f'检测变体失败:{e}')
            return False

    def get_cobs(self, html):
        """抓取所有变体数据"""
        try:
            var = self.data['var']
            cobs = []
            s_ls = var.values()
            for v in s_ls:
                # TODO 提取变体字段
                imgs = self.get_main_imgs('')
                cob_imgs_ls = []


                main_sku = self.get_main_sku('')
                if self.raw_data.get(main_sku):
                    try:
                        main_sku = int(main_sku)
                    except Exception as e:
                        main_sku = int(main_sku.split('-')[0])

                sku = str(main_sku)

                new_sku = sku + '-' + v['color_map']

                if self.raw_data.get(new_sku):
                    # print(f'存在变体数据')
                    cob_imgs_ls = self.raw_data.get(new_sku)['imgs']

                else:
                    print(f'不存在变体:{new_sku}')


                    # base_path = img.rsplit('/', 1)[0]
                    # url = base_path+'/'+self.get_main_sku('')+'-'+ v['color_map']+f'_{num}.png'
                    # url = f'{base_path}/{self.get_main_sku('')}-{v['color_map']}_{num}.png'
                    # num +=1
                    # cob_imgs_ls.append(url)

                if not cob_imgs_ls:
                    continue
                cob_name = self.get_main_name('')
                cob_price = self.get_main_price('')
                cob_sku = v['sku']
                cob_att = {
                    'Color': v['color'],
                    'Size': v['size'],
                }

                cob_desc = Tool.HTML.clean_product_desc_str(self.get_main_desc(''))
                cob_price = Tool.clean_price(cob_price)
                cob_imgs = Tool.Product.clean_imgs(cob_imgs_ls)
                cob = Tool.Product.Variation(
                    url=self.url, cat=self.category, imgs=cob_imgs,
                    name=cob_name, desc=cob_desc, price=cob_price,
                    sku=cob_sku, att=cob_att,parent=self.get_main_sku('')
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



            main_desc = Tool.HTML.clean_product_desc_str(main_desc)
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
