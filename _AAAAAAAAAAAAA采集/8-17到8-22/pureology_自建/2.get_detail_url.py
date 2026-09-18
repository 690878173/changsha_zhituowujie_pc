from lxml import etree
import requests
from config import Tool

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

from _ljp.mb.zj import GetDetail



headers = {
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version': '"151.0.4129.86"',
    'sec-ch-ua-full-version-list': '"Not=A?Brand";v="99.0.0.0", "Microsoft Edge";v="151.0.4129.86", "Chromium";v="151.0.7922.138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"15.0.0"',
}

class Pc(GetDetail):

    def fetch_page(self, p, params):
        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空或等于当前 url 表示停止翻页
        """
        url = Tool.URL.add_site(p.url)
        res = requests.get(url,headers=headers)

        html = etree.HTML(res.text)

        Tool.HTML.save(res.text)


        a = html.xpath('//h2[@class="c-product-tile__name"]/a/@href')

        ls = [Tool.URL.add_site(i) for i in a]
        p.next_url = None
        print(ls)

        return ls,False


    def build_params(self, page):
        """构造参与缓存哈希的请求参数；默认仅包含页码"""
        return  None




if __name__ == '__main__':
    pc = Pc(tool=Tool,
            file_path=file_path,
            output_path=save_path,
            catch_path=catch_path,
            index_path=index_path,
            ts_num=ts_num,
            flush=flush,
            skip_input_url_ls=skip_input_url_ls,
            skip_output_url_ls=skip_output_url_ls,

            )
    pc.run()