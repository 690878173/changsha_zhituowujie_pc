import time
from logging import warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import Tool
file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
cookies = {
    '__apex_test__': '__apex_test__',
    'yotpo_pixel': '67e7dd28-2c26-4753-9130-046ef0d987b6',
    'tag_user_id': '381b164c-4801-4af6-bb69-77e72afefa58-1785810503629',
    '__obref': '414e29c1-b6c7-4e08-860a-73a3492dee26',
    '_gcl_au': '1.1.160345473.1785810505',
    '_ga': 'GA1.1.53714109.1785810505',
    '__attentive_id': 'f6ff5f88d184430e96b3494ecb1e0ed4',
    '__attentive_cco': '1785810505728',
    '_attn_bopd_': 'browser',
    '__attentive_custom_ids': '[{%22name%22:%22fastSimonID%22%2C%22value%22:%225d9a558a-8b57-402f-9359-1f08a097d301_g01KZ59KQ0DB7XM0Y5C5D72W46E%22}]',
    '_shopify_y': 'd1a6aa6a-9db5-4e04-a0e6-65cf933541ee',
    '__attn_eat_id': '381b164c-4801-4af6-bb69-77e72afefa58-1785810503629',
    '_sp_id.00a4': '14e289d20aaeb913.1785810505.1.1785812298.1785810505',
    '_attn_': 'eyJ1Ijoie1wiY29cIjoxNzg1ODEwNTA1NzI3LFwidW9cIjoxNzg1ODEwNTA1NzI3LFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcImY2ZmY1Zjg4ZDE4NDQzMGU5NmIzNDk0ZWNiMWUwZWQ0XCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg1ODE1MTQwMjU0LFwidW9cIjoxNzg1ODE1MTQwMjU0LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL2F0YmpoLmdldGNhc2VseS5jb21cIn0ifQ==',
    '_shopify_s': '3aebc413-37b1-49ef-918c-264667007217',
    'tag_session': '904578dc-1aa4-4d1c-be3f-3c5d1d081d7f-77e35c35-2135-4d12-a14e-413f1198dbaf-1785823629444',
    '_ga_EV91M7JDGZ': 'GS2.1.s1785823630$o3$g0$t1785823630$j60$l0$h2043721314',
    '_ga_YY66KNDXFF': 'GS2.1.s1785823630$o3$g0$t1785823630$j60$l0$h0',
    'cart_currency': 'USD',
    '_shopify_essential': ':AZ_KmcI4AAEACUFmyIGDSwpZT4Xnkr9jqan0mMFRY45UDt8FyR4aiJDfmo-TJG5KFFwe-wqr81-cUOJfLQhsTSc4jV4UYsfwe1pkwdS0m5DZUdDKaDeOOzuJdJxxY2RxaT9lWO-5hadZpp4CF2udEAN7bXF0_Zq0XEqJgI3QmE7cxdhYaTK8yVGeSfHpX-JKzKG6HrfZ2-Sfo60f81GkdzInFUT-9oYMoLDygOcnpfd21AJNaLF05yWPUUHO8a6pXJkh72OH2loGMRYPnF7ryA7M5m_pPTZS8Lqrt6O6Ec7PODBtGGtS1XInqMxTmivpN6tDqgf8JST74RBcBs382dBJeGP8XPOtvWSAkx1lfCvifK9ivKRNK-Rmow0XT-lwZ-0e7__dj3pcisWMyCb0OYsTNtWQOKi-cydiyx2BgJen6VagLN0xcn4iVqQzhKF0iiV44lfGHbbhwAuSPUfZZHNxnmAS1WjpUYy3:',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    # 'cookie': '__apex_test__=__apex_test__; yotpo_pixel=67e7dd28-2c26-4753-9130-046ef0d987b6; tag_user_id=381b164c-4801-4af6-bb69-77e72afefa58-1785810503629; __obref=414e29c1-b6c7-4e08-860a-73a3492dee26; _gcl_au=1.1.160345473.1785810505; _ga=GA1.1.53714109.1785810505; __attentive_id=f6ff5f88d184430e96b3494ecb1e0ed4; __attentive_cco=1785810505728; _attn_bopd_=browser; __attentive_custom_ids=[{%22name%22:%22fastSimonID%22%2C%22value%22:%225d9a558a-8b57-402f-9359-1f08a097d301_g01KZ59KQ0DB7XM0Y5C5D72W46E%22}]; _shopify_y=d1a6aa6a-9db5-4e04-a0e6-65cf933541ee; __attn_eat_id=381b164c-4801-4af6-bb69-77e72afefa58-1785810503629; _sp_id.00a4=14e289d20aaeb913.1785810505.1.1785812298.1785810505; _attn_=eyJ1Ijoie1wiY29cIjoxNzg1ODEwNTA1NzI3LFwidW9cIjoxNzg1ODEwNTA1NzI3LFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcImY2ZmY1Zjg4ZDE4NDQzMGU5NmIzNDk0ZWNiMWUwZWQ0XCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg1ODE1MTQwMjU0LFwidW9cIjoxNzg1ODE1MTQwMjU0LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL2F0YmpoLmdldGNhc2VseS5jb21cIn0ifQ==; _shopify_s=3aebc413-37b1-49ef-918c-264667007217; tag_session=904578dc-1aa4-4d1c-be3f-3c5d1d081d7f-77e35c35-2135-4d12-a14e-413f1198dbaf-1785823629444; _ga_EV91M7JDGZ=GS2.1.s1785823630$o3$g0$t1785823630$j60$l0$h2043721314; _ga_YY66KNDXFF=GS2.1.s1785823630$o3$g0$t1785823630$j60$l0$h0; cart_currency=USD; _shopify_essential=:AZ_KmcI4AAEACUFmyIGDSwpZT4Xnkr9jqan0mMFRY45UDt8FyR4aiJDfmo-TJG5KFFwe-wqr81-cUOJfLQhsTSc4jV4UYsfwe1pkwdS0m5DZUdDKaDeOOzuJdJxxY2RxaT9lWO-5hadZpp4CF2udEAN7bXF0_Zq0XEqJgI3QmE7cxdhYaTK8yVGeSfHpX-JKzKG6HrfZ2-Sfo60f81GkdzInFUT-9oYMoLDygOcnpfd21AJNaLF05yWPUUHO8a6pXJkh72OH2loGMRYPnF7ryA7M5m_pPTZS8Lqrt6O6Ec7PODBtGGtS1XInqMxTmivpN6tDqgf8JST74RBcBs382dBJeGP8XPOtvWSAkx1lfCvifK9ivKRNK-Rmow0XT-lwZ-0e7__dj3pcisWMyCb0OYsTNtWQOKi-cydiyx2BgJen6VagLN0xcn4iVqQzhKF0iiV44lfGHbbhwAuSPUfZZHNxnmAS1WjpUYy3:',
}

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
        limit = 250
        params = {
            'page': page,
            # 'limit': 250  # Shopify 单次请求上限 250 条，极大地减少翻页次数
        }

        try:
            # JSON 接口通常对 Headers 要求较低，但带上 User-Agent 更安全
            # headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = Tool.get(api_url, params=params, timeout=20, verify=False,headers=headers)

            if response.status_code != 200:
                Tool.print(f"   [!] 接口响应异常 (Status: {response.status_code})，停止翻页,url:{api_url}")
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
            if len(products) < limit:
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
            if len(detail_urls) == 0:
                Tool.print(f"--- 分类 [{name}] 处理完毕，总计获得 {len(detail_urls)} 个链接 ---")
        else:
            warning('未更改站点类型为shopify')

        Tool.File.save_json(result, save_path)

    total_count = sum(len(v) for v in result.values())
    print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 {save_path}")
    if num > 0:
        Tool.print(f"   [!] 抓取失败的分类有 {num} 个")


if __name__ == '__main__':
    main()