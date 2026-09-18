from lxml import etree
from config import Tool

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2.json')

# 测试数据条数,以初始url数量计数
ts_num = None

# 排除某些 URL
input_url_no_ls = []
output_url_no_ls = []

# 覆盖缓存
flush = False


@Tool.zs('具体需重写=>获取详细链接，返回列表,下一页码')
def get_detail_url(url, par):
    is_next = False
    products_url = f"{url}?page={par.get('num')}"
    res = Tool.get(products_url)
    html = etree.HTML(res.text)

    products = html.xpath('//a/@href')

    seen = set()
    detail_links = []
    for product in products:
        if not product:
            continue

        # 只要站内商品详情页，排除分类页、功能页、图片、邮件等
        if not product.startswith('/'):
            continue
        if product.startswith(
                ('/shop', '/myrtic', '/cart', '/help', '/about-us', '/authorized-retailers', '/terms',
                 '/privacy', '/accessibility', '/share', '/order', '/_', '/images', '/assets')):
            continue
        if product == '/':
            continue
        if 'design=true' in product:
            continue

        product_url = "https://rticoutdoors.com" + product

        if product_url not in seen:
            seen.add(product_url)
            print(product_url)
            detail_links.append(product_url)

    if len(products) == 48:
        par['num'] += 1
        next_link = url
        # 等待逻辑翻页
        is_next = True
        par['next_url'] = url
    else:
        pass




    return detail_links,is_next


def get_detail_all_url(url):
    ls = []
    par = {'num':1}
    _num = 1
    while True:
        res_ls,is_next = get_detail_url(url, par=par)
        ls.extend(res_ls)
        if not is_next:
            break
        try:
            url = par['next_url']
        except:
            Tool.print(f'par未设置next_url')
        _num += 1
        if _num >20:
            Tool.print(f'页数超过20,当前{_num},检查是否异常',color='yellow')
    return ls


def main():

    data = Tool.File.load_json(catch_path)

    urls_data = Tool.File.load_json(file_path)

    result = data

    num = 0
    for name, url in urls_data.items():
        if not flush:
            if name in data and data.get(name, False):
                Tool.print(f"跳过分类：{name}，因为该分类已存在数据",color='yellow')
                continue
        if url in input_url_no_ls:
            Tool.print(f'跳过分类：{name}，目标url排除',color='yellow')
            continue
        print(f"\n====== 正在处理分类：{name} ======")
        print(f"目标集合: {url.strip()}")

        result[name] = []

        if isinstance(ts_num, int) and num >= ts_num:
            print(f"已处理 {num} 条数据，已超出限制，任务结束")
            break
        num += 1

        try:
            print(f"正在分析 URL: {url}")
            detail_urls = get_detail_all_url(url)
            if detail_urls:
                detail_urls = [i for i in detail_urls if i not in output_url_no_ls]
                before_count = len(result[name])
                result[name].extend(detail_urls)
                result[name] = list(dict.fromkeys(result[name]))
                after_count = len(result[name])
                dup_count = before_count + len(detail_urls) - after_count
                if dup_count > 0:
                    print(f"  [去重] 分类 [{name}] 本次移除了 {dup_count} 条重复URL")
                print(f"  成功获取到 {len(detail_urls)} 条详情页链接")
            else:
                print(f"  get_detail_all_url返回空值，URL: {url} 未获取到数据 (可能是 API 结构不同)")
        except Exception as e:
            print(f"  URL: {url} 处理中途中断: {e}")

        Tool.File.save_json(result, catch_path)

    Tool.File.save_json(result, save_path)
    Tool.File.save_json(result, catch_path)

    total_count = sum(len(v) for v in result.values())
    print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 {save_path}")















if __name__ == '__main__':
    main()