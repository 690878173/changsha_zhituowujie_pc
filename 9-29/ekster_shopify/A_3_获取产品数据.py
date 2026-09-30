import time

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

skip_input_url_ls = []
skip_output_url_ls = []
# 默认使用fieldnames=None,自动写入自定义字段，需要控制字段写入由下游控制，这里保留所有字段
fieldnames = None

ts_num = None
headers = None
cookies = None

if_wp = False
time_sleep = 2

from _ljp.mb.shopify import Get_Product


class Pc(Get_Product):
    requirements = {
        "simple": ("SKU", "Name", "Description", "Images"),
        "variable": ("SKU", "Name", "Images"),
        "variation": ("SKU", "Name", "Parent"),
    }

    def zdy_zd(self, url):
        '''返回字典格式'''
        res = Tool.get(url)
        html = etree.HTML(res.text)

        Tool.HTML.save(res.text)
        dic = {}
        value_ls = html.xpath('//div[@class="tab gap-8 gap-8"]')

        for index,node in enumerate(value_ls):
            name = node.get('data-tab-label')
            for i in ['Specifications']:
                if i in name:
                    value = node
                    dic[i] = Tool.HTML.clean_product_desc(value)
                    break

            else:
                for j in ['Description', 'Shipping']:
                    if j in name:
                        break
                else:
                    print(f'未知字段:{name}')

        return dic

    def fetch_product(self, url, category) -> list:
        Tool = self.tool
        handle = Tool.URL.get_handle(url)

        p_url = f"https://www.{Tool.site}.com/products/{handle}.json"

        try:
            r = Tool.get(p_url, headers=headers,cookies=cookies,timeout=15)

            if r.status_code == 404:
                return []
            data = r.json()

            #TODO 使用原url还是   p_url.replace('.json', '')

            try:
                zdy_data = self.zdy_zd(url)
            except Exception as e:
                raise ValueError(f'自定义字段获取失败:{e}')

            time.sleep(time_sleep)

            shopify_product = data.get("product")

            shopify_product[Tool.custom_key] = zdy_data
            shopify_product['__url'] = url

        except Exception as e:
            Tool.print(f'[ERROR] 接口请求失败:{url} 未知异常: {e}')
            return []

        woo_product = self.shopify_to_woocommerce(
            shopify_product,
            brand=Tool.site,
            custom_categories=category
        )
        _products = [woo_product]
        variations = self.create_variation_products(shopify_product, woo_product)

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