import json
import csv
import re
import time
import uuid
import html
from curl_cffi import requests
import threading
from queue import Queue
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from lxml import etree


class Crawler:
    def __init__(self, input_file, output_file, fail_file, proxies=None,
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

        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }
        self.cookies = {}

    # ==================== JSON-LD 解析 ====================

    def _extract_jsonld_products(self, tree):
        """从页面所有 <script type="application/ld+json"> 中提取 Product 类型数据"""
        scripts = tree.xpath('//script[@type="application/ld+json"]/text()')
        products = []
        for script_text in scripts:
            try:
                data = json.loads(script_text)
                graph = data.get("@graph", [data])
                for item in graph:
                    if not isinstance(item, dict):
                        continue
                    t = item.get("@type")
                    if t == "Product" or (isinstance(t, list) and "Product" in t):
                        products.append(item)
            except (json.JSONDecodeError, TypeError):
                continue
        return products

    def _get_brand_from_jsonld(self, products):
        """从 JSON-LD Product 列表中提取品牌名"""
        for p in products:
            brand = p.get("brand")
            if isinstance(brand, dict) and brand.get("name"):
                return brand["name"]
        return "Black Girl Sunscreen"

    def _get_price_from_jsonld(self, product):
        """从单个 JSON-LD Product 条目提取价格，返回两位小数字符串"""
        offers = product.get("offers")
        if not offers:
            return ""
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = offers.get("price")
        if price is None:
            specs = offers.get("priceSpecification", [])
            if isinstance(specs, list) and specs:
                price = specs[0].get("price", "")
            elif isinstance(specs, dict):
                price = specs.get("price", "")
        if price in (None, "", []):
            return ""
        try:
            return f"{float(price):.2f}"
        except (ValueError, TypeError):
            return ""

    def _extract_variation_data_fallback(self, tree):
        """
        当 JSON-LD 无变体数据时，从 form 的 data-product_variations 属性中
        提取变体的 size / price / regular_price 作为兜底。
        """
        form = tree.xpath('//form[contains(@class,"variations_form")]')
        if not form:
            return []
        raw = form[0].get("data-product_variations", "")
        if not raw:
            return []
        try:
            decoded = html.unescape(raw)
            variations = json.loads(decoded)
        except (json.JSONDecodeError, TypeError):
            return []

        results = []
        for v in variations:
            attrs = v.get("attributes", {})
            size = attrs.get("attribute_size", "")
            disp_price = v.get("display_price")
            reg_price = v.get("display_regular_price")
            results.append({
                "size": size,
                "price": f"{disp_price:.2f}" if disp_price else "",
                "regular_price": f"{reg_price:.2f}" if reg_price else "",
            })
        return results

    # ==================== 请求 ====================

    def fetch(self, category, url):
        import random

        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    time.sleep(random.uniform(1.5, 3.5))

                response = requests.get(
                    url,
                    proxies=self.get_proxy(),
                    timeout=12,
                    impersonate="chrome110",
                    cookies=self.cookies,
                    headers=self.headers,
                )
                if response.status_code == 200:
                    return response.text
                elif response.status_code in [403, 429]:
                    time.sleep(5)
            except Exception:
                pass

        return None

    def load_tasks(self):
        with open(self.input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.total_tasks = sum(len(urls) for urls in data.values())

        seq_id = 0
        for category, urls in data.items():
            for url in urls:
                self.task_queue.put((seq_id, category, url))
                seq_id += 1

    def get_proxy(self):
        if not self.use_proxy or not self.proxies:
            return None
        proxy_str = self.proxies[uuid.uuid4().int % len(self.proxies)]
        ip, port, user, pwd = proxy_str.split(":")
        return {
            "http": f"http://{user}:{pwd}@{ip}:{port}",
            "https": f"http://{user}:{pwd}@{ip}:{port}",
        }

    # ==================== 核心解析 ====================

    def process_response(self, response_text, category, url):
        """
        解析详情页，返回一个字典列表。
        通过 JSON-LD 提取品牌、真实 SKU、变体独立价格。
        """
        try:
            tree = etree.HTML(response_text)

            results = []
            parent_slug = url.split("/")[-2]
            print(url,'3333',parent_slug)

            # ---------- JSON-LD 提取 ----------
            jsonld_products = self._extract_jsonld_products(tree)
            brand = self._get_brand_from_jsonld(jsonld_products)

            # ---------- 标题 ----------
            try:
                name = tree.xpath('//h1/text()')
                name = name[0].strip() if name else ''
            except Exception:
                name = ''

            # ---------- 价格（XPath 兜底，用于 simple 产品无 JSON-LD 时） ----------
            try:
                price_xpath = tree.xpath('//p[contains(@class,"price")]//bdi/text()')
                price_fallback = price_xpath[0].strip().replace('$', '').replace(',', '') if price_xpath else ''
            except Exception:
                price_fallback = ''

            # ---------- 描述（HTML） ----------
            try:
                des = tree.xpath(
                    '//div[contains(@class,"woocommerce-product-details__short-description")]'
                )[0]
                des = etree.tostring(des, encoding='unicode', method='html')
            except Exception:
                des = ''

            # ---------- 图片 ----------
            img_nodes = tree.xpath(
                '//div[contains(@class,"wd-carousel-inner")]//figure/a/img'
            )
            image_urls = []
            for img in img_nodes:
                src = img.get('src')
                if src:
                    image_urls.append(src)

            # ---------- 成分/How To Use（accordion 第一个非 Description 项） ----------
            try:
                ingredients = tree.xpath(
                    '//div[contains(@class,"wd-accordion-item")]'
                )
                if len(ingredients) == 0:
                    ingredients_html = ''
                else:
                    ingredients_html = etree.tostring(ingredients[0], encoding='unicode', method='html')
            except Exception:
                ingredients_html = ''

            # ---------- 判断变体 ----------
            # 优先：JSON-LD 中带 "size" 字条的 Product 条目（每个变体一条）
            variation_entries = [p for p in jsonld_products if p.get("size")]

            if not variation_entries:
                # 兜底：从 data-product_variations 属性提取
                fallback_variations = self._extract_variation_data_fallback(tree)
                if fallback_variations:
                    variation_entries = fallback_variations

            if variation_entries:
                # ===== 变体产品：先输出父产品行（价格为空），再输出各变体行 =====
                all_sizes = []
                for ve in variation_entries:
                    s = ve.get("size", "")
                    if s:
                        all_sizes.append(s)

                # 父产品行
                results.append({
                    "Type": "variable",
                    "SKU": parent_slug,
                    "Name": name,
                    "Description": des,
                    "Summary (product.metafields.c_f.zdy_tabs1)": ingredients_html,
                    "Sale price": "",
                    "Regular price": "",
                    "Attribute 1 name": "size",
                    "Attribute 1 value(s)": ", ".join(all_sizes),
                    "Attribute 2 name": "",
                    "Attribute 2 value(s)": "",
                    "Categories": category,
                    "Tags": "NULL",
                    "Images": ",".join(image_urls),
                    "Parent": "",
                    "brand": brand,
                    "Stock": 1000.00,
                    "is_upload": 0,
                    "url": url
                })

                # 各变体行
                for ve in variation_entries:
                    size = ve.get("size", "")

                    # SKU：优先 JSON-LD 的 sku 字段；兜底用 parent_slug-size
                    sku = ve.get("sku", f"{parent_slug}-{size}")
                    if not sku:
                        sku = f"{parent_slug}-{size}"

                    # 价格：优先 JSON-LD offers；兜底用兜底数据的 price
                    price = self._get_price_from_jsonld(ve)
                    if not price and isinstance(ve, dict):
                        price = ve.get("price", "")

                    results.append({
                        "Type": "variation",
                        "SKU": sku,
                        "Name": name,
                        "Description": des,
                        "Summary (product.metafields.c_f.zdy_tabs1)": ingredients_html,
                        "Sale price": price,
                        "Regular price": price,
                        "Attribute 1 name": "size",
                        "Attribute 1 value(s)": size,
                        "Attribute 2 name": "",
                        "Attribute 2 value(s)": "",
                        "Categories": category,
                        "Tags": "NULL",
                        "Images": ",".join(image_urls),
                        "Parent": parent_slug,
                        "brand": brand,
                        "Stock": 1000.00,
                        "is_upload": 0,
                        "url": url
                    })
            else:
                # ===== Simple 产品 =====
                main_product = jsonld_products[0] if jsonld_products else {}

                # SKU：优先 JSON-LD；兜底用 URL slug
                sku = main_product.get("sku", parent_slug) or parent_slug

                # 价格：优先 JSON-LD；兜底用 XPath
                price = self._get_price_from_jsonld(main_product)
                if not price:
                    price = price_fallback
                # 确保两位小数
                if price:
                    try:
                        price = f"{float(price):.2f}"
                    except (ValueError, TypeError):
                        pass

                results.append({
                    "Type": "simple",
                    "SKU": sku,
                    "Name": name,
                    "Description": des,
                    "Summary (product.metafields.c_f.zdy_tabs1)": ingredients_html,
                    "Sale price": price,
                    "Regular price": price,
                    "Categories": category,
                    "Tags": "NULL",
                    "Images": ",".join(image_urls),
                    "Parent": "",
                    "brand": brand,
                    "Stock": 1000.00,
                    "is_upload": 0,
                    "url": url
                })

            return results

        except Exception as e:
            self.failures.setdefault(category, []).append(url)
            print(f"Error processing {url}: {e}")
            return []

    # ==================== Worker ====================

    def worker(self):
        while True:
            try:
                seq_id, category, url = self.task_queue.get_nowait()
            except:
                break

            rows_to_write = []
            error_type = None

            try:
                response_text = self.fetch(category, url)

                if response_text:
                    cleaned_data = self.process_response(response_text, category, url)
                    if not cleaned_data:
                        error_type = "关键字段为空"
                    else:
                        rows_to_write = cleaned_data
                else:
                    error_type = "请求失败"
                    self.failures.setdefault(category, []).append(url)

                self.result_queue.put((seq_id, rows_to_write))

            except Exception as e:
                error_type = f"任务崩溃 ({e})"
                self.failures.setdefault(category, []).append(url)
                self.result_queue.put((seq_id, []))

            finally:
                with self.lock:
                    self.completed_tasks += 1
                    current = self.completed_tasks
                    total = self.total_tasks

                    if error_type:
                        print(f"[FAILED] {error_type} {current}/{total}: {url}")
                    else:
                        print(f"[PROGRESS] 已完成 {current}/{total}")

                self.task_queue.task_done()

    # ==================== Writer ====================

    def writer_worker(self, fieldnames):
        with open(self.output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            next_seq_to_write = 0
            buffer = {}

            while True:
                item = self.result_queue.get()

                if item is None:
                    break

                seq_id, rows = item

                buffer[seq_id] = rows

                while next_seq_to_write in buffer:
                    current_rows = buffer.pop(next_seq_to_write)

                    if current_rows:
                        writer.writerows(current_rows)

                    next_seq_to_write += 1

                self.result_queue.task_done()

    # ==================== 主流程 ====================

    def run(self):
        self.load_tasks()

        fieldnames = [
            "Type", "SKU", "Name", "Description", "Sale price", "Regular price",
            "Categories", "Tags", "Images", "Parent",
            "Attribute 1 name", "Attribute 1 value(s)",
            "Attribute 2 name", "Attribute 2 value(s)",
            "brand", "Stock", "is_upload",
            "Summary (product.metafields.c_f.zdy_tabs1)", "url"
        ]

        writer_thread = threading.Thread(target=self.writer_worker, args=(fieldnames,))
        writer_thread.start()

        threads = []
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.worker)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.result_queue.put(None)
        writer_thread.join()

        with open(self.fail_file, "w", encoding="utf-8") as f:
            json.dump(self.failures, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    proxies = [
        "173.244.41.44:6228:ohuvqicg:gkfzl265cbwm",
        "23.27.203.244:6979:ohuvqicg:gkfzl265cbwm",
        "198.12.112.249:5260:ohuvqicg:gkfzl265cbwm",
        "31.58.29.76:6042:ohuvqicg:gkfzl265cbwm",
    ]

    crawler = Crawler(
        input_file=r"data/blackgirlsunscreen_detail_url.json",
        output_file=r"data\result.csv",
        fail_file=r"data\fail.json",
        proxies=proxies,
        max_threads=10,
        max_retries=3,
        batch_size=100,
        use_proxy=False
    )
    crawler.run()
