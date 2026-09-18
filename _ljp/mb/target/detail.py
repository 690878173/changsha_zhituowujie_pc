from curl_cffi import requests as cffi_requests
from curl_cffi.requests import RequestsError
import time
import json
import random

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'If-None-Match': 'W/"139p6pwjq7631ke"',
    'Priority': 'u=0, i',
}


def get_target_detail_urls(keyword="doritos", max_pages=9):
    """Collect Target SLP pages, then retry only pages that exhausted retries."""
    all_buy_urls = []
    api_url = 'https://cdui-orchestrations.target.com/cdui_orchestrations/v1/pages/slp'
    fingerprints = ["chrome120", "chrome124", "chrome131", "chrome136", "chrome142", "chrome145"]
    max_retries = 8

    def collect_page(page_idx, phase):
        offset = page_idx * 24
        print(
            f"[{phase}] 正在抓取第 {page_idx + 1} 页，"
            f"关键词: {keyword}, Offset: {offset}..."
        )

        params = {
            'key': '9f36aeafbe60771e321a7cc95a78140772ab3e96',
            'platform': 'WEB',
            'sapphire_channel': 'WEB',
            'sapphire_page': f'/s/{keyword}',  # 动态注入关键词
            'channel': 'WEB',
            'page': f'/s/{keyword}',           # 动态注入关键词
            'visitor_id': '019CC2643248020089F4B2866CA310CC',
            'purchasable_store_ids': '1771,1768,1113,3374,1792',
            'latitude': '41.9831',
            'longitude': '-91.6686',
            'scheduled_delivery_store_id': '1771',
            'state': 'IA',
            'store_id': '1771',
            'zip': '52404',
            'has_pending_inputs': 'false',
            'offset': str(offset),
            'keyword': keyword,
            'count': '24',
            'default_purchasability_filter': 'true',
            'include_sponsored': 'false',
            'new_search': 'true',
            'spellcheck': 'true',
            'store_ids': '1771,1768,1113,3374,1792',
            'is_seo_bot': 'false',
            'include_data_source_modules': 'true',
            'query_string': f'searchTerm={keyword}&category=0%7CAll%7Cmatchallpartial%7Call+categories&searchTermRaw={keyword}',
            'timezone': 'Asia/Shanghai',
        }

        success = False
        res_json = None
        for attempt in range(max_retries):
            fp = fingerprints[attempt % len(fingerprints)]
            try:
                # 每次都开全新 Session，TLS 握手从头开始，杜绝旧连接复用问题
                with cffi_requests.Session(impersonate=fp) as s:
                    resp = s.get(
                        api_url,
                        params=params,
                        headers=headers,
                        timeout=30
                    )

                if resp.status_code != 200:
                    print(f"请求失败，状态码: {resp.status_code}.")
                    print(f"响应内容: {resp.text[:200]}")
                    # 403/429 多半是临时限流，当作网络错误继续重试换指纹
                    if resp.status_code in (403, 429):
                        raise RequestsError(f"被限流，状态码 {resp.status_code}")
                    # 其他非 200（如 401）一般是凭证失效，重试无意义
                    break

                res_json = resp.json()
                success = True
                break

            except RequestsError as e:
                # 涵盖 TLS connect error / 连接被重置 / 超时 / 限流等
                print(f"  第 {attempt + 1}/{max_retries} 次请求失败(指纹 {fp}): {e}")
                if attempt < max_retries - 1:
                    # 退避时间指数递增：10→20→40→80→90→90→90 + 随机抖动，上限 90 秒
                    backoff = min(10 * (2 ** attempt), 90) + random.uniform(0, 5)
                    if attempt >= 2:
                        print(f"     连续失败，长冷却 {backoff:.0f} 秒后换指纹重试...")
                    else:
                        print(f"     退避 {backoff:.0f} 秒后换指纹重试...")
                    time.sleep(backoff)
                else:
                    print("     重试耗尽。")
            except Exception as e:
                print(f"发生错误: {e}")
                break

        # Keep this page for one final batch retry after all other SLP pages.
        if not success or res_json is None:
            print(
                f"[{phase}] 第 {page_idx + 1} 页重试 {max_retries} 次仍失败，"
                f"offset={offset}"
            )
            return None

        products = []
        modules = res_json.get('data_source_modules', [])
        for module in modules:
            temp_products = module.get('module_data', {}).get('search_response', {}).get('products', [])
            if temp_products:
                products = temp_products
                break

        if not products:
            print("这一页没有找到产品数据，可能到底了。")
            return []

        page_urls = []
        for p in products:
            buy_url = p.get('enrichment', {}).get('buy_url') or \
                      p.get('item', {}).get('enrichment', {}).get('buy_url')

            title = p.get('item', {}).get('product_description', {}).get('title', 'N/A')
            print(f"  -> {title}: {buy_url}")

            if buy_url:
                full_url = f"https://www.target.com{buy_url}" if not buy_url.startswith('http') else buy_url
                page_urls.append(full_url)

        return list(dict.fromkeys(page_urls))

    failed_page_indices = []
    for page_idx in range(max_pages):
        page_urls = collect_page(page_idx, "首轮")
        if page_urls is None:
            failed_page_indices.append(page_idx)
            time.sleep(random.uniform(30, 50))
            continue
        if not page_urls:
            break

        page_count = 0
        for full_url in page_urls:
            if full_url not in all_buy_urls:
                all_buy_urls.append(full_url)
                page_count += 1
        print(f"第 {page_idx + 1} 页抓取成功，新增 {page_count} 个链接")

        if page_count == 0:
            break

        # 间隔调大，降低被 Target 主动断连的概率
        time.sleep(random.uniform(8, 14))

    final_failed_page_indices = []
    if failed_page_indices:
        print(f"首轮失败 {len(failed_page_indices)} 页，开始集中补抓一次。")
        for page_idx in failed_page_indices:
            page_urls = collect_page(page_idx, "补抓")
            if page_urls is None:
                final_failed_page_indices.append(page_idx)
                continue
            for full_url in page_urls:
                if full_url not in all_buy_urls:
                    all_buy_urls.append(full_url)

    recovered_count = len(failed_page_indices) - len(final_failed_page_indices)
    print(
        "Target 分类页失败统计："
        f"首轮失败 {len(failed_page_indices)} 页，"
        f"补抓恢复 {recovered_count} 页，"
        f"最终失败 {len(final_failed_page_indices)} 页。"
    )
    if final_failed_page_indices:
        print(
            "最终失败 offset："
            + ", ".join(str(page_idx * 24) for page_idx in final_failed_page_indices)
        )
    return all_buy_urls

class GetDetail:
    def __init__(self,tool,output_path,keyword,all_num=9):
        self.Tool = tool
        self.output_path = output_path
        self.keyword = keyword
        self.all_num = all_num

    def get_keyword(self):
        return self.keyword

    def run(self):
        keyword = self.get_keyword()
        final_results = get_target_detail_urls(keyword=keyword, max_pages=self.all_num)
        res_dic = {
            'DefaultCategory':final_results
        }
        self.Tool.File.save_json(res_dic, self.output_path)

        print(f"\n任务完成！共计 {len(final_results)} 个链接已保存至: {self.output_path}")






if __name__ == "__main__":
    # 执行抓取 (示例关键词: dawn-dish)
    keyword_to_search = "Bona"
    final_results = get_target_detail_urls(keyword=keyword_to_search, max_pages=9)

    # 保存
    file_name = f"data/detail_url.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)

    print(f"\n任务完成！共计 {len(final_results)} 个链接已保存至: {file_name}")
