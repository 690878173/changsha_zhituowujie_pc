from urllib.parse import urlsplit

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

catch_save_num = None

from _ljp.mb.zj import GetDetail
from _ljp.mb.model import PageModel


SEARCH_ENDPOINT = 'https://xn0evn.a.searchspring.io/api/search/search.json'
SEARCH_SITE_ID = 'xn0evn'
RESULTS_PER_PAGE = 48


class Pc(GetDetail):

    def fetch_page(self, P:PageModel, params):
        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空或等于当前 url 表示停止翻页


        确认结束 p.status = 'end'
        确认失败 p.status = 'fail' 或者set_fail()
        """
        try:
            response = Tool.get(SEARCH_ENDPOINT, params=params)
            if response.status_code != 200:
                P.set_fail()
                Tool.print(
                    f'Searchspring 请求失败（HTTP {response.status_code}）：{P.url}',
                    color='red',
                )
                return [], None

            payload = response.json()
            results = payload.get('results', [])
            if not isinstance(results, list):
                raise ValueError('Searchspring 响应的 results 不是列表')

            product_urls = []
            for result in results:
                if not isinstance(result, dict) or not result.get('url'):
                    continue

                # 接口返回的是 myshopify 域名，详情采集使用站点正式域名。
                product_path = urlsplit(result['url']).path
                if product_path.startswith('/products/'):
                    product_urls.append(Tool.URL.add_site(product_path))

            pagination = payload.get('pagination', {})
            next_page = pagination.get('nextPage') if isinstance(pagination, dict) else 0
            has_next = isinstance(next_page, int) and next_page > P.page
            if not product_urls and not has_next:
                P.set_end()

            return list(dict.fromkeys(product_urls)), P.url if has_next else None
        except Exception as error:
            P.set_fail()
            Tool.print(f'Searchspring 解析失败：{error}；{P.url}', color='red')
            return [], None

    def build_params(self, page):
        """构造 Searchspring collection 检索参数，并作为分页缓存键的一部分。"""
        handle = urlsplit(page.url).path.rstrip('/').rsplit('/', 1)[-1]
        if not handle:
            raise ValueError(f'无法从分类地址提取 collection handle：{page.url}')

        return {
            'siteId': SEARCH_SITE_ID,
            'resultsFormat': 'native',
            'bgfilter.ss_hide': 0,
            'bgfilter.tags': 'style-group-lead',
            'bgfilter.collection_handle': handle,
            'page': page.page,
            'resultsPerPage': RESULTS_PER_PAGE,
        }




if __name__ == '__main__':
    pc = Pc(
       tool=Tool,
       input_path=file_path,
       output_path=save_path,
       catch_path=catch_path,
       index_path=index_path,
       ts_num=ts_num,
       flush=flush,
       skip_input_url_ls=skip_input_url_ls,
       skip_output_url_ls=skip_output_url_ls,
       catch_save_num=catch_save_num
       )
    pc.run()
