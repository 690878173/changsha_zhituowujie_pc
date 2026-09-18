"""
在不改动 clawer.py 主体解析逻辑的前提下，把请求层替换为
「浏览器采 cookie + curl_cffi 批量请求」的混合方案，并新增尺码提取。

尺码提取结果写入 Attribute 2 (Attribute 2 name = "Size", Attribute 2 value(s) = 尺码列表)。
价格数据完全沿用父类逻辑，从 price_data_file 加载，不受影响。

用法：
    python clawer_dd.py

依赖：
    pip install curl_cffi DrissionPage lxml

需与 clawer.py / dd_fetcher.py 放在同一目录。
"""

import re
import json
import copy
import time
from urllib.parse import unquote

from clawer import HokaCrawler
from dd_fetcher import DataDomeFetcher, is_blocked

# lxml 用于 HTML 解析（可选，父类已用 etree，这里用 lxml.html 更方便）
try:
    from lxml import html as lxml_html
except ImportError:
    lxml_html = None


class HokaCrawlerDD(HokaCrawler):
    """
    覆盖原类的三处网络相关逻辑：
      _is_datadome_blocked  -> 用窄标记 + 正向校验，消除误判
      _init_browser         -> 初始化混合抓取器（内部才启浏览器）
      fetch_product_page    -> 走 curl_cffi 主通道

    新增：
      _extract_sizes        -> 尺码提取（多策略降级）
      process_response      -> 在父类解析结果上追加尺码到 Attribute 2

    价格、缓存、CSV 输出逻辑全部沿用父类。
    """

    def __init__(self, *args, impersonate="auto", proxy=None,
                 headless=False, delay_range=(0.8, 2.2), **kwargs):
        super().__init__(*args, **kwargs)
        self.impersonate = impersonate
        self.proxy = proxy
        self.headless = headless
        self.delay_range = delay_range
        self.fetcher = None
        # master_id 级产品缓存：同一产品只请求一次，避免不同 URL 重复处理导致结构混乱
        self.product_cache = {}
        self.product_cache_hits = 0

    # ---------- 拦截判定：替换掉父类那个会误判的版本 ----------
    def _is_datadome_blocked(self, text):
        return is_blocked(text)

    # ---------- 请求层初始化 ----------
    def _init_browser(self):
        print("[INFO] 初始化混合请求层（浏览器取 cookie -> curl_cffi 复用）...")
        self.fetcher = DataDomeFetcher(
            home_url="https://www.hoka.com/en/us/",
            impersonate=self.impersonate,
            proxy=self.proxy,
            headless=self.headless,
            timeout=self.timeout,
            max_retries=self.max_retries,
            delay_range=self.delay_range,
            browser_fallback=True,
        )
        self.fetcher.refresh_session()
        # 父类 run() 用 self.page 判断是否需要关闭浏览器，这里置空交由 fetcher 自己管理
        self.page = None
        print("[INFO] 请求层就绪")

    # ---------- 单个产品页请求 ----------
    def fetch_product_page(self, url):
        """
        走 curl_cffi 主通道抓取产品页 HTML。
        返回值直接透传 fetcher.fetch() 的结果 (html_text, error)，
        与父类签名完全一致。
        """
        if self.fetcher is None:
            self._init_browser()
        return self.fetcher.fetch(url, referer="https://www.hoka.com/en/us/")

    # ---------- master_id 级产品缓存 ----------
    def _fetch_and_parse(self, url):
        """
        覆盖父类方法：加一层 master_id 级缓存。
        同一产品（同一个 master_id）只请求一次，避免：
        - 带颜色 URL 和不带颜色 URL 分别处理，产生 simple/variable 混用
        - 同一个产品的多个颜色 URL 重复请求，浪费资源

        缓存里的 rows 不带 Categories（和父类 url_cache 逻辑一致），
        取出时再填充分类。
        """
        master_id, _ = self._extract_id_from_url(url)
        if not master_id:
            # 提取不到 master_id，走父类逻辑
            return super()._fetch_and_parse(url)

        # master_id 缓存命中
        if master_id in self.product_cache:
            self.product_cache_hits += 1
            cached = self.product_cache[master_id]
            rows = copy.deepcopy(cached["rows"])
            err = cached["err"]
            return rows, err

        # 缓存未命中：走父类原始逻辑请求并解析
        rows, err = super()._fetch_and_parse(url)

        # 存入 master_id 缓存（Categories 留空）
        if rows:
            cached_rows = copy.deepcopy(rows)
            for r in cached_rows:
                r["Categories"] = ""
            self.product_cache[master_id] = {
                "rows": cached_rows,
                "err": err,
            }
        else:
            # 失败也缓存一下，避免重复失败请求
            self.product_cache[master_id] = {
                "rows": [],
                "err": err,
            }

        return rows, err

    # ==================== 新增：尺码提取 ====================

    def _extract_sizes(self, html_text):
        """
        从产品页 HTML 中提取主产品的尺码列表，多策略降级尝试。
        注意：只提取主产品的尺码，排除页面下方配件/推荐商品的尺码。

        支持数字尺码（7, 7.5, 8...）和字母尺码（S, M, L, XL...）。
        返回格式：逗号分隔的字符串，如 "7,7.5,8,8.5,9" 或 "S,M,L,XL"
        提取失败返回空字符串。

        优先级（从最可靠到兜底）：
        1. URL 参数 dwvar_xxx_size=（硬编码在 HTML 中，不受 JS 渲染影响）
        2. .attribute-size 区域内的 data-attribute-type="size" 按钮（主产品专属）
        3. data-qa="productUS Size" 标记的按钮（HOKA 主产品特有）
        4. SFCC 产品 JSON 数据（页面内 JS 变量）
        5. JSON-LD 结构化数据（Product 级，不含配件）
        6. 通用 HTML 兜底

        防干扰机制：尺码类型一致性过滤 —— 如果同时提取到数字和字母尺码，
        只保留数量占多数的那一组（排除配件混入的少数尺码）。
        """
        raw_sizes = []

        # ---- 策略 1：URL 参数 dwvar_xxx_size=（最可靠，不受 JS 渲染影响）----
        sizes = self._extract_sizes_from_url_params(html_text)
        if sizes:
            filtered = self._filter_size_consistency(sizes)
            if filtered:
                return self._format_sizes(filtered)

        # ---- 策略 2：.attribute-size 主产品区域内的尺码按钮 ----
        sizes = self._extract_sizes_from_html(html_text, scope="main")
        if sizes:
            filtered = self._filter_size_consistency(sizes)
            if filtered:
                return self._format_sizes(filtered)

        # ---- 策略 3：data-qa="productUS Size" 主产品标记 ----
        sizes = self._extract_sizes_from_html(html_text, scope="qa")
        if sizes:
            filtered = self._filter_size_consistency(sizes)
            if filtered:
                return self._format_sizes(filtered)

        # ---- 策略 4：SFCC 产品 JSON 数据 ----
        sizes = self._extract_sizes_from_js_vars(html_text)
        if sizes:
            filtered = self._filter_size_consistency(sizes)
            if filtered:
                return self._format_sizes(filtered)

        # ---- 策略 5：JSON-LD 结构化数据 ----
        sizes = self._extract_sizes_from_jsonld(html_text)
        if sizes:
            filtered = self._filter_size_consistency(sizes)
            if filtered:
                return self._format_sizes(filtered)

        # ---- 策略 6：通用 HTML 兜底 ----
        sizes = self._extract_sizes_from_html(html_text, scope="all")
        if sizes:
            filtered = self._filter_size_consistency(sizes)
            if filtered:
                return self._format_sizes(filtered)

        return ""

    @staticmethod
    def _filter_size_consistency(sizes_list):
        """
        尺码类型一致性过滤。
        如果同时有数字尺码和字母尺码，只保留数量占多数的那一组，
        用于排除页面上配件/推荐商品混入的少数尺码。

        例：[7,7.5,8,8.5,9,9.5,10,10.5,11,11.5,12,12.5,13,14,15,16,S,M,L,XL]
            → 数字 16 个 > 字母 4 个，保留数字，过滤掉 S/M/L/XL
        """
        if not sizes_list:
            return []

        numeric = []
        letter = []

        for s in sizes_list:
            try:
                float(s)
                numeric.append(s)
            except (ValueError, TypeError):
                # 检查是否是字母尺码（S/M/L/XL 等）
                s_upper = s.upper().strip()
                letter_pattern = r'^(X*S|M|X*L|[2-9]XL|XXS|XS|SM|MD|LG|XL|XXL|XXXL|XXXXL)$'
                if re.match(letter_pattern, s_upper):
                    letter.append(s)

        # 只有一种类型，直接返回
        if numeric and not letter:
            return numeric
        if letter and not numeric:
            return letter

        # 两种都有，保留数量多的那组
        if len(numeric) >= len(letter):
            return numeric
        else:
            return letter

    @staticmethod
    def _format_sizes(sizes_list):
        """
        将尺码列表排序并格式化为逗号分隔字符串。
        - 数字尺码按数值从小到大排
        - 字母尺码按 S < M < L < XL < XXL... 顺序排
        - 混合时数字在前，字母在后
        """
        # 字母尺码的排序权重
        letter_order = {
            'XXS': 10, 'XS': 20, 'S': 30, 'M': 40, 'L': 50,
            'XL': 60, 'XXL': 70, 'XXXL': 80, 'XXXXL': 90,
            '2XL': 70, '3XL': 80, '4XL': 90, '5XL': 100,
            'SM': 30, 'MD': 40, 'LG': 50,
        }

        def _size_key(s):
            s_upper = s.upper()
            # 数字尺码
            try:
                return (0, float(s))
            except (ValueError, TypeError):
                pass
            # 字母尺码
            if s_upper in letter_order:
                return (1, letter_order[s_upper])
            # 其他兜底
            return (2, s)

        sorted_sizes = sorted(sizes_list, key=_size_key)
        return ",".join(sorted_sizes)

    def _extract_sizes_from_jsonld(self, html_text):
        """
        从 <script type="application/ld+json"> 中提取 Product schema 的尺码。
        返回 list，提取失败返回空 list。
        """
        try:
            pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.findall(pattern, html_text, re.DOTALL | re.IGNORECASE)

            for match in matches:
                try:
                    data = json.loads(match.strip())
                except json.JSONDecodeError:
                    continue

                items = data if isinstance(data, list) else [data]

                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if item.get("@type") == "Product" or "Product" in (item.get("@type") or ""):
                        sizes = self._parse_sizes_from_jsonld_product(item)
                        if sizes:
                            return sizes

                        # hasVariant 中可能有具体尺码
                        variants = item.get("hasVariant", [])
                        if isinstance(variants, dict):
                            variants = [variants]
                        for v in variants:
                            if isinstance(v, dict):
                                vs = self._parse_sizes_from_jsonld_product(v)
                                if vs:
                                    return vs
            return []
        except Exception as e:
            print(f"[WARN] JSON-LD 尺码提取异常: {e}")
            return []

    def _parse_sizes_from_jsonld_product(self, product_dict):
        """从 JSON-LD 的 Product / Offer 中提取尺码值。"""
        sizes = set()

        # 直接的 size 字段
        size_val = product_dict.get("size")
        if size_val:
            if isinstance(size_val, list):
                for s in size_val:
                    if isinstance(s, str):
                        cleaned = self._clean_size(s)
                        if cleaned:
                            sizes.add(cleaned)
                    elif isinstance(s, dict):
                        cleaned = self._clean_size(str(s.get("name", "") or s.get("value", "")))
                        if cleaned:
                            sizes.add(cleaned)
            elif isinstance(size_val, str):
                cleaned = self._clean_size(size_val)
                if cleaned:
                    sizes.add(cleaned)

        # 从 offers / hasOfferCatalog 中提取
        for key in ("offers", "hasOfferCatalog"):
            offers = product_dict.get(key, [])
            if isinstance(offers, dict):
                offers = [offers]
            for offer in offers:
                if isinstance(offer, dict):
                    for field in ("size", "sku", "name"):
                        val = offer.get(field)
                        if val and isinstance(val, str):
                            s = self._extract_size_from_string(val)
                            if s:
                                sizes.add(s)

        return list(sizes)

    def _extract_sizes_from_js_vars(self, html_text):
        """
        从页面 JavaScript 变量中提取产品尺码数据。
        适配 Salesforce Commerce Cloud (SFCC) 常见的多种数据格式。
        返回 list，失败返回空 list。
        """
        sizes = set()

        try:
            # 模式 1：明确的 size 数组，如 "sizes": ["7", "8", ...]
            pattern1 = r'"(?:sizes|sizeOptions|availableSizes|sizeList|variationValues|size_values)"\s*:\s*\[(.*?)\]'
            matches = re.findall(pattern1, html_text, re.DOTALL)
            for match in matches:
                size_strs = re.findall(r'"([^"]+)"', match)
                for s in size_strs:
                    cleaned = self._clean_size(s)
                    if cleaned:
                        sizes.add(cleaned)
            if sizes:
                return list(sizes)

            # 模式 2：SFCC variationAttributes 中的 size 定义
            # 如 "size":{"id":"size","name":"US Size","values":[{"value":"7","displayValue":"7"},...]}
            pattern2 = r'"size"\s*:\s*\{[^}]*?"values"\s*:\s*\[(.*?)\]'
            match = re.search(pattern2, html_text, re.DOTALL)
            if match:
                values_str = match.group(1)
                # 提取所有 "value":"xxx" 或 "displayValue":"xxx"
                val_matches = re.findall(
                    r'"(?:value|displayValue)"\s*:\s*"([^"]+)"', values_str
                )
                for s in val_matches:
                    cleaned = self._clean_size(s)
                    if cleaned:
                        sizes.add(cleaned)
            if sizes:
                return list(sizes)

            # 模式 3：dw.app 或 product JSON 中的 variants 数据
            # 从大量 "size":"xxx" 中提取（需要上下文判断是产品变体的 size）
            # 找到包含 variation / variant 的 JS 对象块，再从中提取 size
            pattern3 = r'"variation(?:s|Attributes)?"\s*:\s*\{(.*?)\}'
            matches = re.findall(pattern3, html_text, re.DOTALL)
            for match in matches:
                size_matches = re.findall(r'"size"\s*:\s*"([^"]+)"', match)
                for s in size_matches:
                    cleaned = self._clean_size(s)
                    if cleaned:
                        sizes.add(cleaned)
            if sizes:
                return list(sizes)

            # 模式 4：从 SFCC 的 Product-Variation URL 旁边的 JS 数据里找
            # 匹配 data-size / sizeValue 等字段
            pattern4 = r'"(?:sizeValue|sizeId|sizeCode|optionSize)"\s*:\s*"([^"]+)"'
            matches = re.findall(pattern4, html_text)
            for s in matches:
                cleaned = self._clean_size(s)
                if cleaned:
                    sizes.add(cleaned)

            return list(sizes)
        except Exception as e:
            print(f"[WARN] JS 变量尺码提取异常: {e}")
            return []

    def _extract_sizes_from_url_params(self, html_text):
        """
        从页面 HTML 中的按钮 URL 提取尺码。
        HOKA 每个尺码按钮的 value 属性都是一个 Product-Variation URL，
        里面包含 dwvar_xxx_size=SIZE 参数。
        URL 结构全站统一，比 DOM 结构更稳定。

        返回 list，失败返回空 list。
        """
        sizes = set()

        try:
            # 匹配所有 dwvar_xxx_size=VALUE 形式的 URL 参数
            # VALUE 可能是数字（7, 7.5, 10）或字母（S, M, L, XL）
            pattern = r'dwvar_[^&]+_size=([^&]+)'
            matches = re.findall(pattern, html_text)

            for match in matches:
                # URL 解码
                size_val = unquote(match).strip()
                cleaned = self._clean_size(size_val)
                if cleaned:
                    sizes.add(cleaned)

            return list(sizes)
        except Exception as e:
            print(f"[WARN] URL 参数尺码提取异常: {e}")
            return []

    def _extract_sizes_from_html(self, html_text, scope="all"):
        """
        从 HTML 尺码选择器（按钮/swatch）中提取尺码。

        scope 参数控制提取范围：
          - "main": 只在 .attribute-size 主产品区域内提取（排除配件）
          - "qa": 只匹配带 data-qa="productUS Size" 的按钮（主产品特有）
          - "all": 全部兜底匹配（可能混入配件，尽量不用）

        返回 list，失败返回空 list。
        """
        sizes = set()

        if lxml_html is None:
            return []

        try:
            tree = lxml_html.fromstring(html_text)

            if scope == "main":
                # 只在 .attribute-size 主产品区域内查找
                selectors = [
                    '//div[contains(@class, "attribute-size")]//button[@data-attribute-type="size"]',
                    '//div[contains(@class, "attribute-size")]//button[contains(@class, "options-select")]',
                ]
            elif scope == "qa":
                # 只匹配带 productUS Size data-qa 的按钮（主产品特有）
                selectors = [
                    '//button[contains(@data-qa, "productUS Size")]',
                ]
            else:
                # 全部兜底（可能混入配件）
                selectors = [
                    '//button[contains(@class, "options-select") and @data-attribute-type="size"]',
                    '//button[contains(@data-qa, "Size")]',
                    '//div[contains(@class, "attribute-grid")]//button[@data-attr-value]',
                    '//button[contains(@class, "size") and not(contains(@class, "chart")) and not(contains(@class, "guide"))]',
                    '//div[contains(@class, "size") and contains(@class, "swatch")]//button',
                    '//button[@data-size]',
                    '//button[@data-value]',
                ]
            for sel in selectors:
                buttons = tree.xpath(sel)
                for btn in buttons:
                    # 跳过 size chart / size guide 按钮
                    btn_text = (btn.text_content() or "").strip().lower()
                    if "chart" in btn_text or "guide" in btn_text:
                        continue
                    # 优先从 data-attr-value（HOKA）取，再 data-size / data-value，最后文本
                    size_val = (
                        btn.get('data-attr-value')
                        or btn.get('data-size')
                        or btn.get('data-value')
                    )
                    if not size_val:
                        # 从 .printed-size span 里取（HOKA 结构）
                        printed = btn.xpath('.//span[contains(@class, "printed-size")]')
                        if printed:
                            size_val = printed[0].text_content()
                    if not size_val:
                        size_val = btn.text_content()
                    cleaned = self._clean_size(size_val)
                    if cleaned:
                        sizes.add(cleaned)
                if sizes:
                    break

            # select + option 形式
            if not sizes:
                options = tree.xpath(
                    '//select[contains(@name, "size") or contains(@class, "size")]/option'
                )
                for opt in options:
                    val = opt.get('value') or opt.text_content()
                    cleaned = self._clean_size(val)
                    if cleaned:
                        sizes.add(cleaned)

            return list(sizes)
        except Exception as e:
            print(f"[WARN] HTML 尺码提取异常: {e}")
            return []

    @staticmethod
    def _clean_size(size_str, strict=False):
        """
        清洗尺码字符串。支持数字尺码和字母尺码（S/M/L/XL 等）。

        strict=True 时严格匹配，只返回明确是尺码的字符串；
        strict=False 时宽松匹配，只要不是明显非尺码的都返回。

        例：
          "Size 9" -> "9", "US 9.5" -> "9.5", "090" -> "9"
          "S" -> "S", "M" -> "M", "L" -> "L", "XL" -> "XL", "XXL" -> "XXL"
        """
        if not size_str:
            return ""
        s = str(size_str).strip()
        if not s:
            return ""

        # 去掉常见前缀
        for prefix in ("Size ", "size ", "US ", "us ", "EU ", "eu ", "UK ", "uk "):
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break

        # ---- 数字尺码 ----
        # 匹配纯数字（含小数），如 7, 7.5, 10, 10.5
        m = re.match(r'^(\d+\.?\d*)$', s.strip())
        if m:
            val = m.group(1)
            if val.endswith('.0'):
                val = val[:-2]
            return val

        # ---- 三位数编码，如 090 = 9.0, 095 = 9.5, 105 = 10.5 ----
        if re.match(r'^\d{3}$', s.strip()):
            code = s.strip()
            whole = int(code[:2])
            half = int(code[2])
            if half == 0:
                return str(whole)
            elif half == 5:
                return f"{whole}.5"

        # ---- 字母尺码（S/M/L/XL 系列）----
        # 标准服装尺码：XS, S, M, L, XL, XXL, XXXL, 2XL, 3XL, 4XL 等
        s_upper = s.upper().strip()
        letter_size_pattern = r'^(X*S|M|X*L|[2-9]XL|XS|SM|MD|LG|XL|XXL|XXXL|XXXXL)$'
        if re.match(letter_size_pattern, s_upper):
            return s_upper

        # 非严格模式下，对于短字符串（<=6字符）直接返回原值（可能是特殊尺码）
        if not strict and len(s) <= 6 and len(s) >= 1:
            # 排除明显不是尺码的
            if s.lower() not in ("null", "none", "n/a", "na", "-", "--", "---"):
                return s

        return ""

    def _extract_size_from_string(self, s):
        """从任意字符串（如 SKU）中尝试提取尺码。"""
        if not s:
            return ""
        # 匹配 SKU 末尾的三位数尺码编码，如 -090, -105
        m = re.search(r'-(\d{3})(?:-|$)', s)
        if m:
            return self._clean_size(m.group(1))
        return ""

    # ==================== 覆盖：解析方法，追加尺码 + 笛卡尔积 ====================

    def process_response(self, response_text, url):
        """
        覆盖父类的 process_response。

        核心逻辑：
        1. 调用父类原始解析拿到 rows（含价格、颜色）
        2. 从 HTML 提取主产品尺码
        3. 从 HTML 提取所有颜色列表（补充价格数据可能缺失的颜色）
        4. 如果有尺码：
           - 原来是 simple 的 → 升级为 variable + 尺码 variation
           - 原来是 variable 的 → 在现有颜色基础上追加尺码维度，笛卡尔积展开
        5. variable 行补全：所有颜色图片 + 所有属性值（颜色 + 尺码）

        价格完全沿用父类逻辑，不受影响。
        """
        # 调用父类原始解析（价格从 price_data 来，不受影响）
        rows, err = super().process_response(response_text, url)

        # 如果父类解析失败，直接返回（可能是 DataDome 拦截走了价格兜底）
        if not rows:
            return rows, err

        # 提取尺码
        sizes_str = ""
        try:
            sizes_str = self._extract_sizes(response_text)
        except Exception as e:
            print(f"  [WARN] 尺码提取异常: {e}")

        # 提取页面上的所有颜色（补充价格数据可能只有一个颜色的问题）
        all_colors = self._extract_colors_from_html(response_text)

        if not sizes_str:
            print(f"  [SIZES] 未提取到尺码")
            # 没有尺码也补全一下颜色列表
            if all_colors and len(all_colors) > 1:
                rows = self._enhance_variable_with_colors(rows, all_colors)
            return rows, err

        size_list = [s.strip() for s in sizes_str.split(",") if s.strip()]
        print(f"  [SIZES] 提取到 {len(size_list)} 个尺码: {sizes_str}")
        if all_colors:
            print(f"  [COLORS] 页面检测到 {len(all_colors)} 个颜色")

        # 找出各类型行
        var_rows = [r for r in rows if r.get("Type") == "variable"]
        variation_rows = [r for r in rows if r.get("Type") == "variation"]
        simple_rows = [r for r in rows if r.get("Type") == "simple"]

        new_rows = []

        if var_rows and variation_rows:
            # ===== 情况 1：已有 variable + variation（有颜色）=====
            # 在现有颜色变体基础上，追加尺码维度做笛卡尔积

            # 如果页面上有更多颜色，补充进去
            if all_colors and len(all_colors) > len(variation_rows):
                variation_rows = self._expand_color_variations(
                    variation_rows, all_colors, var_rows[0]
                )

            # variable 父行：补全所有属性值和所有图片
            parent_row = copy.deepcopy(var_rows[0])
            # Attribute 1 (Color)：收集所有颜色值
            color_values = list(set(
                v.get("Attribute 1 value(s)", "") for v in variation_rows
                if v.get("Attribute 1 value(s)")
            ))
            parent_row["Attribute 1 value(s)"] = ", ".join(sorted(color_values))
            # Attribute 2 (Size)：所有尺码
            parent_row["Attribute 2 name"] = "Size"
            parent_row["Attribute 2 value(s)"] = sizes_str
            # Images：收集所有变体的图片
            all_images = []
            for v in variation_rows:
                imgs = v.get("Images", "")
                if imgs:
                    for img in imgs.split(","):
                        img = img.strip()
                        if img and img not in all_images:
                            all_images.append(img)
            if all_images:
                parent_row["Images"] = ",".join(all_images)
            new_rows.append(parent_row)

            # variation 子行：颜色 × 尺码 笛卡尔积
            for base_var in variation_rows:
                for size_val in size_list:
                    var_row = copy.deepcopy(base_var)
                    var_row["Attribute 2 name"] = "Size"
                    var_row["Attribute 2 value(s)"] = size_val
                    # SKU 追加尺码编码，保证唯一
                    size_code = self._size_to_sku_suffix(size_val)
                    var_row["SKU"] = f"{var_row['SKU']}-{size_code}"
                    new_rows.append(var_row)

            print(f"  [VARIATIONS] 笛卡尔积展开: {len(variation_rows)} 个颜色 × {len(size_list)} 个尺码 = {len(variation_rows) * len(size_list)} 条变体")

        elif simple_rows and size_list:
            # ===== 情况 2：simple 但有尺码 → 升级为 variable + 尺码 variation =====
            base_row = simple_rows[0]

            # variable 父行
            parent_row = copy.deepcopy(base_row)
            parent_row["Type"] = "variable"
            parent_row["Sale price"] = ""
            parent_row["Regular price"] = ""
            parent_row["Attribute 1 name"] = "Size"
            parent_row["Attribute 1 value(s)"] = sizes_str
            parent_row["Attribute 2 name"] = ""
            parent_row["Attribute 2 value(s)"] = ""
            # 父产品 SKU 去掉可能的颜色后缀（只留 master_id）
            parent_sku = base_row.get("SKU", "")
            # 去掉末尾的 -XXX 颜色编码
            m = re.match(r'^(\d+)(-[A-Z]+)?$', parent_sku)
            if m:
                parent_row["SKU"] = m.group(1)
            new_rows.append(parent_row)

            # variation 子行：每个尺码一条
            for size_val in size_list:
                var_row = copy.deepcopy(base_row)
                var_row["Type"] = "variation"
                var_row["Parent"] = parent_row["SKU"]
                var_row["Attribute 1 name"] = "Size"
                var_row["Attribute 1 value(s)"] = size_val
                var_row["Attribute 2 name"] = ""
                var_row["Attribute 2 value(s)"] = ""
                # SKU = master_id + 尺码编码
                size_code = self._size_to_sku_suffix(size_val)
                var_row["SKU"] = f"{parent_row['SKU']}-{size_code}"
                new_rows.append(var_row)

            print(f"  [VARIATIONS] simple → variable 升级: {len(size_list)} 个尺码变体")

        else:
            # 其他情况原样返回
            new_rows = rows

        return new_rows, err

    def _extract_colors_from_html(self, html_text):
        """
        从产品页 HTML 中提取所有颜色列表。
        返回 [{"code": "RRYM", "name": "xxx", "image": "https://..."}, ...]
        失败返回空 list。
        """
        colors = []

        if lxml_html is None:
            return colors

        try:
            tree = lxml_html.fromstring(html_text)

            # 颜色按钮常见结构：带 data-attribute-type="color" 的按钮
            color_btns = tree.xpath(
                '//div[contains(@class, "attribute-color")]//button[@data-attribute-type="color"]'
            )
            if not color_btns:
                color_btns = tree.xpath(
                    '//button[contains(@data-qa, "Color") or @data-attribute-type="color"]'
                )

            for btn in color_btns:
                code = btn.get('data-attr-value') or btn.get('data-attr-id') or ''
                name = btn.get('title') or btn.get('aria-label') or code or ''
                # 找颜色缩略图
                img = ''
                img_elem = btn.xpath('.//img')
                if img_elem:
                    img = img_elem[0].get('src') or ''
                if code:
                    colors.append({
                        "code": code.strip(),
                        "name": name.strip(),
                        "image": img.strip(),
                    })

            return colors
        except Exception as e:
            print(f"  [WARN] 颜色提取异常: {e}")
            return []

    def _expand_color_variations(self, variation_rows, all_colors, parent_row):
        """
        如果页面上的颜色比价格数据里的多，补充缺失的颜色变体。
        新颜色的价格使用现有变体的价格作为参考。
        """
        if not all_colors:
            return variation_rows

        existing_codes = set()
        for v in variation_rows:
            sku = v.get("SKU", "")
            # 从 SKU 中提取颜色代码（SKU 格式: master_id-color_code）
            parts = sku.split("-")
            if len(parts) >= 2:
                existing_codes.add(parts[-1])

        # 参考价格（取第一个变体的价格）
        ref_sale_price = variation_rows[0].get("Sale price", "") if variation_rows else ""
        ref_reg_price = variation_rows[0].get("Regular price", "") if variation_rows else ""
        ref_image = variation_rows[0].get("Images", "") if variation_rows else ""
        master_id = parent_row.get("SKU", "")

        added = 0
        for color in all_colors:
            code = color["code"]
            if code in existing_codes:
                continue
            # 补充缺失的颜色变体
            new_var = copy.deepcopy(variation_rows[0]) if variation_rows else {}
            new_var["Type"] = "variation"
            new_var["SKU"] = f"{master_id}-{code}" if master_id else code
            new_var["Parent"] = master_id
            new_var["Attribute 1 name"] = "Color"
            new_var["Attribute 1 value(s)"] = color.get("name", code)
            new_var["Images"] = color.get("image", ref_image)
            new_var["Sale price"] = ref_sale_price
            new_var["Regular price"] = ref_reg_price
            new_var["Attribute 2 name"] = ""
            new_var["Attribute 2 value(s)"] = ""
            # Tech Specs / Features 留空（颜色变体不需要重复）
            for key in list(new_var.keys()):
                if "Tech Specs" in key or "Features" in key:
                    new_var[key] = ""
            variation_rows.append(new_var)
            added += 1

        if added > 0:
            print(f"  [COLORS] 补充了 {added} 个缺失的颜色变体")

        return variation_rows

    def _enhance_variable_with_colors(self, rows, all_colors):
        """
        对于没有尺码的产品，也补全 variable 行的颜色属性值和图片。
        """
        var_rows = [r for r in rows if r.get("Type") == "variable"]
        variation_rows = [r for r in rows if r.get("Type") == "variation"]

        if not var_rows or not all_colors:
            return rows

        parent_row = var_rows[0]
        color_names = [c.get("name", c["code"]) for c in all_colors]
        parent_row["Attribute 1 value(s)"] = ", ".join(color_names)

        # 收集所有图片
        all_images = []
        for c in all_colors:
            if c.get("image") and c["image"] not in all_images:
                all_images.append(c["image"])
        if all_images:
            parent_row["Images"] = ",".join(all_images)

        return rows

    @staticmethod
    def _size_to_sku_suffix(size_val):
        """
        将尺码值转换为 SKU 后缀编码（用于拼接 SKU 保证唯一性）。
        例："7" -> "070", "7.5" -> "075", "10" -> "100", "10.5" -> "105"
             "S" -> "S", "M" -> "M", "XL" -> "XL"
        """
        s = str(size_val).strip()
        # 数字尺码转三位数编码
        try:
            num = float(s)
            whole = int(num)
            half = int(round((num - whole) * 10))
            return f"{whole:02d}{half}"
        except (ValueError, TypeError):
            # 字母尺码直接用大写
            return s.upper()

    # ---------- 收尾 ----------
    def run(self):
        started = time.time()
        try:
            super().run()
        finally:
            if self.fetcher is not None:
                print(f"[STATS] {self.fetcher.stats()}")
                self.fetcher.close()
            print(f"[STATS] master_id缓存: 实际请求={len(self.product_cache)}, 缓存命中={self.product_cache_hits}")
            print(f"[STATS] 总耗时 {time.time() - started:.0f}s")


if __name__ == "__main__":
    crawler = HokaCrawlerDD(
        input_file=r"J:\changsha\8-10到8-15\hoka_自建\data\hoka_detail_url.json",
        output_file=r"output\hoka_result3.csv",
        fail_file=r"output\hoka_fail3.json",
        price_data_file=r"hoka_prices.json",
        max_retries=3,
        timeout=30,
        # "auto" = 按本机 Chrome 真实版本自动对齐 TLS 指纹档位
        impersonate="auto",
        # 若用代理，浏览器和 curl_cffi 必须走同一个，否则 datadome cookie 立即失效
        # proxy="http://user:pass@host:port",
        headless=False,
        delay_range=(1.0, 2.5),
    )
    crawler.run()
