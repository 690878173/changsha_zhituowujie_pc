import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lxml import etree
from config import Tool
zs = Tool.zs

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2.json')

# 测试数据条数,以初始url数量计数
ts_num = None

# 排除某些 URL
no_url_ls = []

# 覆盖缓存
flush = False


cookies = {
    'lume-optimizely': 'f6511bf2-1da1-40d3-aa14-aa482a2c7adb',
    '_shopify_y': 'cf718687-A6E0-47E6-4786-C3EC429758E0',
    '_gcl_au': '1.1.1779159082.1785891750',
    '_ga': 'GA1.1.164619440.1785891750',
    '__ps_r': '_',
    '__ps_lu': 'https://lumedeodorant.com/',
    '__ps_did': 'pscrb_1cf932f1-d17f-4790-bed6-b20a40f2fce5',
    '__ps_fva': '1785891750751',
    'ugc_vid_13a32e02-f650-4e26-9661-45e56571123b': '1fbcc91d-3b93-4afb-835f-1cccaf2c9cc0',
    'FPID': 'FPID2.2.AOa0QqUrIV0IpqKtH8CkfmiN%2FsmllCWKUtYyvtUkTA4%3D.1785891750',
    'octane%2Fv2%2Flast_assistant_quiz_id': '',
    'octane%2Fshopify%2Fuid': '6b41879d6e4cf80319a3aa30410ced9f0e80d312269cefa98622f52a160978b41b25560455d27f96568c24d21369ca0dce466b64ae813e98cfff4481',
    'tatari-session-cookie': '8126809f-b324-d55b-7641-2f55c8e368d5',
    '_ga_DUMMY': 'GS2.1.s1785981697$o7$g0$t1785981697$j60$l0$h1662940293',
    '__cf_bm': 'nq9jbFGxM1uC65LYn2QdmaswhP8Y.hOZLa0V9OyU3sY-1788312658.659176-1.0.1.1-RBSMLuLJ7qRFJUTH7GGPal4zDgECmtnDP2xVVnWhyo69cbICwREcvSbCr7J3fokBExIgzgqDZmJ0ptVQXA0MnQ6lcLc5VxxB7auwsJfc2FMZQac9Vaup9ykyhFGmQoPP',
    '_shopify_s': '5fbdae9d-A75B-4ED6-B0F0-CC443EB82AE8',
    'bpm_fpc': '2f298ed2-9293-4919-a4cb-c3eff1eefd72',
    '__kla_id': 'eyJjaWQiOiJaRGMwTmpsbU1qZ3RNVFkzTlMwME0yVmpMVGd4TTJVdE5HTmlZMlEzTlRRNFpURXoifQ==',
    '__ps_sr': '_',
    '__ps_slu': 'https://lumedeodorant.com/collections/unscented',
    '__obref': '899f6fd4-49e3-4b69-892c-cb8ab3e7604c',
    '_tracking_consent': '3AMPS._USCA_f_f_2NpoNTtHSQ6-6O0gWgEiwA',
    '_dd_s': 'aid=3c12fb92-905d-4c93-a21e-96b95b29830b&logs=1&id=ab7553c9-567c-4e1a-b69e-cc1d6c75df49&created=1788312659433&expire=1788313871989&rum=2',
    'tatari-cookie-test': '45913163',
    '_ga_7D70598JLZ': 'GS2.1.s1788312663$o9$g1$t1788312973$j58$l0$h738288162',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'lume-optimizely=f6511bf2-1da1-40d3-aa14-aa482a2c7adb; _shopify_y=cf718687-A6E0-47E6-4786-C3EC429758E0; _gcl_au=1.1.1779159082.1785891750; _ga=GA1.1.164619440.1785891750; __ps_r=_; __ps_lu=https://lumedeodorant.com/; __ps_did=pscrb_1cf932f1-d17f-4790-bed6-b20a40f2fce5; __ps_fva=1785891750751; ugc_vid_13a32e02-f650-4e26-9661-45e56571123b=1fbcc91d-3b93-4afb-835f-1cccaf2c9cc0; FPID=FPID2.2.AOa0QqUrIV0IpqKtH8CkfmiN%2FsmllCWKUtYyvtUkTA4%3D.1785891750; octane%2Fv2%2Flast_assistant_quiz_id=; octane%2Fshopify%2Fuid=6b41879d6e4cf80319a3aa30410ced9f0e80d312269cefa98622f52a160978b41b25560455d27f96568c24d21369ca0dce466b64ae813e98cfff4481; tatari-session-cookie=8126809f-b324-d55b-7641-2f55c8e368d5; _ga_DUMMY=GS2.1.s1785981697$o7$g0$t1785981697$j60$l0$h1662940293; __cf_bm=nq9jbFGxM1uC65LYn2QdmaswhP8Y.hOZLa0V9OyU3sY-1788312658.659176-1.0.1.1-RBSMLuLJ7qRFJUTH7GGPal4zDgECmtnDP2xVVnWhyo69cbICwREcvSbCr7J3fokBExIgzgqDZmJ0ptVQXA0MnQ6lcLc5VxxB7auwsJfc2FMZQac9Vaup9ykyhFGmQoPP; _shopify_s=5fbdae9d-A75B-4ED6-B0F0-CC443EB82AE8; bpm_fpc=2f298ed2-9293-4919-a4cb-c3eff1eefd72; __kla_id=eyJjaWQiOiJaRGMwTmpsbU1qZ3RNVFkzTlMwME0yVmpMVGd4TTJVdE5HTmlZMlEzTlRRNFpURXoifQ==; __ps_sr=_; __ps_slu=https://lumedeodorant.com/collections/unscented; __obref=899f6fd4-49e3-4b69-892c-cb8ab3e7604c; _tracking_consent=3AMPS._USCA_f_f_2NpoNTtHSQ6-6O0gWgEiwA; _dd_s=aid=3c12fb92-905d-4c93-a21e-96b95b29830b&logs=1&id=ab7553c9-567c-4e1a-b69e-cc1d6c75df49&created=1788312659433&expire=1788313871989&rum=2; tatari-cookie-test=45913163; _ga_7D70598JLZ=GS2.1.s1788312663$o9$g1$t1788312973$j58$l0$h738288162',
}


