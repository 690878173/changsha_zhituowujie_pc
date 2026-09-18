import re
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


fieldnames = [
    "Type", "SKU", "Name", "Description", "Sale price", "Regular price",
    "Categories", "Tags", "Images", "Parent",
    "Attribute 1 name", "Attribute 1 value(s)", "brand", "Attribute 2 name", "Attribute 2 value(s)",
]
def get_detail_page(url, category, res_text) -> list[dict]:
    page_tree = etree.HTML(res_text)

    name = page_tree.xpath(
        '//h1[@class="tw:order-2 tw:mb-1 tw:mt-2 tw:text-left tw:font-body tw:text-2xl tw:font-extrabold tw:uppercase tw:leading-[26px] tw:text-body tw:lg:order-1 tw:lg:mb-3 tw:lg:mt-0"]/text()'
    )[0].strip()

    if not name:
        Tool.print('[ERROR] 该页面为非商品页,缺失商品名字')
        return

    price = None
    line_through_prices = page_tree.xpath(
        '//b[contains(@class,"line-through")]/text()'
    )
    if line_through_prices:
        price = line_through_prices[0].strip().replace('$', '').replace(',', '')

    else:
        all_prices = page_tree.xpath(
            '//span[contains(@class,"product-price")]/text() | '
            '//b[contains(@class,"line-through")]/text()'
        )
        if all_prices:
            prices = []
            for p in all_prices:
                try:
                    val = float(p.strip().replace('$', '').replace(',', ''))
                    prices.append(val)
                except:
                    pass
            if prices:
                price = max(prices)

    if not price:
        Tool.print('[ERROR] 该页面为非商品页,缺失商品价格')
        return

    price = Tool.clean_price(price)

    description = ''
    try:
        desc_nodes = page_tree.xpath(
            '//div[@class="tw:mx-auto tw:grid tw:w-full tw:max-w-[600px] tw:grid-cols-2 tw:justify-center tw:gap-5 tw:lg:max-w-[1225px] tw:lg:justify-between tw:lg:grid-cols-4"] | '
            '//div[@class="tw:text-sm tw:font-light tw:text-body tw:md:text-base tw:[&_*]:text-sm tw:[&_*]:md:!text-base tw:[&_b]:font-bold tw:[&_p]:mb-3"]'
        )
        if desc_nodes:
            return etree.tostring(desc_nodes[0]).decode().strip()

        desc_nodes = page_tree.xpath(
            '//div[@class="tw:mx-auto tw:grid tw:w-full tw:max-w-[600px] tw:grid-cols-2 tw:justify-center tw:gap-5 tw:lg:max-w-[1225px] tw:lg:justify-between tw:lg:grid-cols-3"] | '
            '//div[@class="tw:mx-auto tw:grid tw:w-full tw:max-w-[600px] tw:grid-cols-2 tw:justify-center tw:gap-5 tw:lg:max-w-[1225px] tw:lg:justify-between tw:lg:grid-cols-2"]'
        )
        if desc_nodes:
            return etree.tostring(desc_nodes[0]).decode().strip()

        meta = page_tree.xpath('//meta[@name="description"]/@content')
        if meta:
            description = meta[0]
    except Exception as e:
        print(f'[ERROR] 该产品缺失描述')
    try:
        node = page_tree.xpath('//div[@class="tw:relative tw:mx-auto tw:lg:mr-0 tw:lg:px-9 tw:max-w-md"]//div[@class="markdown"]')[0]
        short_description = etree.tostring(node).decode('utf-8')
    except Exception as e:
        short_description = ''

    try:
        containers = page_tree.xpath(
            '//div[@class="tw:animate-[fadeInLeftFull_0.8s] tw:md:min-h-[200px] tw:lg:min-h-[270px]"]')
        details = ''.join(etree.tostring(d).decode('utf-8') for d in containers)
    except Exception:
        details = ''

    image_url_list = []
    try:
        image_container = page_tree.xpath(
            '//div[@class="tw:relative tw:flex tw:justify-center tw:overflow-hidden tw:cursor-zoom-in tw:bg-position-50-50 tw:hover:bg-no-repeat tw:hover:[background-image:var(--bg-image)] tw:max-w-[600px] tw:max-h-[600px]"]/img/@src'
        )
        for image in image_container:
            if image:
                image = image.strip()
                match = re.search(r'(/i/items/[^,\s"\'<>]+?\.(?:jpg|jpeg|png|webp))', image, re.I)
                if match:
                    image_url = "https://static.rticoutdoors.com" + match.group(1)
                if image.startswith("//"):
                    image_url = "https:" + image
                if image.startswith("/"):
                    image_url = "https://static.rticoutdoors.com" + image
                else:
                    image_url = image
            else:
                image_url = ''
            if image_url and image_url not in image_url_list:
                image_url_list.append(image_url)
    except Exception:
        print('[ERROR] 没有商品图片')
        return

    html = etree.HTML(res_text)

    typ = 'simple'
    main_imgs_ls =
    main_name =
    main_price =
    main_sku =
    main_desc =



    # NOTE==============================
    main_desc = Tool.HTML.clean_product_desc(main_desc)
    main_price = Tool.clean_price(main_price)
    main_img = Tool.Product.clean_imgs(main_imgs_ls)
    if typ == 'simple':
        product = Tool.Product.Simple(
            url=url, cat=category,imgs=main_img,
            name=main_name,sku=main_sku,price=main_price,
            desc=main_desc
        ).to_dic()
        return [product]
    # NOTE==============================


    cobs = []

    s_ls = []

    for _ in s_ls:
        # TODO 进行append填充
        cob_imgs_ls = []
        cob_name =
        cob_price =
        cob_desc =
        cob_sku = None
        cob_att = {}

        # NOTE==============================
        cob_desc = Tool.HTML.clean_product_desc(cob_desc)
        cob_price = Tool.clean_price(cob_price)
        cob_imgs = Tool.Product.clean_imgs(cob_imgs_ls)
        cob = Tool.Product.Variation(
            url=url,cat=category,imgs=cob_imgs,
            name=cob_name,desc=cob_desc,price=cob_price,
            sku=cob_sku,att=cob_att
        ).to_dic()
        cobs.append(cob)
        # NOTE==============================


    return cobs




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
                            Tool.print(f'解析产生数据非列表:{url}')
                        else:
                            ls = []
                            for i in data:
                                if isinstance(i,Tool.Product.Simple) or isinstance(i,Tool.Product.Variation):
                                    ls.append(i.to_data())
                            data = ls


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

        Tool.File.save_csv(list(iter_catch_data(catch_data)), output_ts_file, columns=fieldnames)
        bf = Tool.json_del_url(catch_data)
        Tool.File.save_csv(list(iter_catch_data(bf)), output_file,columns=fieldnames)

        Tool.File.save_json(self.failures, fail_file)

        for _ in range(3):
            Tool.print(f'当前写入文件列名:{fieldnames}')
            Tool.print(f'注意是否写入自定义字段')


def main():
    crawler = Crawler(max_threads=5)
    crawler.run()


if __name__ == '__main__':
    main()
