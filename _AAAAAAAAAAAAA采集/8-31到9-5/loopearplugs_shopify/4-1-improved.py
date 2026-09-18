import json
import csv
import time
import random
import uuid
import re
import threading
from queue import Queue
from curl_cffi import requests
import urllib3
from lxml import etree

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Crawler:
    """
    us.loopearplugs.com 产品自定义字段爬虫。
    专为 Loop 产品页面的 accordion（手风琴）结构优化。

    页面结构:
        <accordion-item class="accordion product__accordion">
          <details>
            <summary>
              <h2 class="accordion__title">What you get</h2>
              <div class="accordion__icon"></div>
            </summary>
            <div class="accordion__content rte">
              <!-- 富文本内容 -->
            </div>
          </details>
        </accordion-item>

    提取规则:
        1. Description: 从 .product__description rte 中提取完整 HTML
        2. What you get: 从 accordion-item 标题为 "What you get" 的区块提取完整 HTML
        3. Shipping & returns: 从标题为 "Shipping & returns" 的区块提取完整 HTML
        4. Understanding noise reduction: 从标题为 "Understanding noise reduction" 的区块提取（部分产品没有此区块）
        5. FAQ: 从所有剩余 accordion-item（FAQ 区块）提取 Q&A 并合并为完整 HTML
    输出格式: CSV
    """

    BASE_URL = "https://us.loopearplugs.com"

    def __init__(self, input_file, output_file, fail_file, proxies=None,
                 max_threads=5, max_retries=3, batch_size=50, use_proxy=False,
                 base_delay=5.0, max_delay=60.0, requests_per_minute=12):
        self.input_file = input_file
        self.output_file = output_file
        self.fail_file = fail_file
        self.proxies = proxies if proxies else []
        self.max_threads = max_threads
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.use_proxy = use_proxy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / self.requests_per_minute

        self.task_queue = Queue()
        self.result_queue = Queue()
        self.failures = {"failed_urls": []}
        self.total_tasks = 0
        self.completed_tasks = 0
        self.lock = threading.Lock()
        self.last_request_time = 0.0

        # 模拟标准浏览器头
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        }

        # ================= 核心配置 1：定义需要提取的字段映射 =================
        # 键: accordion 标题文本 (不区分大小写)
        # 值: CSV 列名
        self.heading_mapping = {
            "What you get": "What you get (product.metafields.c_f.what_you_get)",
            "Shipping & returns": "Shipping & returns (product.metafields.c_f.shipping_returns)",
            "Understanding noise reduction": "Understanding noise reduction (product.metafields.c_f.understanding_noise_reduction)",
        }

        # 额外字段（非 accordion 结构，单独提取）
        self.description_field = "Description (product.metafields.c_f.description)"
        self.faq_field = "FAQ (product.metafields.c_f.faq)"

        # CSV 表头
        self.fieldnames = ["SKU", self.description_field] + list(self.heading_mapping.values()) + [self.faq_field]

    def get_proxy(self):
        if not self.use_proxy or not self.proxies:
            return None
        proxy_str = self.proxies[uuid.uuid4().int % len(self.proxies)]
        ip, port, user, pwd = proxy_str.split(":")
        return {
            "http": f"http://{user}:{pwd}@{ip}:{port}",
            "https": f"http://{user}:{pwd}@{ip}:{port}",
        }

    def _throttle(self):
        now = time.time()
        elapsed = now - self.last_request_time
        wait = self.min_interval - elapsed
        if wait > 0:
            jitter = random.uniform(0, min(2.0, wait * 0.3))
            time.sleep(wait + jitter)
        self.last_request_time = time.time()

    def _backoff_wait(self, attempt, status_code=429):
        if status_code == 429:
            delay = min(self.base_delay * (2 ** attempt) + random.uniform(1, 3), self.max_delay)
            print(f"      429 限流，等待 {delay:.1f} 秒后重试 (第 {attempt + 1}/{self.max_retries} 次)...")
        else:
            # 503/502/504
            delay = min(5 + (attempt ** 2) * 2 + random.uniform(1, 3), self.max_delay)
            print(
                f"      {status_code} 服务不可用，等待 {delay:.1f} 秒后重试 (第 {attempt + 1}/{self.max_retries} 次)...")
        time.sleep(delay)

    def load_tasks(self):
        with open(self.input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        urls = []
        if isinstance(data, list):
            urls = data
        elif isinstance(data, dict):
            # 注意：此处不做全局去重！
            for category, url_list in data.items():
                if isinstance(url_list, list):
                    for url in url_list:
                        urls.append(url)
                elif isinstance(url_list, str):
                    urls.append(url_list)

        # 清洗URL：确保标准格式
        cleaned_urls = []
        for url in urls:
            # 统一域名格式 (将其他 Loop 域名统一为 us.loopearplugs.com)
            url = url.replace("https://www.loopearplugs.com/", "https://us.loopearplugs.com/")
            url = url.replace("https://loopearplugs.com/", "https://us.loopearplugs.com/")

            # 去除查询参数 (?variant= 等)
            url = url.split("?")[0]

            # 如果 URL 包含 /collections/ 和 /products/，提取纯产品 URL
            if "/collections/" in url and "/products/" in url:
                parts = url.split("/products/")
                if len(parts) == 2:
                    url = f"{self.BASE_URL}/products/{parts[1]}"

            # 确保以 / 结尾的 URL 去除尾部斜杠
            url = url.rstrip("/")

            cleaned_urls.append(url)

        self.total_tasks = len(cleaned_urls)
        for url in cleaned_urls:
            self.task_queue.put(url)

    def fetch(self, url):
        """使用 curl_cffi 模拟浏览器请求，返回 HTML 文本或 None"""
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                resp = requests.get(
                    url,
                    proxies=self.get_proxy(),
                    timeout=30,
                    impersonate="chrome120",
                    headers=self.headers,
                    verify=False
                )
                status = getattr(resp, "status_code", None)

                if status == 200:
                    return resp.text
                elif status == 429:
                    self._backoff_wait(attempt, status_code=429)
                    continue
                elif status in (502, 503, 504):
                    self._backoff_wait(attempt, status_code=status)
                    continue
                else:
                    print(f"      [HTTP {status}] {url}")
                    return None

            except Exception as e:
                print(f"      [!] 请求异常: {e}")
                wait = min(self.base_delay * (2 ** attempt), self.max_delay)
                time.sleep(wait)

        return None

    # ================= 核心配置 2：统一提取方法（适配 Loop 网站结构） =================

    def extract_description(self, tree):
        """
        从产品页面提取主描述内容。

        Loop 网站结构:
        <div class="product__description rte quick-add-hidden body">
          <p>描述文本...</p>
        </div>
        """
        desc_nodes = tree.xpath(
            '//div[contains(@class, "product__description") and contains(@class, "rte")]'
        )

        if desc_nodes:
            try:
                html_content = etree.tostring(
                    desc_nodes[0], method='html', encoding='utf-8'
                ).decode('utf-8')
                # 移除 HTML 注释
                html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
                return html_content.strip()
            except Exception:
                return desc_nodes[0].text_content().strip()

        return ""

    def extract_metafield_content(self, tree, target_label):
        """
        根据给定的字段标签，从 Loop 产品页面提取对应的 HTML 内容。

        Loop 网站结构:
        <accordion-item class="accordion product__accordion">
          <details>
            <summary>
              <h2 class="accordion__title text-label-base">What you get</h2>
              <div class="accordion__icon"></div>
            </summary>
            <div class="accordion__content rte text-label-base">
              <p>内容文本...</p>
            </div>
          </details>
        </accordion-item>
        """
        target_label_lower = target_label.strip().lower()

        # 遍历所有带有 accordion__title 的元素，找到与目标标签匹配的项
        title_elements = tree.xpath('//*[contains(@class, "accordion__title")]')

        for title_el in title_elements:
            title_text = ' '.join(title_el.itertext()).strip().lower()
            title_text = ' '.join(title_text.split())  # 清理空白

            if title_text != target_label_lower:
                continue

            # 从 title 元素向上查找 details 父级，再向下查找 accordion__content
            # 结构: h2/h3.accordion__title -> summary -> details -> div.accordion__content
            details_parent = title_el.getparent()  # summary
            if details_parent is not None:
                details_parent = details_parent.getparent()  # details

            if details_parent is not None:
                content_divs = details_parent.xpath(
                    './/div[contains(@class, "accordion__content")]'
                )

                if content_divs:
                    try:
                        # 使用 tostring 保留富文本结构，这对 WooCommerce 导入非常重要
                        html_content = etree.tostring(
                            content_divs[0], method='html', encoding='utf-8'
                        ).decode('utf-8')
                        # 移除 HTML 注释
                        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
                        return html_content.strip()
                    except Exception:
                        return content_divs[0].text_content().strip()

        return ""

    def extract_faq(self, tree, known_titles):
        """
        提取产品页面中所有 FAQ accordion 项，合并为一个 HTML 字符串。

        FAQ 项是所有 accordion 项中标题不属于已知自定义字段的项。
        每个FAQ项的格式:
        <div class="faq-item">
          <h3>问题文本</h3>
          <div class="faq-answer">回答 HTML</div>
        </div>
        """
        known_titles_lower = set(t.strip().lower() for t in known_titles)

        title_elements = tree.xpath('//*[contains(@class, "accordion__title")]')

        faq_parts = []

        for title_el in title_elements:
            title_text = ' '.join(title_el.itertext()).strip()
            title_text_clean = ' '.join(title_text.split())
            title_lower = title_text_clean.lower()

            # 跳过已知自定义字段
            if title_lower in known_titles_lower:
                continue

            # 从 title 元素向上查找 details 父级，再向下查找 accordion__content
            details_parent = title_el.getparent()  # summary
            if details_parent is not None:
                details_parent = details_parent.getparent()  # details

            if details_parent is None:
                continue

            content_divs = details_parent.xpath(
                './/div[contains(@class, "accordion__content")]'
            )

            if not content_divs:
                continue

            try:
                content_html = etree.tostring(
                    content_divs[0], method='html', encoding='utf-8'
                ).decode('utf-8')
                content_html = re.sub(r'<!--.*?-->', '', content_html, flags=re.DOTALL)
            except Exception:
                content_html = content_divs[0].text_content().strip()

            # 构建 FAQ 条目 HTML
            tag = title_el.tag  # h2 或 h3
            faq_parts.append(
                f'<div class="faq-item">\n'
                f'  <{tag} class="faq-question">{title_text_clean}</{tag}>\n'
                f'  <div class="faq-answer">{content_html.strip()}</div>\n'
                f'</div>'
            )

        if faq_parts:
            return "\n".join(faq_parts)

        return ""

    def process_response(self, response_text, url):
        try:
            tree = etree.HTML(response_text)
            sku = url.rstrip("/").split("/")[-1]

            # 初始化结果行
            result = {"SKU": sku}
            for field in self.fieldnames:
                if field != "SKU":
                    result[field] = ""

            found_any = False

            # 1. 提取 Description
            desc_content = self.extract_description(tree)
            result[self.description_field] = desc_content
            if desc_content:
                found_any = True

            # 2. 提取 accordion 自定义字段
            for heading_text, field_name in self.heading_mapping.items():
                content = self.extract_metafield_content(tree, heading_text)
                result[field_name] = content
                if content:
                    found_any = True

            # 3. 提取 FAQ（排除已知字段标题）
            faq_content = self.extract_faq(tree, list(self.heading_mapping.keys()))
            result[self.faq_field] = faq_content
            if faq_content:
                found_any = True

            # 如果完全没有匹配到任何一个字段，标记为失败
            if not found_any:
                self.failures["failed_urls"].append({"url": url, "reason": "no_metafield_found"})
                return []

            return [result]

        except Exception as e:
            self.failures["failed_urls"].append({"url": url, "reason": f"parse_error: {e}"})
            return []

    def worker(self):
        while True:
            try:
                url = self.task_queue.get_nowait()
            except Exception:
                break

            try:
                response_text = self.fetch(url)
                if response_text:
                    cleaned = self.process_response(response_text, url)
                    if not cleaned:
                        with self.lock:
                            print(f"[FAILED - parse] {url}")
                    else:
                        for row in cleaned:
                            self.result_queue.put(row)
                else:
                    with self.lock:
                        print(f"[FAILED - fetch] `{url}`")
                        self.failures["failed_urls"].append({"url": url, "reason": "fetch_failed"})

                with self.lock:
                    self.completed_tasks += 1
                    if self.completed_tasks % 10 == 0 or self.completed_tasks == self.total_tasks:
                        print(f"[PROGRESS] 已完成 {self.completed_tasks}/{self.total_tasks}")

            finally:
                self.task_queue.task_done()

    def writer_worker(self, fieldnames):
        with open(self.output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            buffer = []

            while True:
                item = self.result_queue.get()
                if item is None:
                    if buffer:
                        writer.writerows(buffer)
                        buffer.clear()
                    self.result_queue.task_done()
                    break

                buffer.append(item)
                if len(buffer) >= self.batch_size:
                    writer.writerows(buffer)
                    buffer.clear()

                self.result_queue.task_done()

    def run(self):
        self.load_tasks()

        print(f"\n{'=' * 70}")
        print(f"us.loopearplugs.com 自定义 Metafield 爬虫启动 (Accordion 结构适配版)")
        print(f"  总产品数: {self.total_tasks}")
        print(f"  线程数: {self.max_threads}")
        print(f"  请求限速: {self.requests_per_minute} 次/分钟")
        print(f"  HTTP客户端: curl_cffi (impersonate=chrome120)")
        print(f"  代理状态: {'开启' if self.use_proxy else '关闭'}")
        print(f"  输出文件: {self.output_file}")
        print(f"{'=' * 70}\n")

        time.sleep(random.uniform(1, 3))
        self.last_request_time = time.time()

        writer_thread = threading.Thread(target=self.writer_worker, args=(self.fieldnames,), daemon=True)
        writer_thread.start()

        threads = []
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.task_queue.join()
        self.result_queue.put(None)
        writer_thread.join()

        with open(self.fail_file, "w", encoding="utf-8") as f:
            json.dump(self.failures, f, ensure_ascii=False, indent=4)

        print(f"\n{'=' * 70}")
        print(f"产品详情爬取完成!")
        print(f"  总产品数: {self.total_tasks}")
        print(f"  成功: {self.total_tasks - len(self.failures['failed_urls'])}")
        print(f"  失败: {len(self.failures['failed_urls'])}")
        print(f"  输出文件: {self.output_file}")
        print(f"  失败记录: {self.fail_file}")
        print(f"{'=' * 70}")


if __name__ == "__main__":
    proxies = [
        # "ip:port:user:password",
    ]

    crawler = Crawler(
        input_file=r"C:\实习\loopearplugs\output\detail_url2.json",
        output_file=r"C:\实习\loopearplugs\output\des.csv",
        fail_file=r"C:\实习\loopearplugs\output\fail.json",
        proxies=proxies,
        max_threads=3,
        max_retries=3,
        batch_size=50,
        use_proxy=False,
        base_delay=5.0,
        max_delay=60.0,
        requests_per_minute=12,
    )
    crawler.run()
