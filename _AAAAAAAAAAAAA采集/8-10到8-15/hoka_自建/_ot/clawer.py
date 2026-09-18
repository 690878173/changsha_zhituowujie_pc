import csv
import json
import re
import copy
import time
import random
import os
import threading
import html as html_module
from queue import Queue
from urllib.parse import urlparse, parse_qs
from lxml import etree
from DrissionPage import ChromiumPage, ChromiumOptions


class HokaCrawler:
    """
    第三步：根据产品详情页 URL 列表，爬取产品详情并输出 CSV。
    输入 JSON 格式：{"分类路径": ["https://www.hoka.com/en/us/...", ...]}
    输出 CSV：包含父类（variable）+ 子类（variation）或 simple 类型的产品行。

    使用 DrissionPage 真实浏览器绕过 DataDome 反爬保护。
    单线程运行（浏览器实例不支持多线程）。

    产品类型逻辑：
    - URL 带 dwvar_{id}_color= 参数 → 生成父类 variable + 子类 variation 两行
    - URL 无 dwvar 参数 → 生成一行 simple

    URL 缓存机制：
    - 缓存键为完整 URL（含颜色参数）
    - 同一 URL 只请求一次，产品数据复制到所有关联分类
    """

    # 自定义字段名称（匹配 HOKA 网站实际分区名称）
    # 格式: DisplayName (product.metafields.c_f.InternalName)
    FIELD_TECH_SPECS = "Tech Specs (product.metafields.c_f.Tech_Specs)"
    FIELD_FEATURES = "Features (product.metafields.c_f.Features)"

    def __init__(
        self,
        input_file,
        output_file,
        fail_file,
        price_data_file=None,
        max_retries=3,
        timeout=30,
    ):
        self.input_file = input_file
        self.output_file = output_file
        self.fail_file = fail_file
        self.price_data_file = price_data_file

        self.max_retries = max_retries
        self.timeout = timeout

        self.task_queue = Queue()
        self.result_queue = Queue()

        self.total_tasks = 0
        self.completed_tasks = 0

        # URL 缓存：{url: rows}，同一个 URL 只请求一次
        self.url_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

        # 列表页价格数据
        self.price_data = {}
        if price_data_file:
            try:
                with open(price_data_file, "r", encoding="utf-8") as f:
                    self.price_data = json.load(f)
                print(f"[PRICE] 已加载 {len(self.price_data)} 条价格数据 from {price_data_file}")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[PRICE] 价格数据文件加载失败: {e}")

        self.base_url = "https://www.hoka.com"
        self.page = None
        self.failures = {}

    # -------------------- 基础工具 --------------------
    @staticmethod
    def _clean_text(s):
        return re.sub(r"\s+", " ", (s or "")).strip()

    @staticmethod
    def _format_price(price_val):
        """价格格式化为两位小数，不带货币符号。例如 165.0 -> '165.00'"""
        if price_val is None or price_val == "":
            return ""
        try:
            return f"{float(price_val):.2f}"
        except (ValueError, TypeError):
            return ""

    @staticmethod
    def _parse_price(text):
        """从文本中解析价格数值。"""
        if not text:
            return None
        cleaned = str(text).replace(",", "").replace("$", "").replace("USD", "").strip()
        m = re.search(r"(\d+(?:\.\d+)?)", cleaned)
        return float(m.group(1)) if m else None

    def _record_failure(self, category, url, reason):
        self.failures.setdefault(category, []).append({"url": url, "reason": reason})

    # -------------------- 浏览器初始化 --------------------
    def _init_browser(self):
        """启动 Chrome 浏览器并访问 HOKA 首页以通过 DataDome 验证"""
        co = ChromiumOptions()
        co.headless(False)
        co.set_argument('--no-first-run')
        co.set_argument('--no-default-browser-check')
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--disable-features=IsolateOrigins,site-per-process')
        co.set_argument('--disable-site-isolation-trials')
        co.set_argument('--disable-features=BlockInsecurePrivateNetworkRequests')

        self.page = ChromiumPage(co)
        print("[INFO] Chrome 浏览器启动中...")

        # 访问 HOKA 首页，触发 DataDome JS 验证并获取 cookie
        self.page.get("https://www.hoka.com/en/us/")
        time.sleep(3)

        # 验证是否通过 DataDome
        html = self.page.html
        if self._is_datadome_blocked(html):
            print("[INFO] 等待 DataDome 验证完成...")
            time.sleep(5)
            html = self.page.html
            if self._is_datadome_blocked(html):
                print("[警告] DataDome 验证可能未通过，继续尝试...")

        print("[INFO] 浏览器启动成功，已通过 DataDome 验证")

    def _is_datadome_blocked(self, text):
        """
        检查响应是否为 DataDome 挑战页。
        """
        if not text:
            return True
        text_lower = text.lower()
        if "datadome" in text_lower:
            return True
        if "captcha-delivery" in text_lower:
            return True
        if len(text) < 3000 and "var dd=" in text_lower:
            return True
        if len(text) < 3000 and "hoka.com" in text_lower and "challenge" in text_lower:
            return True
        return False

    # -------------------- 任务加载 --------------------
    def load_tasks(self):
        """
        读取全量 JSON，保留所有分类关系。
        同一个产品 URL 可能出现在多个分类中，全部入队。
        在处理中通过 URL 缓存实现请求去重。
        """
        with open(self.input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        seq_id = 0
        seen = set()

        for category, urls in data.items():
            if not isinstance(urls, list):
                continue
            for url in urls:
                if not isinstance(url, str) or not url.strip():
                    continue
                key = (category, url.strip())
                if key in seen:
                    continue
                seen.add(key)
                self.task_queue.put((seq_id, category, url.strip()))
                seq_id += 1

        self.total_tasks = seq_id

    # -------------------- URL 解析工具 --------------------
    @staticmethod
    def _extract_id_from_url(url):
        """
        从 HOKA URL 中提取 master_id 和 color_code。
        URL 格式: /en/us/{category}/{product-slug}/{master-id}.html?dwvar_{master-id}_color={color-code}
        返回: (master_id, color_code)
        """
        parsed = urlparse(url)
        path = parsed.path

        filename = path.rstrip("/").split("/")[-1]
        master_id = ""
        if filename.endswith(".html"):
            master_id = filename[:-5]
        elif filename:
            master_id = filename

        qs = parse_qs(parsed.query)
        color_code = ""
        for key, val in qs.items():
            if key.startswith("dwvar_") and key.endswith("_color"):
                if val:
                    color_code = val[0]
                break

        return master_id, color_code

    def _lookup_price_data(self, url):
        """
        通过 URL 查找列表页价格数据，尝试多种匹配策略。
        返回: price_info dict 或 None
        """
        if not self.price_data:
            return None

        # 策略 1: 精确匹配
        price_info = self.price_data.get(url)
        if price_info:
            return price_info

        # 策略 2: 去掉尾部斜杠后匹配
        if url.endswith("/"):
            price_info = self.price_data.get(url.rstrip("/"))
            if price_info:
                return price_info

        # 策略 3: 添加尾部斜杠后匹配
        price_info = self.price_data.get(url + "/")
        if price_info:
            return price_info

        # 策略 4: 去掉查询参数后匹配（用于 simple 产品）
        parsed = urlparse(url)
        url_no_query = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        price_info = self.price_data.get(url_no_query)
        if price_info:
            return price_info

        return None

    @staticmethod
    def _lookup_color_name(color_code, all_colors):
        """
        从 all_color_images 中查找颜色名称。
        如果找不到，使用 color_code 作为回退值（确保属性值不为空）。

        :param color_code: 颜色代码（如 "WHT"）
        :param all_colors: all_color_images 列表
        :return: 颜色名称字符串
        """
        if not color_code:
            return ""

        # 策略 1: 从 all_color_images 中查找
        if isinstance(all_colors, list):
            for c in all_colors:
                if isinstance(c, dict) and c.get("code", "").upper() == color_code.upper():
                    name = c.get("name", "")
                    if name:
                        return name

        # 策略 2: 使用 color_code 作为回退值（确保属性值不为空）
        return color_code

    # -------------------- 产品详情页请求 --------------------
    def fetch_product_page(self, url):
        """
        使用浏览器导航到产品详情页并返回 HTML。
        若被 DataDome 拦截，等待 CAPTCHA 验证。

        :param url: 产品详情页 URL
        :return: (html_text, error)  成功时 error 为 None
        """
        for attempt in range(self.max_retries):
            try:
                self.page.get(url)
                time.sleep(3)

                # 获取完整 DOM HTML（包含动态加载的内容）
                html = self.page.run_js(
                    "return document.documentElement.outerHTML;"
                )
                if not html:
                    html = self.page.html

                if not html or len(html) < 500:
                    # 可能正在加载，等待更长时间
                    time.sleep(3)
                    html = self.page.run_js(
                        "return document.documentElement.outerHTML;"
                    )
                    if not html:
                        html = self.page.html

                # 检查 DataDome 拦截
                if self._is_datadome_blocked(html):
                    print(f"[RETRY] DataDome 拦截，等待验证 "
                          f"({attempt + 1}/{self.max_retries}): {url}")
                    # 等待 DataDome 自动通过或用户手动验证
                    for wait_i in range(15):
                        time.sleep(3)
                        html = self.page.run_js(
                            "return document.documentElement.outerHTML;"
                        )
                        if not html:
                            html = self.page.html
                        if html and not self._is_datadome_blocked(html) and len(html) > 5000:
                            return html, None
                        if wait_i % 5 == 0:
                            print(f"  等待 DataDome 验证... ({wait_i * 3}s)")

                    # 最后一次尝试
                    if attempt < self.max_retries - 1:
                        time.sleep(random.uniform(3, 6))
                        continue
                    return None, "DataDome 拦截（未通过验证）"

                return html, None

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait = random.uniform(2, 4) * (attempt + 1)
                    print(f"[RETRY] 请求异常: {e}，等待 {wait:.1f}s "
                          f"后重试 ({attempt + 1}/{self.max_retries})")
                    time.sleep(wait)
                else:
                    return None, f"请求异常: {e}"

        return None, "达到最大重试次数"

    # -------------------- 详情页内容提取 --------------------
    @staticmethod
    def _extract_description_from_html(tree, html_text):
        """
        从产品详情页 HTML 中提取产品描述。
        保留原始 HTML 标签。

        策略:
        1. SFCC JavaScript 中的 longDescription
        2. JSON-LD 结构化数据中的 description
        3. meta og:description
        4. meta name="description"
        5. 页面中的产品描述区域
        """
        # 策略 1: SFCC JavaScript 中的 longDescription（最可靠，保留 HTML）
        desc_patterns = [
            r'"longDescription"\s*:\s*"((?:[^"\\]|\\.)*)"',
            r'"productDescription"\s*:\s*"((?:[^"\\]|\\.)*)"',
        ]
        for pattern in desc_patterns:
            match = re.search(pattern, html_text)
            if match:
                desc = match.group(1)
                # 反转义 JSON 字符串
                desc = desc.replace("\\n", "\n").replace('\\"', '"').replace("\\/", "/")
                desc = html_module.unescape(desc).strip()
                if len(desc) > 20:
                    return desc

        # 策略 2: JSON-LD 结构化数据
        ld_scripts = tree.xpath("//script[@type='application/ld+json']/text()")
        for script_text in ld_scripts:
            try:
                data = json.loads(script_text)
                if isinstance(data, dict):
                    desc = data.get("description", "")
                    if desc and len(desc) > 20:
                        return html_module.unescape(desc).strip()
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            desc = item.get("description", "")
                            if desc and len(desc) > 20:
                                return html_module.unescape(desc).strip()
            except (json.JSONDecodeError, TypeError):
                continue

        # 策略 3: meta property="og:description"
        og_desc = tree.xpath("//meta[@property='og:description']/@content")
        if og_desc and len(og_desc[0]) > 20:
            return html_module.unescape(og_desc[0]).strip()

        # 策略 4: meta name="description"
        meta_desc = tree.xpath("//meta[@name='description']/@content")
        if meta_desc and len(meta_desc[0]) > 20:
            return html_module.unescape(meta_desc[0]).strip()

        # 策略 5: 产品描述区域
        desc_selectors = [
            "//div[contains(@class, 'product-description')]",
            "//div[contains(@class, 'product-details-description')]",
            "//div[contains(@class, 'description-content')]",
            "//div[contains(@id, 'description')]",
            "//div[contains(@class, 'product-detail-description')]",
            "//div[contains(@class, 'collapsible-content')]",
            "//div[contains(@class, 'tab-content')]",
        ]
        for selector in desc_selectors:
            elements = tree.xpath(selector)
            for elem in elements:
                inner_html = etree.tostring(elem, encoding="unicode", method="html")
                text = "".join(elem.itertext()).strip()
                if text and len(text) > 30:
                    return inner_html

        return ""

    @staticmethod
    def _extract_tech_specs_from_html(tree, html_text):
        """
        从详情页 HTML 中提取 Tech Specs（规格参数）。
        HOKA 页面的 "Tech Specs" / "The Details" 区域包含：
        - Weight（重量）
        - Heel-To-Toe Drop（落差）
        - 其他规格参数

        保留 HTML 标签。
        """
        specs_parts = []

        # 策略 1: 查找 "Tech Specs" 标题后的内容
        tech_specs_selectors = [
            "//h2[contains(text(), 'Tech Specs')]/following-sibling::div",
            "//h3[contains(text(), 'Tech Specs')]/following-sibling::div",
            "//h4[contains(text(), 'Tech Specs')]/following-sibling::div",
            "//h2[contains(text(), 'Tech Specs')]/parent::div//following-sibling::div[1]",
            "//h3[contains(text(), 'Tech Specs')]/parent::div//following-sibling::div[1]",
            "//*[contains(@class, 'tech-specs')]",
            "//*[contains(@class, 'techspecs')]",
            "//*[contains(@class, 'product-specs')]",
        ]
        for selector in tech_specs_selectors:
            elements = tree.xpath(selector)
            for elem in elements:
                inner_html = etree.tostring(elem, encoding="unicode", method="html")
                text = "".join(elem.itertext()).strip()
                if text and len(text) > 10:
                    specs_parts.append(inner_html)
                    break
            if specs_parts:
                break

        # 策略 2: 查找 "The Details" / "Specifications" 标题后的规格列表
        if not specs_parts:
            details_selectors = [
                "//h2[contains(text(), 'The Details')]/following-sibling::div",
                "//h3[contains(text(), 'The Details')]/following-sibling::div",
                "//h4[contains(text(), 'The Details')]/following-sibling::div",
                "//h2[contains(text(), 'Specifications')]/following-sibling::div",
                "//h3[contains(text(), 'Specifications')]/following-sibling::div",
                "//h2[contains(text(), 'The Details')]/parent::div//following-sibling::div[1]",
                "//h3[contains(text(), 'The Details')]/parent::div//following-sibling::div[1]",
            ]
            for selector in details_selectors:
                elements = tree.xpath(selector)
                for elem in elements:
                    inner_html = etree.tostring(elem, encoding="unicode", method="html")
                    text = "".join(elem.itertext()).strip()
                    if text and len(text) > 10:
                        specs_parts.append(inner_html)
                        break
                if specs_parts:
                    break

        # 策略 3: 查找包含规格关键词的 dt/dd 对或 li 列表
        if not specs_parts:
            spec_labels = [
                "Weight", "Drop", "Heel Height", "Forefoot Height",
                "Stack Height", "Heel-To-Toe Drop", "Offset",
                "Upper", "Outsole", "Midsole",
            ]
            found_specs = []

            # 查找 dt/dd 对
            for label in spec_labels:
                dt_elems = tree.xpath(f"//dt[contains(text(), '{label}')]")
                for dt in dt_elems:
                    dd = dt.xpath("./following-sibling::dd[1]")
                    if dd:
                        dt_text = "".join(dt.itertext()).strip()
                        dd_text = "".join(dd[0].itertext()).strip()
                        if dd_text:
                            found_specs.append(f"<p>{dt_text}: {dd_text}</p>")

            # 查找 li 元素
            if not found_specs:
                for label in spec_labels:
                    li_elems = tree.xpath(
                        f"//li[contains(text(), '{label}') "
                        f"and not(contains(text(), 'add to cart'))]"
                    )
                    for li in li_elems:
                        text = "".join(li.itertext()).strip()
                        if text and len(text) > 3:
                            li_html = etree.tostring(li, encoding="unicode", method="html")
                            found_specs.append(li_html)

            if found_specs:
                specs_parts = found_specs

        # 策略 4: 从 SFCC JavaScript 中提取规格数据
        if not specs_parts:
            attr_patterns = [
                r'"weight"\s*:\s*"?([^",}]+)"?',
                r'"drop"\s*:\s*"?([^",}]+)"?',
                r'"heelHeight"\s*:\s*"?([^",}]+)"?',
                r'"forefootHeight"\s*:\s*"?([^",}]+)"?',
            ]
            found_js_specs = []
            for pattern in attr_patterns:
                match = re.search(pattern, html_text, re.IGNORECASE)
                if match:
                    val = match.group(1).strip()
                    if val:
                        label = pattern.split('"')[1]
                        found_js_specs.append(f"<p>{label}: {val}</p>")
            if found_js_specs:
                specs_parts = found_js_specs

        return "".join(specs_parts)

    @staticmethod
    def _extract_features_from_html(tree, html_text):
        """
        从详情页 HTML 中提取 Features（特性/材质信息）。
        HOKA 页面的 "Features" 区域包含材质、构造等特性列表。

        保留 HTML 标签。
        """
        features_parts = []

        # 跳过的关键词（非产品特性的列表项）
        skip_keywords = [
            "add to cart", "shipping", "return", "size guide",
            "size chart", "add to bag", "out of stock",
            "sign up", "newsletter", "email", "privacy",
            "terms", "cookie", "account", "login",
        ]

        # 策略 1: 查找 "Features" 标题后的列表
        features_selectors = [
            "//*[contains(text(), 'Features')]/following-sibling::ul",
            "//*[contains(text(), 'Features:')]/following-sibling::ul",
            "//h2[contains(text(), 'Features')]/following-sibling::ul",
            "//h3[contains(text(), 'Features')]/following-sibling::ul",
            "//h4[contains(text(), 'Features')]/following-sibling::ul",
            "//*[contains(@class, 'features')]//ul",
            "//*[contains(@class, 'product-features')]//ul",
            "//*[contains(@class, 'product-features')]",
        ]

        for selector in features_selectors:
            elements = tree.xpath(selector)
            for elem in elements:
                li_elems = elem.xpath(".//li") if elem.tag == "ul" else [elem]
                for li in li_elems:
                    text = "".join(li.itertext()).strip()
                    if not text or len(text) < 3:
                        continue
                    if any(kw in text.lower() for kw in skip_keywords):
                        continue
                    li_html = etree.tostring(li, encoding="unicode", method="html")
                    features_parts.append(li_html)
            if features_parts:
                break

        # 策略 2: 查找 "Benefits" 标题后的列表
        if not features_parts:
            benefits_selectors = [
                "//*[contains(text(), 'Benefits')]/following-sibling::ul",
                "//h2[contains(text(), 'Benefits')]/following-sibling::ul",
                "//h3[contains(text(), 'Benefits')]/following-sibling::ul",
                "//h4[contains(text(), 'Benefits')]/following-sibling::ul",
            ]
            for selector in benefits_selectors:
                elements = tree.xpath(selector)
                for elem in elements:
                    li_elems = elem.xpath(".//li")
                    for li in li_elems:
                        text = "".join(li.itertext()).strip()
                        if not text or len(text) < 3:
                            continue
                        if any(kw in text.lower() for kw in skip_keywords):
                            continue
                        li_html = etree.tostring(li, encoding="unicode", method="html")
                        features_parts.append(li_html)
                if features_parts:
                    break

        # 策略 3: 从 SFCC JavaScript 中提取 features 数据
        if not features_parts:
            features_pattern = r'"features"\s*:\s*\[((?:[^\[\]]|\[[^\]]*\])*)\]'
            match = re.search(features_pattern, html_text, re.IGNORECASE)
            if match:
                features_str = match.group(1)
                feature_items = re.findall(r'"([^"]+)"', features_str)
                for item in feature_items:
                    if len(item) > 3 and not any(kw in item.lower() for kw in skip_keywords):
                        features_parts.append(f"<li>{item}</li>")

        return "".join(features_parts)

    # -------------------- 从列表页价格数据构建产品行 --------------------
    def _extract_from_price_data(self, url, description="", tech_specs="", features=""):
        """
        从列表页价格数据中提取产品数据。
        返回: (rows, error_reason)
        """
        price_info = self._lookup_price_data(url)
        if not price_info:
            return [], "无列表页价格数据"

        name = price_info.get("name", "")
        master_id = price_info.get("master_id", "")
        variant_id = price_info.get("variant_id", "")
        regular_price = price_info.get("regular_price")
        sale_price = price_info.get("sale_price")
        color_name = price_info.get("color_name", "")
        color_code = price_info.get("color_code", "")
        image_url = price_info.get("image_url", "")
        all_colors = price_info.get("all_color_images", []) or price_info.get("all_colors", [])

        if not name:
            return [], "产品名称为空"

        # 如果 master_id 为空，尝试从 URL 中提取
        if not master_id:
            url_master_id, url_color_code = self._extract_id_from_url(url)
            master_id = url_master_id or master_id
            if not color_code and url_color_code:
                color_code = url_color_code

        # 如果 color_name 为空，从 all_color_images 中查找
        if not color_name and color_code:
            color_name = self._lookup_color_name(color_code, all_colors)

        # 从 all_colors 构建父类图片列表
        parent_images = []
        if isinstance(all_colors, list):
            for c in all_colors:
                if isinstance(c, dict) and c.get("img"):
                    parent_images.append(c["img"])
        if not parent_images and image_url:
            parent_images.append(image_url)

        rows = []

        if color_code:
            # ===== 有颜色变体 → 生成父类 variable + 子类 variation =====
            rows.append({
                "Type": "variable",
                "SKU": master_id,
                "Name": name,
                "Description": description,
                "Sale price": "",
                "Regular price": "",
                "Categories": "",
                "Tags": "NULL",
                "Images": ",".join(parent_images[:8]) if parent_images else "",
                "Parent": "",
                "Attribute 1 name": "Color",
                "Attribute 1 value(s)": color_name,
                "Attribute 2 name": "",
                "Attribute 2 value(s)": "",
                "brand": "HOKA",
                "Stock": 1000.0,
                "is_upload": 0,
                self.FIELD_TECH_SPECS: tech_specs,
                self.FIELD_FEATURES: features,
            })

            child_sku = f"{master_id}-{color_code}"
            rows.append({
                "Type": "variation",
                "SKU": child_sku,
                "Name": name,
                "Description": "",
                "Sale price": self._format_price(sale_price),
                "Regular price": self._format_price(regular_price),
                "Categories": "",
                "Tags": "NULL",
                "Images": image_url if image_url else "",
                "Parent": master_id,
                "Attribute 1 name": "Color",
                "Attribute 1 value(s)": color_name,
                "Attribute 2 name": "",
                "Attribute 2 value(s)": "",
                "brand": "HOKA",
                "Stock": 1000.0,
                "is_upload": 0,
                self.FIELD_TECH_SPECS: "",
                self.FIELD_FEATURES: "",
            })
        else:
            # ===== 无颜色变体 → simple，不带属性 =====
            images_str = ",".join(parent_images[:8]) if parent_images else (image_url if image_url else "")
            rows.append({
                "Type": "simple",
                "SKU": master_id,
                "Name": name,
                "Description": description,
                "Sale price": self._format_price(sale_price),
                "Regular price": self._format_price(regular_price),
                "Categories": "",
                "Tags": "NULL",
                "Images": images_str,
                "Parent": "",
                "Attribute 1 name": "",
                "Attribute 1 value(s)": "",
                "Attribute 2 name": "",
                "Attribute 2 value(s)": "",
                "brand": "HOKA",
                "Stock": 1000.0,
                "is_upload": 0,
                self.FIELD_TECH_SPECS: tech_specs,
                self.FIELD_FEATURES: features,
            })

        return rows, None

    # -------------------- 产品详情解析 --------------------
    def process_response(self, response_text, url):
        """
        解析产品详情页 HTML，返回 CSV 行列表。
        返回: (rows, err_reason)
        """
        if self._is_datadome_blocked(response_text):
            return self._extract_from_price_data(url)

        try:
            tree = etree.HTML(response_text)

            description = self._extract_description_from_html(tree, response_text)
            tech_specs = self._extract_tech_specs_from_html(tree, response_text)
            features = self._extract_features_from_html(tree, response_text)

            return self._extract_from_price_data(url, description, tech_specs, features)

        except Exception as e:
            return self._extract_from_price_data(url)

    # -------------------- 获取并解析（带 URL 缓存） --------------------
    def _fetch_and_parse(self, url):
        """
        获取并解析产品页面。
        返回: (rows, err_reason)
        """
        response_text, fetch_err = self.fetch_product_page(url)
        if not response_text:
            rows, price_err = self._extract_from_price_data(url)
            if rows:
                return rows, None
            return [], fetch_err or price_err or "请求失败且无价格数据"

        rows, parse_err = self.process_response(response_text, url)
        if not parse_err:
            return rows, None

        return [], parse_err

    # -------------------- Worker（单线程，带 URL 缓存） --------------------
    def process_tasks(self):
        """
        单线程处理任务：获取 URL，解析，缓存结果，填充分类。
        """
        while True:
            task = self.task_queue.get()
            if task is None:
                self.task_queue.task_done()
                break

            seq_id, category, url = task
            rows_to_write = []
            error_type = None
            from_cache = False

            try:
                # 1. 检查 URL 缓存
                if url in self.url_cache:
                    cached_rows = self.url_cache[url]
                    self.cache_hits += 1
                    from_cache = True

                if from_cache:
                    rows_to_write = copy.deepcopy(cached_rows)
                    for row in rows_to_write:
                        row["Categories"] = category
                else:
                    # 2. 缓存未命中：请求页面并解析
                    rows_to_write, parse_err = self._fetch_and_parse(url)
                    if parse_err or not rows_to_write:
                        error_type = parse_err or "解析结果为空"
                        self._record_failure(category, url, error_type)
                    else:
                        for row in rows_to_write:
                            row["Categories"] = category
                        if url not in self.url_cache:
                            self.url_cache[url] = copy.deepcopy(rows_to_write)
                            self.cache_misses += 1
                            for row in self.url_cache[url]:
                                row["Categories"] = ""

                self.result_queue.put((seq_id, rows_to_write))

            except Exception as e:
                error_type = f"任务崩溃: {e}"
                self._record_failure(category, url, error_type)
                self.result_queue.put((seq_id, []))

            finally:
                self.completed_tasks += 1
                cur = self.completed_tasks
                total = self.total_tasks
                cache_tag = "[CACHE]" if from_cache else "[FETCH]"
                if error_type:
                    print(f"[FAILED] {error_type} {cur}/{total}: {url}")
                else:
                    print(f"[PROGRESS] {cache_tag} 已完成 {cur}/{total}: {category} -> {url}")

                self.task_queue.task_done()

    # -------------------- Writer --------------------
    def writer_worker(self, fieldnames):
        """
        Writer 线程：按 seq_id 顺序写入 CSV。
        """
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        with open(self.output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            next_seq = 0
            buffer = {}

            while True:
                item = self.result_queue.get()
                if item is None:
                    self.result_queue.task_done()
                    break

                seq_id, rows = item
                buffer[seq_id] = rows

                while next_seq in buffer:
                    current_rows = buffer.pop(next_seq)
                    if current_rows:
                        writer.writerows(current_rows)
                    next_seq += 1

                self.result_queue.task_done()

    # -------------------- 主流程 --------------------
    def run(self):
        """主入口：加载任务，启动浏览器，处理任务，写入 CSV。"""
        self.load_tasks()
        if self.total_tasks == 0:
            print("没有可执行任务，请检查 input_file 内容。")
            return

        fieldnames = [
            "Type", "SKU", "Name", "Description", "Sale price", "Regular price",
            "Categories", "Tags", "Images", "Parent",
            "Attribute 1 name", "Attribute 1 value(s)", "Attribute 2 name", "Attribute 2 value(s)",
            "brand", "Stock", "is_upload",
            self.FIELD_TECH_SPECS,
            self.FIELD_FEATURES,
        ]

        # 启动 Writer 线程
        writer_thread = threading.Thread(target=self.writer_worker, args=(fieldnames,))
        writer_thread.start()

        # 启动浏览器
        self._init_browser()

        # 添加结束标记
        self.task_queue.put(None)

        # 单线程处理任务
        self.process_tasks()

        # 等待 Writer 完成
        self.result_queue.put(None)
        writer_thread.join()

        # 关闭浏览器
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass

        # 保存失败记录
        os.makedirs(os.path.dirname(self.fail_file), exist_ok=True)
        with open(self.fail_file, "w", encoding="utf-8") as f:
            json.dump(self.failures, f, ensure_ascii=False, indent=2)

        print(f"\n任务完成: total={self.total_tasks}, completed={self.completed_tasks}")
        print(f"URL 缓存: 实际请求={self.cache_misses}, 缓存命中={self.cache_hits}, 节省请求={self.cache_hits}")
        print(f"失败记录已写入: {self.fail_file}")
        print(f"结果已写入: {self.output_file}")


if __name__ == "__main__":
    crawler = HokaCrawler(
        input_file=r"output\hoka_detail_url_wjy.json",
        output_file=r"output\hoka_result.csv",
        fail_file=r"output\hoka_fail.json",
        price_data_file=r"output\hoka_prices.json",
        max_retries=3,
        timeout=30,
    )
    crawler.run()
