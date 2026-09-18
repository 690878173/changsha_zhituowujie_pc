"""商品详情抓取模板（多线程 + 缓存）

通用流程：加载 URL 任务 -> 多线程请求解析 -> 缓存 -> 输出 result.csv
专有逻辑（各站点不同）交由子类实现 fetch_product：
"""
import hashlib
import json
import threading
from queue import Queue
from queue import Empty

from _ljp.mb.model import Catch, Index,Base

class Get_Product(Base):
    """商品详情抓取基类"""

    def __init__(self, tool,
                 input_path,
                 output_path,
                 fail_file,
                 catch_path,
                 index_path,
                 output_ts_file,
                 catch_save_num=None,
                 ts_num=None,
                 skip_input_url_ls=None,
                 skip_output_url_ls=None,
                 flush=False,
                 fieldnames=None,
                 max_threads=5
                 ):
        self.tool = tool
        self.Tool = tool
        self.input_path = input_path
        self.output_file = output_path
        self.fail_file = fail_file
        self.catch_path = catch_path
        self.index_path = index_path
        self.output_ts_file = output_ts_file

        self.catch_save_num = catch_save_num or 20
        self.ts_num = ts_num
        self.skip_input_url_ls = skip_input_url_ls or []
        self.skip_output_url_ls = skip_output_url_ls or []
        self.flush = flush
        self.fieldnames = fieldnames
        self.max_threads = max_threads

        # 任务队列、结果队列
        self.task_queue = Queue()
        self.result_queue = Queue()

        # 缓存模型统一复用 modal.py 中的 DetailCatch / DetailIndex。
        self.catch = None
        self.index = None
        self.catch_data = {}
        self.index_data = {}
        self.failures = {}

        self.total_tasks = 0
        self.finished_count = 0
        # URLs that missed the disk/in-memory cache and produced product rows this run.
        self.fetched_urls = []

        self.cache_changes_since_save = 0

        self.global_lock = threading.Lock()
        self.url_locks = {}
        self.url_locks_lock = threading.Lock()

        self._init()

    # ================= 专有逻辑（子类实现） =================


    def fetch_product(self, url, category) -> list[dict]:
        """请求并解析单个商品。

        返回标准化产品字典列表（每个元素为 Product.to_dic() 结果）。
        """
        raise NotImplementedError


    # ================= 通用流程（无需修改） =================

    def _normalize_products(self, parse_result):
        """将站点返回值统一为可写入商品索引的字典列表。"""
        if parse_result is None:
            return []
        if isinstance(parse_result, dict):
            parse_result = [parse_result]

        data = []
        for item in parse_result:
            if isinstance(item, dict):
                data.append(item)
            elif hasattr(item, 'to_dic'):
                data.append(item.to_dic())
        return data

    def _get_url_lock(self, url):
        with self.url_locks_lock:
            return self.url_locks.setdefault(url, threading.Lock())

    def _mark_cache_changed(self):
        self.cache_changes_since_save += 1

    @staticmethod
    def _clone_with_category(rows, category):
        """复用同一 url 解析结果，替换分类名称"""
        result = []
        for row in rows:
            new_row = dict(row).copy()
            new_row['Categories'] = category
            result.append(new_row)
        return result

    @staticmethod
    def _generate_task_id(url, category=None):
        """生成确定性唯一 ID；商品结果按 URL 共享缓存。"""
        if not isinstance(category, str):
            cat_str = json.dumps(category, sort_keys=True, ensure_ascii=False)
        else:
            cat_str = category

        # 2. 拼接并用 MD5 生成 32 位哈希
        raw = f"{url}||{cat_str}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()

    def load_tasks(self):
        data = self.tool.File.load_json(self.input_path)
        self._load_tasks_from_mapping(data)

    def _load_tasks_from_mapping(self, data):
        """Queue standard ``{category: [url]}`` tasks for the shared cache flow."""
        if not isinstance(data, dict):
            raise TypeError("Step4 input must be a category-to-URL mapping")
        seq_id = 0

        for category, urls in data.items():
            if not isinstance(urls, (list, tuple)):
                raise TypeError(f"Step4 URLs for category {category!r} must be a list")
            for url in urls:

                if url in self.skip_input_url_ls:
                    continue
                seq_id += 1

                # 同一个 URL 不同分类共用一份商品解析结果。
                task_id = self._generate_task_id(url)
                if self.index.check(url, task_id):
                    # 直接交给 writer_worker 记录分类任务。
                    with self.global_lock:
                        if task_id not in self.catch.check(category):
                            self.catch.append(category, task_id, url)
                            self._mark_cache_changed()
                    self.result_queue.put((task_id, category, url, [], False))
                else:
                    # 未命中，交给请求线程池去抓取
                    self.task_queue.put((str(task_id ), category, url))

                if isinstance(self.ts_num, int) and seq_id >= self.ts_num:
                    self.Tool.print(f'启用测试模式，限制任务数:{self.ts_num}')
                    self.total_tasks = seq_id
                    return
        self.total_tasks = seq_id

    def request_worker(self):
        try:
            while True:
                try:
                    seq_id, category, url = self.task_queue.get_nowait()
                except Empty:
                    break

                # 同一 URL 可能属于多个分类，避免并发线程重复请求。
                with self._get_url_lock(url):
                    cached_data = self.index.check(url, seq_id)
                    if cached_data:
                        with self.global_lock:
                            if seq_id not in self.catch.check(category):
                                self.catch.append(category, seq_id, url)
                                self._mark_cache_changed()
                        self.result_queue.put((seq_id, category, url, [], False))
                        continue

                    data = []
                    is_failed = False
                    try:
                        parse_result = self.fetch_product(url, category)
                        data = self._normalize_products(parse_result)
                        if not data:
                            raise ValueError('商品解析结果为空，不写入缓存，将在下次运行时重试。')

                        # 立即写入 DetailIndex 的内存数据，供同 URL 的其他线程复用。
                        with self.global_lock:
                            self.index.append(seq_id, url, data)
                            self.fetched_urls.append(url)
                            self._mark_cache_changed()

                    except Exception as e:
                        is_failed = True
                        self.Tool.print(f"【任务失败】seq:{seq_id} url:{url} error:{e}")
                        with self.global_lock:
                            self.failures.setdefault(category, []).append(url)

                    self.result_queue.put((seq_id, category, url, data, is_failed))
        finally:
            self.close_playwright()

    def writer_worker(self):
        while True:
            item = self.result_queue.get()
            if item is None:
                break

            seq_id, category, url, data, is_failed = item
            self.result_queue.task_done()

            fetched_this_run = False
            if not is_failed:
                with self.global_lock:
                    fetched_this_run = bool(data)
                    data = data or self.index.check(url, seq_id) or []
                    if seq_id not in self.catch.check(category):
                        self.catch.append(category, seq_id, url)
                        self._mark_cache_changed()

            with self.global_lock:
                self.finished_count += 1
                curr = self.finished_count
                total = self.total_tasks
                status_tag = "[FAILED]" if is_failed else "[OK]" if fetched_this_run else "[CATCH]"
                print(f"{status_tag} {curr}/{total} | {url}")
                if fetched_this_run:
                    print(f'[OK DATA] rows={len(data)}')

            with self.global_lock:
                should_flush = (
                    self.cache_changes_since_save > 0
                    and self.cache_changes_since_save >= self.catch_save_num
                )
            if should_flush:
                self._save_all_cache()

        self._save_all_cache()

    def _save_all_cache(self):
        with self.global_lock:
            self.index.save()
            self.catch.save()
            self.cache_changes_since_save = 0
            return True

    def _iter_all_product_rows(self):
        for category, task_data in self.catch.data.items():
            for task_id, task in task_data.items():
                data = self.index.check(task['url'], task_id) or []
                yield from self._clone_with_category(data, category)

    def run(self):
        self.load_tasks()
        self.Tool.print(f"总共待处理任务数量: {self.total_tasks}")

        writer_thread = threading.Thread(target=self.writer_worker)
        writer_thread.start()

        thread_list = []
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.request_worker)
            t.start()
            thread_list.append(t)

        for t in thread_list:
            t.join()

        self.result_queue.put(None)
        writer_thread.join()

        all_rows = list(self._iter_all_product_rows())

        self.tool.File.save_csv(all_rows, self.output_ts_file, columns=self.fieldnames)
        clean_rows = self.tool.json_del_url(all_rows)
        self.tool.File.save_csv(clean_rows, self.output_file, columns=self.fieldnames)

        self.tool.File.save_json(self.failures, self.fail_file)

        if self.fetched_urls:
            self.Tool.print(
                f"本次缓存未命中且请求成功的 URL（{len(self.fetched_urls)} 个）："
            )
            print('\n'.join(self.fetched_urls))
        else:
            self.Tool.print('本次没有缓存未命中且请求成功的 URL。')

        self.Tool.print("====================抓取完成====================")

        self.Tool.print(f"输出表头: {self.fieldnames or self.tool.File.read_csv(data=clean_rows).columns}")
        self.Tool.print("确认字段是否满足导入需求！")

        return all_rows
