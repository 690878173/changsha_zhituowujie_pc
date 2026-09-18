import csv
import json
import os
import threading
from queue import Queue
from lxml import etree

from config import Tool

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site("data/result.csv")
fail_file = Tool.File.path_add_site("data/fail.json")
catch_path = Tool.File.path_add_site('hc/3.json')
# 输出带url地址的res文件
output_ts_file = Tool.File.path_add_site('hc/result_ts.csv')

# 测试数据条数 (None = 全部抓取)
ts_num = None


input_url_no_ls = []
output_url_no_ls = []


# 品牌名称
BRAND_NAME = Tool.site



fieldnames = [
    "Type", "SKU", "Name", "Description", "Sale price", "Regular price",
    "Categories", "Tags", "Images", "Parent",
    "Attribute 1 name", "Attribute 1 value(s)", "brand", "Attribute 2 name", "Attribute 2 value(s)",
    "Stock", "is_upload", "Product InformationProduct Information (product.metafields.c_f.zdy_tabs1)"
]



def get_detail_page(url, category, res_text) -> list[dict]:
    """站点解析（模板，按实际页面结构重写）"""
    html = etree.HTML(res_text)

    Tool.HTML.save(res_text)

    if url == 'https://www.hatch.co/accessories/powercords/restore-2':
        name = html.xpath('.//h1[@class="style-module__509fTa__overviewHeading hatch-type-title-medium"]/text()')[0]
        price = ''.join(
            html.xpath('//span[@itemprop="price"]')[0]
        )
        desc_node = html.xpath('//p[@class="style-module__509fTa__overviewDescription hatch-type-paragraph-medium"]')[0]
        desc = Tool.HTML.clean_product_desc(desc_node)
        price = Tool.clean_price(price)
        imgs = html.xpath('.//div[@class="style-module__DwQZKW__featuredImageBlock"]//img/@src')
        imgs = [Tool.URL.add_site(i) for i in imgs]
        sku = url.split('/')[-1]
        ls = []
        ls.append(Tool.Product.Simple(sku=sku,name=name,desc=desc,price=price,imgs=imgs,cat=category,url=url,).to_dic())
        return ls

    # ========== 1. 解析公共字段 ==========
    name = html.xpath('.//h1[@class="style-module__7f1vJG__title hatch-type-title-medium"]/text()')[0]
    desc_node = html.xpath('.//p[@class="style-module__7f1vJG__textDescription hatch-type-paragraph-medium"]')[0]
    desc = Tool.HTML.clean_product_desc(desc_node)


    price = ''.join(
        html.xpath('//span[@class="style-module__7f1vJG__price hatch-type-title-x-small"]//text()'))

    price = Tool.clean_price(price)

    size_nodes = html.xpath('//div[@class="style-module__xUPIPa__variantSelector"]')[0]

    imgs = html.xpath("//div[@class='style-module__IIsoOa__featuredItem']//img/@src")
    imgs = [Tool.URL.add_site(i) for i in imgs]

    size_name = size_nodes.xpath('./span/text()')[0]





    other_size_url = size_nodes.xpath('./ul/li/a/@href')
    _sku_houzhui = len(other_size_url)

    cobs = [
        Tool.Product.Variation(name=name,
                               sku=f'{name}_{size_name}',
                               desc=desc, price=price, imgs=imgs, cat=category, url=url,
                               brand=Tool.site, att={'Color': size_name}, parent=f'{name}_{_sku_houzhui}')
    ]

    for _url in other_size_url:
        _url = Tool.URL.add_site(_url)
        res = Tool.get(_url)
        html = etree.HTML(res.text)
        _desc_node = html.xpath('.//p[@class="style-module__7f1vJG__textDescription hatch-type-paragraph-medium"]')[0]
        _desc = Tool.HTML.clean_product_desc(_desc_node)

        _price = ''.join(
            html.xpath('//span[@class="style-module__7f1vJG__price hatch-type-title-x-small"]//text()'))

        _price = Tool.clean_price(_price)

        _size_nodes = html.xpath('//div[@class="style-module__xUPIPa__variantSelector"]')[0]

        _imgs = html.xpath("//div[@class='style-module__IIsoOa__featuredItem']//img/@src")
        _imgs = [Tool.URL.add_site(i) for i in _imgs]
        _size_name = _size_nodes.xpath('./span/text()')[0]
        _cob = Tool.Product.Variation(name=name, sku=f'{name}_{_size_name}', desc=_desc, price=_price, imgs=_imgs, cat=category, url=_url, brand=Tool.site, att={'Color':_size_name}, parent=f'{name}_{_sku_houzhui}')

        cobs.append(_cob)
    return [cob.to_dic() for cob in cobs]


