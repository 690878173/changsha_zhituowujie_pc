import csv
import json
import os
import threading
from queue import Queue

from lxml import etree

from base_f import Tool,images_split,ProductSimple,ProductVariation

# 测试数据条数 (None = 全部抓取)
ts_num = None
# 重新运行需要删除缓存文件

# 品牌名称 (根据站点修改)
BRAND_NAME = "javvycoffee"

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file=Tool.File.path_add_site("data/result.csv")
fail_file=Tool.File.path_add_site("data/fail.json")
catch_path = Tool.File.path_add_site('data/_hc.json')

output_ts_file = Tool.File.path_add_site('data/result_te.csv')

fieldnames = [
            "Type", "SKU", "Name", "Description", "Sale price", "Regular price",
            "Categories", "Tags", "Images", "Parent",
            "Attribute 1 name", "Attribute 1 value(s)", "brand", "Attribute 2 name", "Attribute 2 value(s)",
            "Stock", "is_upload", "Product InformationProduct Information (product.metafields.c_f.zdy_tabs1)"
        ]

'''
desc:保留html结构
price:去除价格符号后缀



'''
def get_detail_page(url, category, res_text):
    res_ls = []
    html = etree.HTML(res_text)
    name = url.split('/')[-1].replace('-', ' ').upper()
    desc = etree.tostring(html.xpath('//div[@class="pdp-tabs-content w-tab-content"]')[0], encoding='unicode')
    price = ''.join(
        html.xpath('//div[@class="frequency-heading one-time"]//div[@class="frequency-prices_inner"]//text()'))
    if not price:
        price = ''.join(html.xpath('//p[@class="p-16 c-dark _w-700"]/text()'))
    if not price:
        price = ''.join(html.xpath('//span[@class="p-16 c-dark _w-700"]/text()'))
    # ig_node = html.xpath('//div[@class="product-section__visuals"]//img/@src')[:-1]
    # img_url = [i.split('?')[0] for i in ig_node]
    main_img = html.xpath('//div[@class="product-featured-image"]//img/@src')[0]
    slider_img = html.xpath('//div[@class="product-images-slider"]//img/@src')
    main_other_img = html.xpath('//div[@class="product-thumb"]//img/@src')
    # print(name)
    # print(desc)
    # print(price)
    # print(main_img)
    # print(slider_img)
    # print(main_other_img)
    image_ls = []
    for i in [main_img] + main_other_img:
        if i.startswith('http'):
            image_ls.append(i)
        else:
            print('无效域名')
    image_list_str = images_split.join(image_ls)

    price = Tool.clean_price(price)





    size = html.xpath('//div[@class="pdp-size-picker"]')
    color = []

    sku = url.split('/')[-1]

    WARN_RED = "\033[91m"
    END = "\033[0m"

    if not price:
        print(f"{WARN_RED}====================================={END}")
        print(f"{WARN_RED}【价格缺失】URL: {url}{END}")
        print(f"{WARN_RED}====================================={END}")
    if not desc:
        print(f"{WARN_RED}====================================={END}")
        print(f"{WARN_RED}【描述缺失】URL: {url}{END}")
        print(f"{WARN_RED}====================================={END}")

    if not size and not color:
        Type = "simple"
        dt : ProductSimple = {
            "Type": Type,
            "SKU": sku,
            "Name": name,
            "Description": desc,  # 如果没找到，此处为 ""
            "Sale price": price,
            "Regular price": price,
            "Categories": category,
            "Tags": "",
            "Images": image_list_str,
            "Parent": "",
            "brand": BRAND_NAME,
            "Stock": 1000.00,
            "is_upload": 0,
            'url': url
        }
        res_ls.append(dt)
    else:
        Type = 'variation'
        if not color:
            color = ['']
        if not size:
            size = ['']
        for s in size:
            for c in color:

                dt:ProductVariation = {
                    "Type": Type,
                    "SKU": sku,
                    "Name": name,
                    "Description": desc,  # 如果没找到，此处为 ""
                    # 如果没找到，此处为 ""
                    "Sale price": price,
                    "Regular price": price,
                    "Attribute 1 name": "size",
                    "Attribute 1 value(s)": s,
                    "Attribute 2 name": "color",
                    "Attribute 2 value(s)": c,
                    "Categories": category,
                    "Tags": "",
                    "Images": image_list_str,
                    "Parent": "",
                    "brand": BRAND_NAME,
                    "Stock": 1000.00,
                    "is_upload": 0,
                    'url': url
                }
                res_ls.append(dt)
    return res_ls

