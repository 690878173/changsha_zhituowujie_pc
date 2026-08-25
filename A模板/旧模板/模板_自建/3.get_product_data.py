import threading
from queue import Queue
from lxml import etree

from config import Tool

# 文件路径配置
input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site("res/result.csv")
fail_file = Tool.File.path_add_site('fail/3.json')
catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
# 携带原始url输出文件
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

# 测试数据条数 (None = 全部抓取)
ts_num = None

# URL黑名单
input_url_no_ls = []
output_url_no_ls = []

# CSV输出表头
fieldnames = None


class _T:
    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.typ = 'simple'
        self.html = etree.HTML(res_text)

    def get_main_name(self, html):
        try:
            # TODO 业务xpath
            return ""
        except Exception as e:
            raise ValueError(f'获取主名称失败:{e}') from e


    def get_main_price(self, html):
        try:
            # TODO 业务xpath
            return ""
        except Exception as e:
            raise ValueError(f'获取价格失败:{e}')
            return ""

    def get_main_sku(self, html):
        try:
            # TODO 业务xpath
            return ""
        except Exception as e:
            Tool.print(f'获取sku失败:{e}')
            return ""

    def get_main_desc(self, html):
        try:
            # TODO 业务xpath
            return ""
        except Exception as e:
            Tool.print(f'获取描述失败:{e}')
            return ""

    def get_main_imgs(self, html):
        try:
            # TODO 业务xpath，返回图片列表
            return []
        except Exception as e:
            Tool.print(f'获取图片失败:{e}')
            return []

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

    def check_cob(self, html):
        """判断是否存在变体商品"""
        try:
            # TODO 业务逻辑，返回 True/False
            return False
        except Exception as e:
            Tool.print(f'检测变体失败:{e}')
            return False

    def get_cobs(self, html):
        """抓取所有变体数据"""
        try:
            cobs = []
            s_ls = []  # TODO 变体节点列表xpath
            for _ in s_ls:
                # TODO 提取变体字段
                cob_imgs_ls = []
                cob_name = ""
                cob_price = ""
                cob_sku = None
                cob_att = {}

                cob_desc = Tool.HTML.clean_product_desc(cob_desc)
                cob_price = Tool.clean_price(cob_price)
                cob_imgs = Tool.Product.clean_imgs(cob_imgs_ls)
                cob = Tool.Product.Variation(
                    url=self.url, cat=self.category, imgs=cob_imgs,
                    name=cob_name, desc=cob_desc, price=cob_price,
                    sku=cob_sku, att=cob_att
                ).to_dic()
                cobs.append(cob)
            return cobs
        except Exception as e:
            Tool.print(f'获取变体数据失败:{e}')
            return []

    def run(self):
        try:
            """统一入口：执行解析，返回标准化产品字典列表"""
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
                    desc=main_desc,**main_att
                ).to_dic()
                return [product]

            return self.get_cobs(self.html)
        except Exception as e:
            Tool.print(f'run 解析失败:{e}')
            return []


