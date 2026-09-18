import json
import csv
import time
import uuid
import re
import threading
from queue import Queue
from curl_cffi import requests
from lxml import etree


class Crawler:
    def __init__(self, input_file, output_file, fail_file, brand,
                 proxies=None, max_threads=10, max_retries=3,
                 batch_size=100, use_proxy=True):
        self.input_file = input_file
        self.output_file = output_file
        self.fail_file = fail_file
        self.brand = brand
        self.proxies = proxies if proxies else []
        self.max_threads = max_threads
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.use_proxy = use_proxy

        self.task_queue = Queue()
        self.result_queue = Queue()
        self.failures = {}
        self.url_category = {}
        self.total_tasks = 0
        self.completed_tasks = 0
        self.lock = threading.Lock()

        # 已经生成的 parent SKU 集合（用于去重）
        self.seen_parents = set()

        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

    # 无效属性值集合（会污染 Color/Size 的文本）
    INVALID_ATTR_VALUES = {
        "", "select", "choose", "option", "out of stock", "sold out",
        "unavailable", "notify me", "coming soon", "discontinued",
        "temporarily unavailable", "backorder", "pre-order", "pre order",
    }

    @staticmethod
    def is_valid_attr_value(value):
        """判断属性值是否合法（非空、非无效值、不含 stock 状态）。"""
        if not value or not isinstance(value, str):
            return False
        val = value.strip().lower()
        if not val:
            return False
        if val in Crawler.INVALID_ATTR_VALUES:
            return False
        if any(bad in val for bad in ["out of stock", "sold out", "unavailable", "notify me"]):
            return False
        return True

    @staticmethod
    def merge_attribute_values(val1, val2):
        """合并两个属性值字符串（| 分隔），去重并保持顺序。"""
        if not val1 and not val2:
            return ""
        if not val1:
            return val2
        if not val2:
            return val1
        parts1 = [p.strip() for p in val1.split("|") if p.strip()]
        parts2 = [p.strip() for p in val2.split("|") if p.strip()]
        merged = []
        for p in parts1 + parts2:
            if p not in merged:
                merged.append(p)
        return "|".join(merged)

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    @staticmethod
    def normalize_image_url(image):
        """将图片地址统一转成完整原图链接，避免 cdn-cgi 参数里的逗号破坏 CSV 分隔。"""
        if not image:
            return ""
        image = image.strip()
        match = re.search(r'(/i/items/[^,\s"\'<>]+?\.(?:jpg|jpeg|png|webp))', image, re.I)
        if match:
            return "https://static.rticoutdoors.com" + match.group(1)
        if image.startswith("//"):
            return "https:" + image
        if image.startswith("/"):
            return "https://static.rticoutdoors.com" + image
        return image

    @staticmethod
    def clean_sku(text):
        """把任意文本转成合法 SKU：只保留字母数字和连字符。"""
        if not text:
            return ""
        text = text.strip()
        # 先把各种空白、斜杠、& 等替换成连字符
        text = re.sub(r'[\s/&\(\)\[\]\{\}\.]+', '-', text)
        # 去掉非字母数字连字符的字符
        text = re.sub(r'[^A-Za-z0-9\-]', '', text)
        # 去掉首尾连字符，合并多个连字符
        text = re.sub(r'-+', '-', text).strip('-')
        return text

    @staticmethod
    def format_price(price_str):
        """统一格式化为保留两位小数的字符串。"""
        if not price_str:
            return ""
        try:
            price = float(str(price_str).replace('$', '').replace(',', '').strip())
            return f"{price:.2f}"
        except (ValueError, TypeError):
            return str(price_str).strip()

    def choose_best_category(self, old_category, new_category):
        """同一商品 URL 出现在多个分类时，保留最合适的分类。"""
        if not old_category:
            return new_category

        def score(category):
            text = category.lower()
            parts = [p.strip() for p in category.split(",") if p.strip()]
            value = len(parts) * 10
            top_categories = [
                "hard coolers", "soft coolers", "drinkware",
                "bags", "gear", "clearance", "custom shop",
            ]
            hit_top_count = sum(1 for top in top_categories if top in text)
            if hit_top_count > 1:
                value -= 1000
            if "shop all" in text:
                value -= 100
            if "clearance" in text:
                value -= 50
            return value

        return new_category if score(new_category) > score(old_category) else old_category

    # ------------------------------------------------------------------
    # 任务加载
    # ------------------------------------------------------------------
    def load_tasks(self):
        with open(self.input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_count = 0
        for category, urls in data.items():
            for url in urls:
                if not url:
                    continue
                raw_count += 1
                old_category = self.url_category.get(url, "")
                self.url_category[url] = self.choose_best_category(old_category, category)

        for url, category in self.url_category.items():
            self.task_queue.put((category, url))

        self.total_tasks = self.task_queue.qsize()
        print(f"[DEDUP] 原始URL数: {raw_count}，去重后请求数: {self.total_tasks}")

    # ------------------------------------------------------------------
    # 网络请求
    # ------------------------------------------------------------------
    def get_proxy(self):
        if not self.use_proxy or not self.proxies:
            return None
        proxy_str = self.proxies[uuid.uuid4().int % len(self.proxies)]
        ip, port, user, pwd = proxy_str.split(":")
        return {
            "http": f"http://{user}:{pwd}@{ip}:{port}",
            "https": f"http://{user}:{pwd}@{ip}:{port}",
        }

    def fetch(self, category, url):
        for attempt in range(self.max_retries):
            try:
                print(url)
                proxy = self.get_proxy()
                response = requests.get(
                    url,
                    headers=self.headers,
                    proxies=proxy,
                    impersonate='chrome120',
                    verify=False,
                    timeout=30
                )
                time.sleep(3)
                return response.text
            except Exception as e:
                print(f"[RETRY {attempt+1}/{self.max_retries}] {url} -> {e}")
                time.sleep(2)
        self.failures.setdefault(category, []).append(url)
        return None

    # ------------------------------------------------------------------
    # 页面解析
    # ------------------------------------------------------------------
    def extract_name(self, page_tree):
        """提取商品名称。"""
        try:
            name = page_tree.xpath(
                '//h1[@class="tw:order-2 tw:mb-1 tw:mt-2 tw:text-left tw:font-body tw:text-2xl tw:font-extrabold tw:uppercase tw:leading-[26px] tw:text-body tw:lg:order-1 tw:lg:mb-3 tw:lg:mt-0"]/text()'
            )[0].strip()
            print(f"[NAME] {name}")
            return name
        except Exception:
            print('[ERROR] 该页面为非商品页,缺失商品名字')
            return None

    def extract_price(self, page_tree):
        """提取原价（优先取 line-through 的划线价，避免取到折后价）。"""
        try:
            # 1. 优先取 line-through 的原价
            line_through_prices = page_tree.xpath(
                '//b[contains(@class,"line-through")]/text()'
            )
            if line_through_prices:
                price = line_through_prices[0].strip().replace('$', '').replace(',', '')
                print(f"[PRICE] original={price}")
                return self.format_price(price)

            # 2. 如果没有 line-through，取页面上所有价格中的最大值（避免取到折后价）
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
                    max_price = max(prices)
                    print(f"[PRICE] max={max_price}")
                    return self.format_price(max_price)

            print('[ERROR] 该页面为非商品页,缺失价格')
            return None
        except Exception:
            print('[ERROR] 该页面为非商品页,缺失价格')
            return None

    def extract_description(self, page_tree):
        """提取描述。"""
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
                return meta[0]
            return ''
        except Exception as e:
            print(f'[ERROR] 该产品缺失描述')
            return ''

    def extract_short_description(self, page_tree):
        """提取简短描述。"""
        try:
            node = page_tree.xpath('//div[@class="tw:relative tw:mx-auto tw:lg:mr-0 tw:lg:px-9 tw:max-w-md"]//div[@class="markdown"]')[0]
            return etree.tostring(node).decode('utf-8')
        except Exception:
            return ''

    def extract_details(self, page_tree):
        """提取详情。"""
        try:
            containers = page_tree.xpath('//div[@class="tw:animate-[fadeInLeftFull_0.8s] tw:md:min-h-[200px] tw:lg:min-h-[270px]"]')
            return ''.join(etree.tostring(d).decode('utf-8') for d in containers)
        except Exception:
            return ""

    def extract_images(self, page_tree):
        """提取所有商品图片。"""
        image_url_list = []
        try:
            image_container = page_tree.xpath(
                '//div[@class="tw:relative tw:flex tw:justify-center tw:overflow-hidden tw:cursor-zoom-in tw:bg-position-50-50 tw:hover:bg-no-repeat tw:hover:[background-image:var(--bg-image)] tw:max-w-[600px] tw:max-h-[600px]"]/img/@src'
            )
            for image in image_container:
                image_url = self.normalize_image_url(image)
                if image_url and image_url not in image_url_list:
                    image_url_list.append(image_url)
            print(f"[IMAGES] {len(image_url_list)} 张")
        except Exception:
            print('[ERROR] 没有商品图片')
        return image_url_list

    def extract_sizes(self, page_tree):
        """提取所有 Size 选项。"""
        sizes = []
        try:
            # 方式1: 页面上的 size 标签（如 <i class="...font-bold...">L</i>）
            size_nodes = page_tree.xpath(
                '//div[contains(@class,"tw:flex") and contains(@class,"tw:items-center") and contains(@class,"tw:gap-2")]'
                '//i[contains(@class,"font-italic") and contains(@class,"font-bold")]/text()'
            )
            for s in size_nodes:
                val = s.strip()
                if self.is_valid_attr_value(val) and val not in sizes:
                    sizes.append(val)

            # 方式2: 从 URL 链接参数中提取 size（补充，不只作为备选）
            size_links = page_tree.xpath('//a[contains(@href,"size=")]/@href')
            for href in size_links:
                m = re.search(r'size=([^&]+)', href)
                if m:
                    val = m.group(1).replace('-', ' ').strip()
                    if self.is_valid_attr_value(val) and val not in sizes:
                        sizes.append(val)

            if sizes:
                print(f"[SIZES] {sizes}")
        except Exception:
            pass
        return sizes

    def extract_colors(self, page_tree):
        """提取所有 Color 选项。"""
        colors = []
        try:
            # 方式1: color swatch 的 title / data-swatch 属性（帽子等）
            swatch_colors = page_tree.xpath('//a[@data-swatch]/@title')
            for c in swatch_colors:
                val = c.strip()
                if self.is_valid_attr_value(val) and val not in colors:
                    colors.append(val)

            # 方式2: 从 URL 链接参数中提取 color（T-Shirt 等，补充）
            color_links = page_tree.xpath('//a[contains(@href,"color=")]/@href')
            for href in color_links:
                m = re.search(r'color=([^&]+)', href)
                if m:
                    val = m.group(1).replace('-', ' ').strip()
                    if self.is_valid_attr_value(val) and val not in colors:
                        colors.append(val)

            # 方式3: 旧版结构（兼容）
            if not colors:
                color_nodes = page_tree.xpath(
                    '//i[contains(@class,"font-italic") and contains(@class,"font-bold")]/span/text()'
                )
                for c in color_nodes:
                    val = c.strip()
                    if self.is_valid_attr_value(val) and val not in colors:
                        colors.append(val)

            if colors:
                print(f"[COLORS] {colors}")
        except Exception:
            pass
        return colors

    @staticmethod
    def normalize_color(color):
        """标准化颜色字符串用于比较：小写、移除 & / - 等符号、合并空格。"""
        if not color:
            return ""
        c = color.lower()
        c = c.replace('&', ' ').replace('/', ' ').replace('-', ' ')
        c = re.sub(r'[^a-z0-9\s]', ' ', c)
        c = re.sub(r'\s+', ' ', c).strip()
        return c

    def extract_current_color(self, page_tree, url):
        """确定当前页面显示的是哪个颜色的变体。

        每个 URL 对应一个颜色，页面图片就是该颜色的图片。
        优先从 URL 参数提取（用户明确指定了颜色），
        其次从图片 alt 文本提取。
        """
        # 方式1: 从 URL 参数中提取 color（用户明确指定了想要的颜色）
        m = re.search(r'[?&]color=([^&]+)', url)
        if m:
            color = m.group(1).replace('-', ' ').strip()
            return color

        # 方式2: 从图片 alt 文本中提取颜色名（与 swatch title 格式一致）
        # alt 格式: "52 QT Ultra-Light Wheeled Cooler, Cool Grey & Navy Image"
        alt_texts = page_tree.xpath('//div[contains(@class,"embla")]//img/@alt')
        if not alt_texts:
            alt_texts = page_tree.xpath('//img[contains(@alt,"Image")]/@alt')
        for alt in alt_texts:
            m = re.search(r',\s*([^,]+?)\s+Image', alt)
            if m:
                return m.group(1).strip()

        return None

    # ------------------------------------------------------------------
    # 核心：组装数据
    # ------------------------------------------------------------------
    def process_response(self, response_text, category, url):
        page_tree = etree.HTML(response_text)

        # 1. 名称（关键字段，缺失则放弃）
        name = self.extract_name(page_tree)
        if not name:
            return []

        # 2. 价格（关键字段，缺失则放弃）
        price = self.extract_price(page_tree)
        if not price:
            return []

        # 3. 描述等辅助字段
        description = self.extract_description(page_tree)
        short_description = self.extract_short_description(page_tree)
        details = self.extract_details(page_tree)
        image_url_list = self.extract_images(page_tree)
        if not image_url_list:
            return []

        # 4. 提取 size / color（所有选项）
        sizes = self.extract_sizes(page_tree)
        colors = self.extract_colors(page_tree)

        # 4.5 确定当前页面显示的颜色（用于图片-颜色对应）
        current_color = self.extract_current_color(page_tree, url)
        if current_color:
            print(f"[CURRENT_COLOR] {current_color}")

        # 5. 生成合法 SKU 前缀（Parent SKU）
        parent_sku = self.clean_sku(name)
        if not parent_sku:
            parent_sku = self.clean_sku(re.sub(r'[^A-Za-z0-9]', '', name)) or "product"

        results = []
        has_variants = bool(sizes or colors)

        # ================================================================
        # 生成 Parent 行（Variable 或 Simple）
        # ================================================================
        parent_row = {
            "Type": "variable" if has_variants else "simple",
            "SKU": parent_sku,
            "Name": name,
            "Description": description,
            "Details": details,
            "Short Description": short_description,
            "Sale price": "" if has_variants else price,
            "Regular price": "" if has_variants else price,
            "Categories": category,
            "Tags": "NULL",
            "Images": ",".join(image_url_list),
            "Parent": "",
            "Brand": self.brand,
            "Attribute 1 name": "",
            "Attribute 1 value(s)": "",
            "Attribute 2 name": "",
            "Attribute 2 value(s)": "",
            "Attribute 3 name": "",
            "Attribute 3 value(s)": "",
            "Product_Description (product.metafields.c_f.Product_Description)": description,
            "Stock": "1000.00",
            "is_upload": 0,
        }

        # 只在有变体时给 Parent 填充 Attribute（值用 | 连接所有选项）
        if has_variants:
            if colors and sizes:
                parent_row["Attribute 1 name"] = "Color"
                parent_row["Attribute 1 value(s)"] = "|".join(colors)
                parent_row["Attribute 2 name"] = "Size"
                parent_row["Attribute 2 value(s)"] = "|".join(sizes)
            elif colors:
                parent_row["Attribute 1 name"] = "Color"
                parent_row["Attribute 1 value(s)"] = "|".join(colors)
            elif sizes:
                parent_row["Attribute 1 name"] = "Size"
                parent_row["Attribute 1 value(s)"] = "|".join(sizes)

        results.append(parent_row)

        # ================================================================
        # 生成 Variation 行
        # ================================================================
        if has_variants:
            # 构建 size × color 的笛卡尔积；如果某一维为空，用 [""] 占位
            size_list = sizes if sizes else [""]
            color_list = colors if colors else [""]

            for size in size_list:
                for color in color_list:
                    # Variation SKU：parent-sku + size + color
                    sku_parts = [parent_sku]
                    if size:
                        sku_parts.append(self.clean_sku(size))
                    if color:
                        sku_parts.append(self.clean_sku(color))
                    var_sku = "-".join(sku_parts)

                    var_row = {
                        "Type": "variation",
                        "SKU": var_sku,
                        "Name": name,          # 名字后面绝对不加属性
                        "Description": description,
                        "Details": details,
                        "Short Description": short_description,
                        "Sale price": price,
                        "Regular price": price,
                        "Categories": category,
                        "Tags": "NULL",
                        "Images": "",          # 图片下方单独赋值
                        "Parent": parent_sku,   # Parent 就是纯产品名，不带属性
                        "Brand": self.brand,
                        "Attribute 1 name": "",
                        "Attribute 1 value(s)": "",
                        "Attribute 2 name": "",
                        "Attribute 2 value(s)": "",
                        "Attribute 3 name": "",
                        "Attribute 3 value(s)": "",
                        "Product_Description (product.metafields.c_f.Product_Description)": description,
                        "Stock": "1000.00",
                        "is_upload": 0,
                    }

                    # 图片-颜色对应逻辑：
                    # 只有当前页面的颜色与 variation 颜色匹配时，才赋值图片
                    # 其他颜色的 variation 图片留空，由各自对应的 URL 填充
                    if colors and current_color:
                        if self.normalize_color(color) == self.normalize_color(current_color):
                            var_row["Images"] = image_url_list[0] if image_url_list else ""
                        else:
                            var_row["Images"] = ""
                    elif not colors:
                        # 没有颜色变体，所有 variation 用同一张图
                        var_row["Images"] = image_url_list[0] if image_url_list else ""
                    else:
                        # 有颜色但无法确定当前颜色，用第一张图兜底
                        var_row["Images"] = image_url_list[0] if image_url_list else ""

                    # 根据 color/size 存在情况正确填入 Attribute
                    if colors and sizes:
                        var_row["Attribute 1 name"] = "Color"
                        var_row["Attribute 1 value(s)"] = color
                        var_row["Attribute 2 name"] = "Size"
                        var_row["Attribute 2 value(s)"] = size
                    elif colors:
                        var_row["Attribute 1 name"] = "Color"
                        var_row["Attribute 1 value(s)"] = color
                    elif sizes:
                        var_row["Attribute 1 name"] = "Size"
                        var_row["Attribute 1 value(s)"] = size

                    results.append(var_row)

        return results

    # ------------------------------------------------------------------
    # 工作线程
    # ------------------------------------------------------------------
    def worker(self):
        while True:
            try:
                category, url = self.task_queue.get_nowait()
            except Exception:
                break

            response_text = self.fetch(category, url)
            if response_text:
                cleaned_data = self.process_response(response_text, category, url)
                if not cleaned_data:
                    with self.lock:
                        print(f"[FAILED] 关键字段为空: {url} | 分类: {category}")
                else:
                    for row in cleaned_data:
                        self.result_queue.put(row)
            else:
                with self.lock:
                    print(f"[FAILED] 请求失败: {url}")
                self.failures.setdefault(category, []).append(url)

            with self.lock:
                self.completed_tasks += 1
                print(f"[PROGRESS] 已完成 {self.completed_tasks}/{self.total_tasks}")

            self.task_queue.task_done()

    def _merge_row_attributes(self, target, source):
        """将 source 的 Attribute values 合并到 target 中（按 name 匹配）。"""
        for i in range(1, 4):
            name_key = f"Attribute {i} name"
            val_key = f"Attribute {i} value(s)"
            t_name = target.get(name_key, "")
            s_name = source.get(name_key, "")
            if t_name and t_name == s_name:
                merged = self.merge_attribute_values(
                    target.get(val_key, ""),
                    source.get(val_key, "")
                )
                target[val_key] = merged

    def writer_worker(self, fieldnames):
        with open(self.output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            sku_rows = {}
            while True:
                result = self.result_queue.get()
                if result is None:
                    if sku_rows:
                        writer.writerows(sku_rows.values())
                    break

                sku = result.get("SKU", "")
                if not sku:
                    self.result_queue.task_done()
                    continue

                old_row = sku_rows.get(sku)
                if old_row is None:
                    sku_rows[sku] = result
                else:
                    # 如果是相同 SKU 的 Parent 行（variable），合并 Attribute values
                    if old_row.get("Type") == "variable" and result.get("Type") == "variable":
                        self._merge_row_attributes(old_row, result)
                        # 保留更优的分类
                        old_category = old_row.get("Categories", "")
                        new_category = result.get("Categories", "")
                        best_category = self.choose_best_category(old_category, new_category)
                        if best_category == new_category:
                            old_row["Categories"] = new_category
                        # 保留更完整的图片列表（取并集）
                        old_images = set(old_row.get("Images", "").split(",")) if old_row.get("Images") else set()
                        new_images = set(result.get("Images", "").split(",")) if result.get("Images") else set()
                        merged_images = old_images | new_images
                        old_row["Images"] = ",".join([img for img in merged_images if img.strip()])
                    else:
                        # 对 Variation 行：优先保留有图片的那行
                        if old_row.get("Type") == "variation" and result.get("Type") == "variation":
                            old_img = old_row.get("Images", "")
                            new_img = result.get("Images", "")
                            if new_img and not old_img:
                                # 新行有图片，旧行没有 → 用新行
                                sku_rows[sku] = result
                            elif old_img and not new_img:
                                # 旧行有图片，新行没有 → 保留旧行
                                pass
                            else:
                                # 都有或都没有 → 按分类优劣选择
                                old_category = old_row.get("Categories", "")
                                new_category = result.get("Categories", "")
                                best_category = self.choose_best_category(old_category, new_category)
                                if best_category == new_category:
                                    sku_rows[sku] = result
                        else:
                            # simple 行或其他情况：保留最优分类
                            old_category = old_row.get("Categories", "")
                            new_category = result.get("Categories", "")
                            best_category = self.choose_best_category(old_category, new_category)
                            if best_category == new_category:
                                sku_rows[sku] = result

                self.result_queue.task_done()

    # ------------------------------------------------------------------
    # 运行入口
    # ------------------------------------------------------------------
    def run(self):
        self.load_tasks()

        fieldnames = [
            "Type", "SKU", "Name", "Description", "Details", "Short Description",
            "Sale price", "Regular price", "Categories", "Tags", "Images", "Parent",
            "Attribute 1 name", "Attribute 1 value(s)",
            "Attribute 2 name", "Attribute 2 value(s)",
            "Attribute 3 name", "Attribute 3 value(s)",
            "Brand", "Product_Description (product.metafields.c_f.Product_Description)",
            "Stock", "is_upload"
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
        "173.0.10.200:6376:ohuvqicg:gkfzl265cbwm",
        "46.202.227.245:6239:ohuvqicg:gkfzl265cbwm",
        "23.27.91.235:6314:ohuvqicg:gkfzl265cbwm",
        "45.43.167.239:6421:ohuvqicg:gkfzl265cbwm",
        "179.61.166.117:6540:ohuvqicg:gkfzl265cbwm",
        "184.174.25.226:6115:ohuvqicg:gkfzl265cbwm",
        "184.174.28.61:5076:ohuvqicg:gkfzl265cbwm",
        "45.61.96.40:6020:ohuvqicg:gkfzl265cbwm",
        "154.6.83.62:6533:ohuvqicg:gkfzl265cbwm",
        "184.174.28.206:5221:ohuvqicg:gkfzl265cbwm",
        "166.88.224.206:6104:ohuvqicg:gkfzl265cbwm",
        "207.244.219.192:6448:ohuvqicg:gkfzl265cbwm",
        "185.202.175.57:6845:ohuvqicg:gkfzl265cbwm",
        "154.6.129.12:5482:ohuvqicg:gkfzl265cbwm",
        "136.0.184.241:6662:ohuvqicg:gkfzl265cbwm",
        "184.174.43.148:6688:ohuvqicg:gkfzl265cbwm",
        "23.229.125.243:5512:ohuvqicg:gkfzl265cbwm",
        "142.147.242.106:6085:ohuvqicg:gkfzl265cbwm",
        "45.61.98.26:5710:ohuvqicg:gkfzl265cbwm",
        "2.57.20.180:6172:ohuvqicg:gkfzl265cbwm",
        "192.186.185.69:6628:ohuvqicg:gkfzl265cbwm",
        "198.23.239.110:6516:ohuvqicg:gkfzl265cbwm",
        "216.74.115.115:6709:ohuvqicg:gkfzl265cbwm",
        "173.245.88.40:5343:ohuvqicg:gkfzl265cbwm",
        "23.27.210.207:6577:ohuvqicg:gkfzl265cbwm",
        "173.211.69.63:6656:ohuvqicg:gkfzl265cbwm",
        "191.101.11.117:6515:ohuvqicg:gkfzl265cbwm",
        "104.239.80.5:5583:ohuvqicg:gkfzl265cbwm",
        "161.123.5.152:5201:ohuvqicg:gkfzl265cbwm",
        "198.46.241.137:6672:ohuvqicg:gkfzl265cbwm",
        "184.174.27.73:6296:ohuvqicg:gkfzl265cbwm",
        "23.26.95.229:5711:ohuvqicg:gkfzl265cbwm",
        "46.202.59.207:5698:ohuvqicg:gkfzl265cbwm",
        "38.153.148.132:5403:ohuvqicg:gkfzl265cbwm",
        "142.111.48.228:7005:ohuvqicg:gkfzl265cbwm",
        "173.211.69.148:6741:ohuvqicg:gkfzl265cbwm",
        "38.153.152.53:9403:ohuvqicg:gkfzl265cbwm",
        "192.186.185.201:6760:ohuvqicg:gkfzl265cbwm",
        "23.27.203.41:6776:ohuvqicg:gkfzl265cbwm",
        "45.61.96.137:6117:ohuvqicg:gkfzl265cbwm",
        "216.74.80.40:6612:ohuvqicg:gkfzl265cbwm",
        "38.154.224.73:6614:ohuvqicg:gkfzl265cbwm",
        "154.6.115.232:6701:ohuvqicg:gkfzl265cbwm",
        "45.41.178.1:6222:ohuvqicg:gkfzl265cbwm",
        "104.239.78.100:6045:ohuvqicg:gkfzl265cbwm",
        "192.227.131.112:6696:ohuvqicg:gkfzl265cbwm",
        "206.232.103.220:6377:ohuvqicg:gkfzl265cbwm",
        "23.95.255.164:6748:ohuvqicg:gkfzl265cbwm",
        "174.140.254.151:6742:ohuvqicg:gkfzl265cbwm",
        "173.211.69.142:6735:ohuvqicg:gkfzl265cbwm",
        "172.245.158.222:6175:ohuvqicg:gkfzl265cbwm",
        "67.227.36.80:6122:ohuvqicg:gkfzl265cbwm",
        "45.39.4.221:5646:ohuvqicg:gkfzl265cbwm",
        "142.111.131.225:6303:ohuvqicg:gkfzl265cbwm",
        "173.211.0.91:6584:ohuvqicg:gkfzl265cbwm",
        "192.186.172.35:9035:ohuvqicg:gkfzl265cbwm"
    ]

    crawler = Crawler(
        input_file=r"/8-10到8-15/rticoutdoors_他人_更新数据/rticoutdoors_all.json",
        output_file=r"/8-10到8-15/rticoutdoors_他人_更新数据/rticoutdoors1.csv",
        fail_file=r"/8-10到8-15/rticoutdoors_他人_更新数据/fail1.json",
        brand="rticoutdoors",          # brand 现在作为参数传入
        proxies=proxies,
        max_threads=8,
        max_retries=3,
        batch_size=100,
        use_proxy=False
    )
    crawler.run()
