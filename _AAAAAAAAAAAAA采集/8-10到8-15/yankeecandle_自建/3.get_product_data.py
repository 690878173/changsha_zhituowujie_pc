import json
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
# js数据
js_path = Tool.File.path_add_site('hc/3_js.json')
# 测试数据条数 (None = 全部抓取)
ts_num = None


input_url_no_ls = []
output_url_no_ls = []

fieldnames = None
# fieldnames = [
#     "Type", "SKU", "Name", "Description", "Sale price", "Regular price",
#     "Categories", "Tags", "Images", "Parent",
#     "Attribute 1 name", "Attribute 1 value(s)", "brand", "Attribute 2 name", "Attribute 2 value(s)",
# ]


class _T:
    def __init__(self,url,category,res_text):

        self.url:str = url
        self.category = category
        self.res_text = res_text
        self.typ = 'simple'
        self.html = etree.HTML(res_text)
        self.save_html()
        # self._init()

    def _init(self):
        try:
            html = self.html
            js_code_str = html.xpath('//script[@id="mobify-data"]//text()')[0]
            data = json.loads(js_code_str)
            data = data['__PRELOADED_STATE__']["__reactQuery"]["queries"]
            Tool.File.save_json(data,js_path)

            s = data[-2]["state"]['data']['c_shortName']
        except Exception as e:
            Tool.print(f'解析js失败:{e}')

    def save_html(self):
        Tool.HTML.save(self.res_text)
        pass

    def get_main_name(self,html):
        try:
            return self.url.split('/')[-2].replace('.html','')
        except Exception as e:
            Tool.print(f'获取主名称失败:{e}')

    def get_main_price(self,html):
        try:
            r =  html.xpath('//p[@aria-label="price"]//text()')
            return Tool.clean_price(''.join(r))
        except Exception as e:
            Tool.print(f'获取价格失败:{e}')

    def get_main_sku(self,html):
        try:
            return self.url.split('/')[-1].replace('.html','')
        except Exception as e:
            Tool.print(f'获取sku失败:{e}')

    def get_main_desc(self,html):
        try:
            desc = html.xpath('//p[@aria-label="Product Description"]')[0]
            return desc
        except Exception as e:
            Tool.print(f'获取描述失败:{e}，{self.url}')

    def get_main_imgs(self,html):
        try:
            ls = html.xpath('//img[@class="chakra-image css-6jrdpz"]/@src')[:3]

            return [Tool.URL.add_site(i) for i in ls]
        except Exception as e:
            Tool.print(f'获取图片出错:{e}')

    def check_cob(self,html):
        return False

    def get_att(self,html):
        try:
            sty = html.xpath('//p[@class="chakra-text css-1al38q0"]//span//text()')
            if sty[0] == 'Style:':
                sty = ''.join(sty[-1]).strip()
                dic = {'Style':sty}
                print(dic)
                return dic
            return {}
        except Exception as e:
            Tool.print(f'获取属性失败:{e}')
            return {}

    def get_cobs(self,html):
        cobs = []
        s_ls = []
        for _ in s_ls:
            # TODO 进行append填充
            cob_imgs_ls = []
            cob_name = None
            cob_price = None
            cob_desc = None
            cob_sku = None
            cob_att = {}

            # NOTE==============================
            cob_desc = Tool.HTML.clean_product_desc(cob_desc)
            cob_price = Tool.clean_price(cob_price)
            cob_imgs = Tool.Product.clean_imgs(cob_imgs_ls)
            cob = Tool.Product.Variation(
                url=self.url, cat=self.category, imgs=cob_imgs,
                name=cob_name, desc=cob_desc, price=cob_price,
                sku=cob_sku, att=cob_att
            )
            cobs.append(cob)

        return cobs


    def run(self):

        main_name = self.get_main_name(self.html)
        main_price = self.get_main_price(self.html)
        main_sku = self.get_main_sku(self.html)
        main_desc = self.get_main_desc(self.html)
        main_imgs_ls = self.get_main_imgs(self.html)
        main_att = self.get_att(self.html)


        main_desc = Tool.HTML.clean_product_desc(main_desc)
        main_price = Tool.clean_price(main_price)
        main_img = Tool.Product.clean_imgs(main_imgs_ls)

        if self.check_cob(self.html):
            self.typ = 'variation'


        if self.typ == 'simple':
            product = Tool.Product.Simple(
                url=self.url, cat=self.category, imgs=main_img,
                name=main_name, sku=main_sku, price=main_price,
                desc=main_desc, **main_att
            )
            return [product]

        return self.get_cobs(self.html)



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
                        _t = _T(url,category,res_text)
                        data = _t.run()
                        if not isinstance(data,list):
                            Tool.print(f'解析产生数据非列表:{url}')
                        else:
                            ls = []
                            for i in data:
                                if isinstance(i,Tool.Product.variation) or isinstance(i,Tool.Product.simple):
                                    ls.append(i.to_dic())
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