class Crawler:
    def __init__(self, max_threads=10):
        self.input_file = input_file
        self.fail_file = fail_file
        self.max_threads = max_threads

        # 任务队列、结果队列
        self.task_queue = Queue()
        self.result_queue = Queue()

        # 缓存存储
        self.catch_data = dict()    # {seq_id: url} 任务索引
        self.index_data = dict()    # {url: [商品字典]} url -> 解析结果
        self.failures = dict()

        self.total_tasks = 0
        self.finished_count = 0

        # 内存缓存：同一url只请求一次，跨分类复用
        self.url_memory_cache = dict()

        # 线程锁
        self.global_lock = threading.Lock()
        self.cache_lock = threading.Lock()

        self._load_local_cache()

    def _load_local_cache(self):
        """启动加载本地持久化缓存"""
        self.catch_data = Tool.File.load_json(catch_path)
        self.index_data = Tool.File.load_json(index_path)
        Tool.print(f"本地缓存加载完成，已有任务：{len(self.catch_data)} 条")

    @staticmethod
    def _clone_with_category(rows, category):
        """复用同一url解析结果，替换分类名称，用于多分类共用商品链接场景"""
        result = []
        for row in rows:
            new_row = dict(row)
            new_row['Categories'] = category
            result.append(new_row)
        return result

    def load_tasks(self):
        """加载待抓取任务到队列"""
        data = Tool.File.load_json(self.input_file)
        seq_id = 0
        for category, urls in data.items():
            for url in urls:
                if url in input_url_no_ls:
                    continue
                self.task_queue.put((str(seq_id), category, url))
                seq_id += 1
                # 测试条数限制
                if isinstance(ts_num, int) and seq_id >= ts_num:
                    Tool.print(f'启用测试模式，限制任务数:{ts_num}')
                    self.total_tasks = seq_id
                    return
        self.total_tasks = seq_id

    def request_worker(self):
        """请求&解析工作线程"""
        while True:
            try:
                seq_id, category, url = self.task_queue.get_nowait()
            except Queue.Empty:
                break

            # 1. 判断本地磁盘缓存是否存在
            if url in self.index_data:
                with self.global_lock:
                    self.catch_data[seq_id] = {'url':url,'category':category}
                self.result_queue.put((seq_id, category, url, [], False))
                continue

            data = []
            is_failed = False
            try:
                res = Tool.get(url)
                if not res or not res.text:
                    raise Exception("请求返回空响应")

                # 页面解析
                parser = _T(url, category, res.text)
                raw_product_list = parser.run()

                # 标准化清洗结果
                parse_result = []
                for item in raw_product_list:
                    if isinstance(item, dict):
                        parse_result.append(item)
                    elif hasattr(item, "to_dic"):
                        parse_result.append(item.to_dic())

                # 写入内存缓存
                with self.cache_lock:
                    self.url_memory_cache[url] = parse_result
                data = parse_result

            except Exception as e:
                is_failed = True
                Tool.print(f"【任务失败】seq:{seq_id} url:{url} error:{str(e)}")
                with self.global_lock:
                    self.failures.setdefault(category, []).append(url)

            self.result_queue.put((seq_id, category, url, data, is_failed))

    def writer_worker(self):
        """统一写入线程：负责缓存落地，避免多线程同时写文件冲突"""
        flush_counter = 0
        flush_interval = 20

        while True:
            item = self.result_queue.get()
            if item is None:
                break

            seq_id, category, url, data, is_failed = item
            self.result_queue.task_done()

            # 成功解析，写入缓存索引
            if not is_failed:
                with self.global_lock:
                    data = data or self.index_data.get(url,[])
                    self.catch_data[seq_id] = {'url':url,'category':category}
                    self.index_data[url] = data

            # 进度统计
            with self.global_lock:
                self.finished_count += 1
                curr = self.finished_count
                total = self.total_tasks
                status_tag = "[FAILED]" if is_failed else "[OK]"
                print(f"{status_tag} {curr}/{total} | {url}")

            # 定时落地缓存文件
            flush_counter += 1
            if flush_counter >= flush_interval:
                flush_counter = 0
                self._save_all_cache()

        # 队列结束，最终持久化一次
        self._save_all_cache()

    def _save_all_cache(self):
        Tool.File.save_json(self.catch_data, catch_path)
        Tool.File.save_json(self.index_data, index_path)

    def run(self):
        self.load_tasks()
        Tool.print(f"总共待处理任务数量: {self.total_tasks}")

        # 启动写入线程
        writer_thread = threading.Thread(target=self.writer_worker)
        writer_thread.start()

        # 启动请求线程池
        thread_list = []
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.request_worker)
            t.start()
            thread_list.append(t)

        # 等待所有请求线程结束
        for t in thread_list:
            t.join()

        # 通知写入线程退出
        self.result_queue.put(None)
        writer_thread.join()

        # 导出CSV结果
        def iter_all_product_rows():
            for req_id,dc in self.catch_data.items():
                url = dc['url']
                cat = dc['category']

                data = self.index_data[url]
                
                data = self._clone_with_category(data,cat)

                yield from data



        all_rows = list(iter_all_product_rows())
        # 输出带URL版本CSV
        Tool.File.save_csv(all_rows, output_ts_file, columns=fieldnames)
        # 清理url字段后输出正式文件
        clean_rows = Tool.json_del_url(all_rows)
        Tool.File.save_csv(clean_rows, output_file, columns=fieldnames)

        # 保存失败链接
        Tool.File.save_json(self.failures, fail_file)

        Tool.print("\n====================抓取完成====================")
        Tool.print(f"输出表头: {fieldnames}")
        Tool.print("确认字段是否满足导入需求！")


def main():
    crawler = Crawler(max_threads=5)
    crawler.run()


if __name__ == '__main__':
    main()