class Crawler:
    def __init__(self, proxies=None,
                 max_threads=10, max_retries=3, batch_size=100, use_proxy=True):
        self.input_file = input_file
        self.output_file = output_file
        self.fail_file = fail_file
        self.proxies = proxies if proxies else []
        self.max_threads = max_threads
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.use_proxy = use_proxy

        self.task_queue = Queue()
        self.result_queue = Queue()
        self.failures = {}
        self.total_tasks = 0
        self.completed_tasks = 0
        self.lock = threading.Lock()

        self.headers = {}
        self.cookies = {}

    def load_tasks(self):
        data = Tool.File.load_json(self.input_file)

        self.total_tasks = sum(len(urls) for urls in data.values())

        seq_id = 0
        for category, urls in data.items():
            for url in urls:
                # 将 seq_id 一并放入队列: (0, cat, url), (1, cat, url)...
                self.task_queue.put((seq_id, category, url))
                seq_id += 1
                if isinstance(ts_num, int) and seq_id >= ts_num:
                    break

    def worker(self,buffer):
        while True:
            try:
                seq_id, category, url = self.task_queue.get_nowait()
            except Exception:
                break
            if str(seq_id) in buffer and buffer[str(seq_id)]:
                # print(f"任务 {seq_id} 已存在，跳过")
                continue


            rows_to_write = []
            error_type = None  # 用于标记失败原因，None 表示成功

            try:
                res = Tool.get(url)
                if not res:
                    error_type = "请求失败"
                    self.failures.setdefault(category, []).append(url)

                else:
                    res_text = res.text
                    try:
                        data = get_detail_page(url, category, res_text)
                        rows_to_write =data
                    except Exception as e:
                        error_type = "关键字段为空"
                        print(e)
                        self.failures.setdefault(category, []).append(url)

                self.result_queue.put((seq_id, rows_to_write))

            except Exception as e:
                # ---------------- 崩溃捕获 ----------------
                error_type = f"任务崩溃 ({e})"
                self.failures.setdefault(category, []).append(url)
                # 发送空结果占位
                self.result_queue.put((seq_id, []))

            finally:
                # ---------------- 统一打印进度 ----------------
                with self.lock:
                    self.completed_tasks += 1
                    current = self.completed_tasks
                    total = self.total_tasks

                    if error_type:
                        print(f"[FAILED] {error_type} {current}/{total}: {url}")
                    else:
                        print(f"[PROGRESS] 已完成 {current}/{total}")

    def writer_worker(self, fieldnames,output_file):
        """
        Writer 负责重组顺序
        """
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            next_seq_to_write = 0  # 当前正在等待写入的序号 (0, 1, 2...)
            buffer = {}  # 缓冲区: { 序号: [数据行] }

            while True:
                item = self.result_queue.get()

                if item is None:  # 结束信号
                    break

                seq_id, rows = item

                # 1. 把拿到的数据存入缓冲区
                buffer[seq_id] = rows

                # 2. 检查缓冲区里有没有我们正在等待的那个序号 (next_seq_to_write)
                #    如果 0 号还没来，buffer 里有了 1 号，这里会循环等待，直到 0 号来了
                while next_seq_to_write in buffer:
                    current_rows = buffer.pop(next_seq_to_write)

                    if current_rows:  # 如果列表不为空（即没有失败）
                        writer.writerows(current_rows)

                    # 只有写入了当前序号（或者确认当前序号是空失败任务），才把指针 +1
                    next_seq_to_write += 1

                self.result_queue.task_done()

    def my_writer_worker(self, fieldnames,catch_path):
        if os.path.exists(catch_path):
            with open(catch_path, "r", newline="", encoding="utf-8") as f:
                buffer = json.load(f)
        else:
            buffer = {}

        num = 0
        while True:
            item = self.result_queue.get()

            if item is None:  # 结束信号
                break

            seq_id, rows = item
            buffer[str(seq_id)] = rows
            num += 1
            if num == 20:
                num = 0
                Tool.File.save_json(buffer, catch_path)

            self.result_queue.task_done()

    def run(self):
        self.load_tasks()
        if not os.path.exists(catch_path):
            Tool.File.save_json({}, catch_path)
        buffer = Tool.File.load_json(catch_path)
        self.completed_tasks = len(buffer)
        writer_thread = threading.Thread(target=self.my_writer_worker, args=(fieldnames,catch_path))
        writer_thread.start()

        threads = []
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.worker,args=(buffer,))
            t.start()
            threads.append(t)

        # 等待所有爬虫任务完成
        for t in threads:
            t.join()

        self.result_queue.put(None)
        writer_thread.join()

        buffer = Tool.File.load_json(catch_path)
        buffer = Tool.sort_data(buffer)

        with open(output_ts_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames+['url'])
            writer.writeheader()
            for rows in buffer.values():
                writer.writerows(rows)
        bf = Tool.json_del_url(buffer)
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rows in bf.values():
                writer.writerows(rows)

        # 写入失败文件
        Tool.File.save_json(self.failures, fail_file)


def main():
    crawler = Crawler(max_threads=5, max_retries=3, batch_size=100)
    crawler.run()

if __name__ == '__main__':
    main()