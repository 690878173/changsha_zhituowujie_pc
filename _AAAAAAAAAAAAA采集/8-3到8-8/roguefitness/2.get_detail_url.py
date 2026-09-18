import time

from curl_cffi import requests
from curl_cffi.requests.exceptions import TooManyRedirects, RequestException
import urllib3
from lxml import etree
from config import Tool,zs


file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2.json')
# 测试数据条数,以初始url数量计数
ts_num = None

# 排除某些 URL
no_url_ls = ['https://www.roguefitness.com/weightlifting-bars-plates/storage',
             'https://www.roguefitness.com/facility-outfitting/affiliate-gyms',
             'https://www.roguefitness.com/facility-outfitting/training-gyms',
             'https://www.roguefitness.com/rogue-curl-bar-stainless-steel'
             ]

# 覆盖缓存
flush = False

@zs('需重写=>获取详细链接，返回列表,下一页码')
def get_detail_url(url,num=None):
    raw_url = url
    if 'page_number' not in url:

        if num is None:
            num=1
        else:
            url = f'{url}?page_number={num}'

    res = Tool.get(url)

    html = etree.HTML(res.text)

    product_url = html.xpath(
        '//div[@class="holder hover-enabled"]/a/@href')
    detail_links = []
    for i in product_url:
        if i is None:
            Tool.print('链接为空值')
        detail_links.append(Tool.base_url + i)

    next_a = html.xpath('.//div[@class="pagination center pagination"]/div[@class="large"]/a/@href')
    if next_a:
        next_url_d = Tool.base_url+next_a[-1]
        # print(html.xpath('.//div[@class="pagination center pagination"]/div[@class="large"]/a/@href'))
        if next_url_d != url:
            # print(next_url_d,url)
            detail_links.extend(get_detail_url(next_url_d,num+1)[0])
    detail_links = [i.split('?')[0] for i in detail_links]
    return detail_links,None


def get_detail_all_url(url):
    ls = []
    page_num = None
    while True:
        res_ls,page_num = get_detail_url(url,num=page_num)
        ls.extend(res_ls)
        if not page_num:
            break
    return ls

def parse_ml_json(flush=False):
    self = Tool

    data = self.load_json(save_path)

    url_dict = self.load_json(file_path)

    result = data

    num = 0
    for name, url_data in url_dict.items():
        if not flush:
            if name in data and data.get(name ,False):
                print(f"跳过分类：{name}，因为该分类已存在数据")
                continue
        print(f"\n====== 正在处理分类：{name} ======")
        result[name] = []
        if isinstance(url_data, str):
            url_list = [url_data]
        else:
            url_list = url_data

        # 遍历每个分类下的初始 URL
        for url in url_list:
            if isinstance(ts_num, int) and num >= ts_num:
                print(f"已处理 {num} 条数据，已超出限制，任务结束")
                break
            num += 1

            try:
                print(f"正在分析 URL: {url}")
                detail_urls = get_detail_all_url(url)
                if detail_urls:
                    # 保持顺序扩展结果
                    detail_urls = [i for i in detail_urls if i not in no_url_ls]
                    result[name].extend(detail_urls)

                    print(f"  成功获取到 {len(detail_urls)} 条详情页链接")
                else:
                    print(f"  URL: {url} 未获取到数据 (可能是 API 结构不同)")
            except Exception as e:
                print(f"  URL: {url} 处理中途中断: {e}")

        if not result[name]:
            del result[name]

    self.save_json(result, save_path)

    total_count = sum(len(v) for v in result.values())
    print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 {save_path}")

def shopify_get_detail_url(collection_url):
    """
        通过 Shopify 的 .json 接口获取该分类下所有产品的 Handle 并拼接 URL
        """
    all_product_urls = []
    page = 1
    # 确保 URL 干净，去掉结尾的斜杠，拼接 products.json
    clean_url = collection_url.strip().rstrip('/')
    api_url = f"{clean_url}/products.json"

    # 提取基础域名用于拼接产品页 (例如 https://feetures.com)
    from urllib.parse import urlparse
    parsed = urlparse(clean_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"

    while True:
        params = {
            'page': page,
            'limit': 250  # Shopify 单次请求上限 250 条，极大地减少翻页次数
        }

        try:
            # JSON 接口通常对 Headers 要求较低，但带上 User-Agent 更安全
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(api_url, params=params, headers=headers, timeout=15, verify=False)

            if response.status_code != 200:
                print(f"   [!] 接口响应异常 (Status: {response.status_code})，停止翻页")
                break

            data = response.json()
            products = data.get('products', [])

            if not products:
                # 没有产品返回，说明抓完了
                break

            for p in products:
                handle = p.get('handle')
                if handle:
                    # 拼接成标准的产品详情页链接
                    full_url = f"{base_domain}/products/{handle}"
                    all_product_urls.append(full_url)

            print(f"   第 {page} 页成功：抓取到 {len(products)} 个链接")

            # 如果返回的数量小于 limit，说明是最后一页了
            if len(products) < 250:
                break

            page += 1
            time.sleep(0.5)  # JSON 接口响应快，0.5秒间隔足够

        except Exception as e:
            print(f"   [!] JSON 抓取过程中出错: {e}")
            break

    return all_product_urls

def main():

    data = Tool.File.load_json(catch_path)

    url_dict = Tool.File.load_json(file_path)

    result = data

    num = 0
    for name, url_data in url_dict.items():
        if not flush:
            if name in data and data.get(name, False):
                print(f"跳过分类：{name}，因为该分类已存在数据")
                continue
        print(f"\n====== 正在处理分类：{name} ======")
        print(f"目标集合: {url_data.strip()}")

        if Tool.site_type == 'shopify':
            detail_urls = shopify_get_detail_url(url_data)
            result[name] = detail_urls
        else:
            result[name] = []
            # 待考虑重构，因为url为字符串
            if isinstance(url_data, str):
                url_list = [url_data]
            else:
                url_list = url_data
            # 遍历每个分类下的初始 URL
            for url in url_list:
                if isinstance(ts_num, int) and num >= ts_num:
                    print(f"已处理 {num} 条数据，已超出限制，任务结束")
                    break
                num += 1

                try:
                    print(f"正在分析 URL: {url}")
                    if url in no_url_ls:
                        Tool.print(f'跳过排除url:{url}')
                        continue
                    detail_urls = get_detail_all_url(url)
                    if detail_urls:
                        # 保持顺序扩展结果
                        detail_urls = [i for i in detail_urls if i not in no_url_ls]
                        result[name].extend(detail_urls)
                        print(f"  成功获取到 {len(detail_urls)} 条详情页链接")
                    else:
                        Tool.print(f"  URL: {url} 未获取到数据 (可能是 API 结构不同)")
                except Exception as e:
                    Tool.print(f"  URL: {url} 处理中途中断: {e}")
        Tool.File.save_json(result, catch_path)
        Tool.File.save_json(result, save_path)

    total_count = sum(len(v) for v in result.values())
    print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 {save_path}")















if __name__ == '__main__':
    main()