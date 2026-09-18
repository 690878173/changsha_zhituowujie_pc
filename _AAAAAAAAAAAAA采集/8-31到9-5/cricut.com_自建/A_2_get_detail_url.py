from urllib.parse import urlsplit

from lxml import etree
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


SEARCH_ENDPOINT = (
    'https://cricut.com/on/demandware.store/'
    'Sites-cricut-us-Site/en_US/Search-UpdateGrid'
)
PAGE_SIZE = 40
SORT_RULE = 'best-matches'
API_HEADERS = {'X-Requested-With': 'XMLHttpRequest'}


class Pc(GetDetail):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The public category URL slug is not always the SFCC cgid.
        self._cgid_cache = {}

    def _get_cgid(self, category_url):
        """Read the canonical SFCC category id from the category page."""
        if category_url in self._cgid_cache:
            return self._cgid_cache[category_url]

        cgid = None
        try:
            response = Tool.get(category_url)
            if response.status_code == 200 and response.text:
                html = etree.HTML(response.text)
                values = html.xpath('//*[@data-cgid]/@data-cgid') if html is not None else []
                cgid = next((value.strip() for value in values if value.strip()), None)
        except Exception as error:
            Tool.print(f'分类页 cgid 解析失败：{error}；使用 URL 兜底', color='yellow')

        if not cgid:
            path = urlsplit(category_url).path.rstrip('/')
            cgid = path.rsplit('/', 1)[-1] or 'root'

        self._cgid_cache[category_url] = cgid
        return cgid

    def fetch_page(self, P:PageModel, params):
        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空或等于当前 url 表示停止翻页


        确认结束 p.status = 'end'
        确认失败 p.status = 'fail' 或者set_fail()
        """
        try:
            headers = dict(API_HEADERS)
            headers['Referer'] = P.url
            response = Tool.get(SEARCH_ENDPOINT, params=params, headers=headers)
            if response.status_code != 200 or not response.text:
                P.set_fail()
                Tool.print(
                    f'Demandware 请求失败（HTTP {response.status_code}）：{P.url}',
                    color='red',
                )
                return [], None

            html = etree.HTML(response.text)
            if html is None:
                raise ValueError('响应不是有效 HTML')

            product_urls = []
            for href in html.xpath('//a[contains(@class, "product-tile__link")]/@href'):
                if not href or not href.startswith('/en-us/'):
                    continue
                product_urls.append(Tool.URL.add_site(href))
            product_urls = list(dict.fromkeys(product_urls))

            count_values = html.xpath(
                '//span[contains(@class, "js-search-result-count")]/@data-results'
            )
            total = None
            if count_values:
                try:
                    total = int(float(count_values[0]))
                except (TypeError, ValueError):
                    total = None

            start = int(params.get('start', 0))
            page_size = int(params.get('sz', PAGE_SIZE))
            has_next = bool(product_urls) and (
                start + len(product_urls) < total if total is not None
                else len(product_urls) >= page_size
            )
            if not product_urls:
                if total == 0:
                    P.set_end()
                else:
                    P.set_fail()
                    Tool.print(
                        f'Demandware 响应未找到商品卡片：{P.url}',
                        color='red',
                    )

            return product_urls, P.url if has_next else None
        except Exception as error:
            P.set_fail()
            Tool.print(f'Demandware 解析失败：{error}；{P.url}', color='red')
            return [], None

    def build_params(self, page):
        """构造 Search-UpdateGrid 参数，并让分页参数参与缓存键。"""
        return {
            'cgid': self._get_cgid(page.url),
            'srule': SORT_RULE,
            'start': (page.page - 1) * PAGE_SIZE,
            'sz': PAGE_SIZE,
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
