import time

import requests
import urllib3
from lxml import etree
from base_f import Tool,zs


file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')

# 测试数据条数
ts_num = None


# 排除某些 URL
no_url_ls = ['https://javvycoffee.com/products/javvy-x-comfrt-hoodie']


@zs('获取详细链接列表')
def get_detail_url(url):
    self = Tool
    res = self.get(url)
    html = etree.HTML(res.text)

    product_url = html.xpath(
        '//div[@class="product-card on--collection-page"]/a[@class="product__visuals-wrapper"]/@href')
    detail_links = [self.base_url + i for i in product_url]
    return detail_links

def parse_ml_json(file_path=file_path ,flush=False):
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
                detail_urls = get_detail_url(url)
                if detail_urls:
                    # 保持顺序扩展结果
                    detail_urls = [i for i in detail_urls if i not in no_url_ls]
                    result[name].extend(detail_urls)
                    print(f"  成功获取到 {len(detail_urls)} 条详情页链接")
                else:
                    print(f"  URL: {url} 未获取到数据 (可能是 API 结构不同)")
            except Exception as e:
                print(f"  URL: {url} 处理中途中断: {e}")


    self.save_json(result, save_path)

    total_count = sum(len(v) for v in result.values())
    print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 {save_path}")

def main():
    parse_ml_json()

if __name__ == '__main__':
    main()