@zs('lumedeodorant: 集合页无分页，section.grid 内取 /products/ 链接')
def get_detail_url(url, par):
    is_next = False
    res = Tool.get(url,headers=headers,cookies=cookies)
    html = etree.HTML(res.text)
    # Tool.HTML.save(res.text)

    # 需要挂梯子才能访问

    # 从商品网格容器中提取产品链接
    product_links = html.xpath(
        '//section[contains(@class,"grid grid-cols-2")]'
        '//a[contains(@href,"/products/") and not(contains(@href,"/collections/"))]/@href'
    )


    # 去重并补全URL
    detail_links = []
    seen = set()
    for link in product_links:
        if link not in seen:
            seen.add(link)
            detail_links.append(Tool.URL.add_site(link))
        else:
            Tool.print(f'重复url:{url}')

    return detail_links, is_next


def get_detail_all_url(url):
    ls = []
    par = {}
    _num = 1
    while True:
        res_ls, is_next = get_detail_url(url, par=par)

        ls.extend(res_ls)
        if not is_next:
            break
        url = par['next_url']
        _num += 1
        if _num > 100:
            Tool.print(f'页数超过100,当前{_num},检查是否异常', color='yellow')
    return ls


def parse_ml_json(file_path=file_path, flush=False):
    self = Tool

    data = self.File.load_json(save_path)

    url_dict = self.File.load_json(file_path)

    result = data

    num = 0
    for name, url_data in url_dict.items():
        if not flush:
            if name in data and data.get(name, False):
                print(f"跳过分类：{name}，因为该分类已存在数据")
                continue
        print(f"\n====== 正在处理分类：{name} ======")
        result[name] = []
        if isinstance(url_data, str):
            url_list = [url_data]
        else:
            url_list = url_data

        for url in url_list:
            # 跳过非商品集合页面（放在计数之前）
            if not any(kw in url for kw in ['/collections/', '/shop', '/discovery-sets']):
                print(f"  跳过非集合URL: {url}")
                continue

            if isinstance(ts_num, int) and num >= ts_num:
                print(f"已处理 {num} 条数据，已超出限制，任务结束")
                break
            num += 1

            try:
                print(f"正在分析 URL: {url}")
                detail_urls = get_detail_all_url(url)
                if detail_urls:
                    detail_urls = [i for i in detail_urls if i not in no_url_ls]
                    before_count = len(result[name])
                    result[name].extend(detail_urls)
                    result[name] = list(dict.fromkeys(result[name]))
                    after_count = len(result[name])
                    dup_count = before_count + len(detail_urls) - after_count
                    if dup_count > 0:
                        print(f"  [去重] 分类 [{name}] 本次移除了 {dup_count} 条重复URL")
                    print(f"  成功获取到 {len(detail_urls)} 条详情页链接")
                else:
                    print(f"  URL: {url} 未获取到数据 (可能是 API 结构不同)")
            except Exception as e:
                print(f"  URL: {url} 处理中途中断: {e}")

    self.File.save_json(result, save_path)

    total_count = sum(len(v) for v in result.values())
    print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 {save_path}")


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
        print(f"\n====== 正在处理分类：{name} =====")
        url_str = url_data if isinstance(url_data, str) else url_data
        print(f"目标集合: {url_str}")

        result[name] = []
        if isinstance(url_data, str):
            url_list = [url_data]
        else:
            url_list = url_data

        for url in url_list:
            # 跳过非商品集合页面（放在计数之前）
            if not any(kw in url for kw in ['/collections/', '/shop', '/discovery-sets']):
                print(f"  跳过非集合URL: {url}")
                continue

            if isinstance(ts_num, int) and num >= ts_num:
                print(f"已处理 {num} 条数据，已超出限制，任务结束")
                break
            num += 1

            try:
                print(f"正在分析 URL: {url}")
                detail_urls = get_detail_all_url(url)
                if detail_urls:
                    detail_urls = [i for i in detail_urls if i not in no_url_ls]
                    before_count = len(result[name])
                    result[name].extend(detail_urls)
                    result[name] = list(dict.fromkeys(result[name]))
                    after_count = len(result[name])
                    dup_count = before_count + len(detail_urls) - after_count
                    if dup_count > 0:
                        print(f"  [去重] 分类 [{name}] 本次移除了 {dup_count} 条重复URL")
                    print(f"  成功获取到 {len(detail_urls)} 条详情页链接")
                else:
                    print(f"  URL: {url} 未获取到数据 (可能是 API 结构不同)")
            except Exception as e:
                print(f"  URL: {url} 处理中途中断: {e}")

        Tool.File.save_json(result, save_path)
        Tool.File.save_json(result, catch_path)

    total_count = sum(len(v) for v in result.values())
    print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 {save_path}")


if __name__ == '__main__':
    main()
