"""商品详情抓取模板（多线程 + 缓存）

通用流程：加载 URL 任务 -> 多线程请求解析 -> 缓存 -> 输出 result.csv
专有逻辑（各站点不同）交由子类实现 fetch_product：
"""
import hashlib
import json
import threading
from decimal import Decimal, InvalidOperation
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
                 max_threads=5,
                 retry_failed_tasks=True,
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
        self.retry_failed_tasks = bool(retry_failed_tasks)

        # 任务队列、结果队列
        self.task_queue = Queue()
        self.result_queue = Queue()

        # 缓存模型统一复用 modal.py 中的 DetailCatch / DetailIndex。
        self.catch = None
        self.index = None
        self.catch_data = {}
        self.index_data = {}
        self.failures = {}
        # Failures are kept per category task until a retry succeeds.  The
        # public fail file is built from this final state, not from first-pass
        # errors that later recovered.
        self._failed_tasks = {}
        self._initial_failed_tasks = {}

        self.total_tasks = 0
        self.finished_count = 0
        self.retry_total = 0
        self.retry_finished_count = 0
        # Output order belongs to the current input mapping, not to cache or
        # worker completion order.  Each entry is (source_order, category,
        # source_url, cache_task_id).
        self.ordered_tasks = []
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

    def should_stop_requests(self):
        """Return ``True`` when site-specific request workers should stop.

        The default keeps the normal Step4 behavior. A site can override this
        for a manual anti-bot checkpoint without recording queued URLs as
        failed or caching empty product rows.
        """
        return False


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

    @staticmethod
    def _has_required_cache_value(value):
        """Return whether a universal Step4 field is non-empty."""
        if isinstance(value, (list, tuple, set)):
            return any(Get_Product._has_required_cache_value(item) for item in value)
        if value is None:
            return False

        return bool(str(value).strip())

    @staticmethod
    def _has_positive_price(value):
        """Accept only positive integer or decimal sale/regular prices."""
        if value is None or isinstance(value, bool):
            return False
        normalized = str(value).strip().replace("$", "").replace(",", "")
        normalized = normalized.replace("/ea", "").replace("/EA", "").strip()
        if not normalized:
            return False
        try:
            price = Decimal(normalized)
            return price.is_finite() and price > 0
        except (InvalidOperation, ValueError):
            return False

    def _validate_rows_before_cache(self, rows):
        """Apply Type-specific cache requirements immediately before persistence."""
        requirements = {
            "simple": ("SKU", "Name", "Description", "Images"),
            "variable": ("SKU", "Name", "Description", "Images"),
            "variation": ("SKU", "Name", "Parent"),
        }
        for position, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise ValueError(f"商品第 {position} 行不是字典，未写入缓存")

            product_type = str(row.get("Type") or "simple").strip().casefold()
            if product_type not in requirements:
                raise ValueError(
                    f"商品第 {position} 行 Type 无效，未写入缓存: {row.get('Type')!r}"
                )

            missing = [
                field
                for field in requirements[product_type]
                if not self._has_required_cache_value(row.get(field))
            ]
            if missing:
                raise ValueError(
                    f"商品第 {position} 行 {product_type} 必要字段缺失，未写入缓存: "
                    + ", ".join(missing)
                )

            if product_type != "variable":
                invalid_prices = [
                    field
                    for field in ("Sale price", "Regular price")
                    if not self._has_positive_price(row.get(field))
                ]
                if invalid_prices:
                    raise ValueError(
                        f"商品第 {position} 行 {product_type} 价格无效，未写入缓存: "
                        + ", ".join(invalid_prices)
                    )
            row["Stock"] = 1000

    def _get_url_lock(self, url):
        with self.url_locks_lock:
            return self.url_locks.setdefault(url, threading.Lock())

    def _mark_cache_changed(self):
        self.cache_changes_since_save += 1

    @staticmethod
    def _failure_key(category, task_id):
        return category, task_id

    def _record_failure(self, category, task_id, url, attempt):
        key = self._failure_key(category, task_id)
        with self.global_lock:
            task = (task_id, category, url)
            self._failed_tasks[key] = task
            if attempt == 0:
                self._initial_failed_tasks.setdefault(key, task)

    def _clear_failure(self, category, task_id):
        with self.global_lock:
            self._failed_tasks.pop(self._failure_key(category, task_id), None)

    def _failure_mapping(self):
        failures = {}
        with self.global_lock:
            for _, category, url in self._failed_tasks.values():
                failures.setdefault(category, []).append(url)
        return failures

    @staticmethod
    def _clone_with_category(rows, category, source_url=''):
        """复用同一 url 解析结果，替换分类名称并保留调试来源 URL。"""
        result = []
        for row in rows:
            new_row = dict(row).copy()
            new_row['Categories'] = category
            new_row.setdefault('url', source_url)
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
        task_count = 0
        source_order = 0
        self.ordered_tasks = []
        ordered_task_keys = set()

        for category, urls in data.items():
            if not isinstance(urls, (list, tuple)):
                raise TypeError(f"Step4 URLs for category {category!r} must be a list")
            for url in urls:

                if url in self.skip_input_url_ls:
                    continue
                task_count += 1

                # 同一个 URL 不同分类共用一份商品解析结果。
                task_id = self._generate_task_id(url)
                task_key = (category, task_id)
                if task_key not in ordered_task_keys:
                    self.ordered_tasks.append((source_order, category, url, task_id))
                    ordered_task_keys.add(task_key)
                    source_order += 1
                if self.index.check(url, task_id):
                    # 直接交给 writer_worker 记录分类任务。
                    with self.global_lock:
                        if task_id not in self.catch.check(category):
                            self.catch.append(category, task_id, url)
                            self._mark_cache_changed()
                    self.result_queue.put((task_id, category, url, [], False, 0))
                else:
                    # 未命中，交给请求线程池去抓取
                    self.task_queue.put((task_id, category, url, 0))

                if isinstance(self.ts_num, int) and task_count >= self.ts_num:
                    self.Tool.print(f'启用测试模式，限制任务数:{self.ts_num}')
                    self.total_tasks = task_count
                    return
        self.total_tasks = task_count

    def request_worker(self):
        try:
            while True:
                if self.should_stop_requests():
                    break
                try:
                    task_id, category, url, attempt = self.task_queue.get_nowait()
                except Empty:
                    break

                # 同一 URL 可能属于多个分类，避免并发线程重复请求。
                with self._get_url_lock(url):
                    cached_data = self.index.check(url, task_id)
                    if cached_data:
                        with self.global_lock:
                            if task_id not in self.catch.check(category):
                                self.catch.append(category, task_id, url)
                                self._mark_cache_changed()
                        self.result_queue.put((task_id, category, url, [], False, attempt))
                        continue

                    data = []
                    is_failed = False
                    try:
                        parse_result = self.fetch_product(url, category)
                        data = self._normalize_products(parse_result)
                        if not data:
                            raise ValueError('商品解析结果为空，不写入缓存，将在下次运行时重试。')
                        self._validate_rows_before_cache(data)

                        # 立即写入 DetailIndex 的内存数据，供同 URL 的其他线程复用。
                        with self.global_lock:
                            self.index.append(task_id, url, data)
                            self.fetched_urls.append(url)
                            self._mark_cache_changed()

                    except Exception as e:
                        is_failed = True
                        self.Tool.print(f"【任务失败】task:{task_id} url:{url} error:{e}")
                        self._record_failure(category, task_id, url, attempt)

                    self.result_queue.put((task_id, category, url, data, is_failed, attempt))
        finally:
            self.close_playwright()

    def writer_worker(self):
        while True:
            item = self.result_queue.get()
            if item is None:
                break

            task_id, category, url, data, is_failed, attempt = item
            self.result_queue.task_done()

            fetched_this_run = False
            if not is_failed:
                with self.global_lock:
                    fetched_this_run = bool(data)
                    data = data or self.index.check(url, task_id) or []
                    if task_id not in self.catch.check(category):
                        self.catch.append(category, task_id, url)
                        self._mark_cache_changed()
                self._clear_failure(category, task_id)

            with self.global_lock:
                if attempt:
                    self.retry_finished_count += 1
                    curr = self.retry_finished_count
                    total = self.retry_total
                    status_prefix = "[RETRY "
                    status_suffix = "]"
                else:
                    self.finished_count += 1
                    curr = self.finished_count
                    total = self.total_tasks
                    status_prefix = "["
                    status_suffix = "]"
                status = "FAILED" if is_failed else "OK" if fetched_this_run else "CATCH"
                status_tag = f"{status_prefix}{status}{status_suffix}"
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

    def _run_request_workers(self):
        thread_list = []
        for _ in range(self.max_threads):
            thread = threading.Thread(target=self.request_worker)
            thread.start()
            thread_list.append(thread)
        for thread in thread_list:
            thread.join()

    def _retry_failed_task_batch(self):
        """Run one extra request phase after the initial queue has drained."""
        if not self.retry_failed_tasks:
            return
        if not self.task_queue.empty():
            self.Tool.print(
                "检测到未启动的任务，跳过本轮失败补抓；保留给下次运行。",
                color='yellow',
            )
            return

        with self.global_lock:
            retry_tasks = list(self._failed_tasks.values())
        if not retry_tasks:
            return
        self.retry_total = len(retry_tasks)
        self.retry_finished_count = 0
        self.Tool.print(
            f"首轮失败 {self.retry_total} 个任务，开始集中补抓一次。",
            color='yellow',
        )
        self.task_queue = Queue()
        for task_id, category, url in retry_tasks:
            self.task_queue.put((task_id, category, url, 1))
        self._run_request_workers()

    def _iter_all_product_rows(self):
        """Yield cached product rows in current input-file order.

        ``Catch`` is written by concurrent workers and is therefore a cache
        membership record, not an ordering source.  Rebuilding this iterator
        from ``ordered_tasks`` also makes a cache-only run honor a newly
        reordered detail-url input file.  Each product's parent/variation rows
        remain in their original order.
        """
        for _, category, source_url, task_id in self.ordered_tasks:
            data = self.index.check(source_url, task_id) or []
            yield from self._clone_with_category(data, category, source_url)

    def run(self):
        self.load_tasks()
        self.Tool.print(f"总共待处理任务数量: {self.total_tasks}")

        writer_thread = threading.Thread(target=self.writer_worker)
        writer_thread.start()

        self._run_request_workers()
        self._retry_failed_task_batch()

        self.result_queue.put(None)
        writer_thread.join()
        self.tool.print(f'正在生成csv文件')
        all_rows = list(self._iter_all_product_rows())

        self.tool.File.save_csv(all_rows, self.output_ts_file, columns=self.fieldnames)
        clean_rows = self.tool.json_del_url(all_rows)
        self.tool.File.save_csv(clean_rows, self.output_file, columns=self.fieldnames)

        self.failures = self._failure_mapping()
        self.tool.File.save_json(self.failures, self.fail_file)

        initial_failure_count = len(self._initial_failed_tasks)
        final_failure_count = len(self._failed_tasks)
        recovered_count = initial_failure_count - final_failure_count
        self.Tool.print(
            "商品抓取失败统计："
            f"首轮失败 {initial_failure_count} 个，"
            f"补抓恢复 {max(0, recovered_count)} 个，"
            f"最终失败 {final_failure_count} 个。",
            color='yellow' if final_failure_count else 'green',
        )

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