class Crawler:
    def __init__(self, max_threads=10):
        self.input_file = input_file
        self.fail_file = fail_file
        self.max_threads = max_threads

        self.task_queue = Queue()
        self.result_queue = Queue()
        self.failures = {}
        self.total_tasks = 0
        self.catch_data_len = 0
        self.lock = threading.Lock()

    def load_tasks(self):
        data = Tool.File.load_json(self.input_file)
        seq_id = 0
        for category, urls in data.items():
            for url in urls:
                if url in input_url_no_ls:
                    continue
                self.task_queue.put((str(seq_id), category, url))
                seq_id += 1
                if isinstance(ts_num, int) and seq_id >= ts_num:
                    Tool.print(f'启动测试条数:{ts_num}')
                    self.total_tasks = seq_id
                    return
        self.total_tasks = seq_id

    def request_worker(self, catch_data):
        while True:
            try:
                seq_id, category, url = self.task_queue.get_nowait()
            except Exception:
                break
            if str(seq_id) in catch_data and catch_data[str(seq_id)]:
                continue

            data = []
            error_type = None

            try:
                res = Tool.get(url)
                if not res:
                    error_type = "请求失败"
                    self.failures.setdefault(category, []).append(url)
                else:
                    res_text = res.text
                    try:
                        data = get_detail_page(url, category, res_text)
                        if not isinstance(data,list):
                            Tool.print(f'解析数据不是字典')
                            exit()
                    except Exception as e:
                        error_type = "解析失败"
                        Tool.print(e)
                        self.failures.setdefault(category, []).append(url)

                self.result_queue.put((seq_id, data))

            except Exception as e:
                error_type = f"任务崩溃 ({e})"
                self.failures.setdefault(category, []).append(url)
                self.result_queue.put((seq_id, []))

            finally:
                with self.lock:
                    self.catch_data_len += 1
                    current = self.catch_data_len
                    total = self.total_tasks
                    if error_type:
                        print(f"[FAILED] {error_type} {current}/{total}: {url}")
                    else:
                        print(f"[PROGRESS] 已完成 {current}/{total}")

    def writer_worker(self, catch_data):
        _num = 0
        while True:
            item = self.result_queue.get()
            if item is None:
                break

            seq_id, rows = item
            catch_data[seq_id] = rows

            _num += 1
            if _num == 20:
                _num = 0
                Tool.File.save_json(catch_data, catch_path)

            self.result_queue.task_done()

        Tool.File.save_json(catch_data, catch_path)

    def run(self):
        self.load_tasks()

        catch_data = Tool.File.load_json(catch_path)
        self.catch_data_len = len(catch_data)
        if self.catch_data_len >0:
            Tool.print(f'加载缓存，已存在数据{self.catch_data_len}条')

        writer_thread = threading.Thread(target=self.writer_worker, args=(catch_data,))
        writer_thread.start()

        threads = []
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.request_worker, args=(catch_data,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.result_queue.put(None)
        writer_thread.join()

        catch_data = Tool.File.load_json(catch_path)
        catch_data = Tool.sort_data(catch_data)

        def iter_catch_data(_catch_data):
            for _rows in _catch_data.values():
                if _rows:
                    yield from _rows

        # with open(output_ts_file, "w", newline="", encoding="utf-8") as f:
        #     writer = csv.DictWriter(f, fieldnames=fieldnames + ['url'])
        #     writer.writeheader()
        #     writer.writerows(iter_catch_data(catch_data))
        print(catch_data)
        bf = Tool.json_del_url(catch_data)
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(iter_catch_data(bf))

        Tool.File.save_json(self.failures, fail_file)


def main():
    crawler = Crawler(max_threads=5)
    crawler.run()


if __name__ == '__main__':
    main()
