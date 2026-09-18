import time
from logging import warning
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



from base_f import Tool
file_path = Tool.File.path_add_site('data/ml.json')

save_path = Tool.File.path_add_site('data/detail_url.json')



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
                Tool.print(f"   [!] 接口响应异常 (Status: {response.status_code})，停止翻页")
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
                return all_product_urls

            page += 1
            time.sleep(0.5)  # JSON 接口响应快，0.5秒间隔足够

        except Exception as e:
            Tool.print(f"   [!] JSON 抓取过程中出错: {e}")
            break

    return []

def main():

    data = Tool.File.load_json(save_path)

    url_dict = Tool.File.load_json(file_path)

    result = data
    num = 0

    for name, url_data in url_dict.items():
        print(f"\n====== 正在处理分类：{name} ======")
        print(f"目标集合: {url_data.strip()}")
        if name in result and result[name]:
            Tool.print(f"   [!] 该分类已处理过，跳过", color='yellow')
            continue

        if Tool.site_type == 'shopify':
            detail_urls = shopify_get_detail_url(url_data)
            result[name] = detail_urls
            if len(detail_urls) == 0:
                num +=1

            print(f"--- 分类 [{name}] 处理完毕，总计获得 {len(detail_urls)} 个链接 ---")
        else:
            warning('未更改站点类型为shopify')

        Tool.File.save_json(result, save_path)

    total_count = sum(len(v) for v in result.values())
    print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 {save_path}")
    if num > 0:
        Tool.print(f"   [!] 抓取失败的分类有 {num} 个")















if __name__ == '__main__':
    main()