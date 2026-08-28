import time

from config import Tool
from _ljp.mb.model import Base, PageModel
file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

# 测试数据条数,以初始url数量计数
ts_num = None

# 排除某些 URL（输入分类黑名单）
skip_input_url_ls = []
# 输出商品链接黑名单
skip_output_url_ls = []

# 覆盖缓存：True=无视本地缓存强制重新请求
flush = False
time_sleep = 0.5

catch_save_num = None

headers = None
cookies = None

from _ljp.mb.shopify import GetDetail

class Pc(GetDetail):


    def before_request(self, p: PageModel):
        url = p.url
        clean_url = url.strip().rstrip('/')
        api_url = f"{clean_url}/products.json"
        base_domain = Tool.URL.get_base_domain(clean_url)

        p.extra['before_request'] = {
            'api_url': api_url,
            'base_domain': base_domain,
        }


    def fetch_page(self, p:PageModel, params):
        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空 表示停止翻页
        """
        all_product_urls = []
        api_url = p.extra['before_request']['api_url']
        base_domain = p.extra['before_request']['base_domain']
        page = p.page

        url = p.next_url

        try:
            response = Tool.get(api_url, params=params, timeout=15, verify=False,headers=headers,cookies=cookies)

            if response.status_code != 200:
                Tool.print(f"   [!] 接口响应异常 (Status: {response.status_code})，停止翻页")
                return [], None

            data = response.json()
            products = data.get('products', [])

            if not products:
                # 没有产品返回，说明抓完了
                return [],None

            for p in products:
                handle = p.get('handle')
                if handle:
                    # 拼接成标准的产品详情页链接
                    full_url = f"{base_domain}/products/{handle}"
                    if full_url in self.skip_output_url_ls:
                        Tool.print(f'在跳过列表::{full_url}')
                        continue
                    all_product_urls.append(full_url)

            print(f"   第 {page} 页成功：抓取到 {len(products)} 个链接")

            # 如果返回的数量小于 limit，说明是最后一页了
            if len(products) < 250:
                return all_product_urls, None

            time.sleep(time_sleep)


            return all_product_urls, url
        except Exception as e:
            Tool.print(f"   [!] JSON 抓取过程中出错: {e}")
            return [] , None


    def build_params(self, p:PageModel):
        """构造参与缓存哈希的请求参数；默认仅包含页码"""
        params = {
            'page': p.page,
            'limit': 250  # Shopify 单次请求上限 250 条，极大地减少翻页次数
        }

        return params




if __name__ == '__main__':
    pc = Pc(tool=Tool,
            input_path=file_path,
            output_path=save_path,
            catch_path=catch_path,
            index_path=index_path,
            ts_num=ts_num,
            flush=flush,
            skip_input_url_ls=skip_input_url_ls,
            skip_output_url_ls=skip_output_url_ls,
            catch_save_num= catch_save_num

            )
    pc.run()