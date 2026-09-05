"""Target detail parser using DrissionPage through the shared cached Step4."""

import json
import re
import time
import html as html_parser
import threading
from pathlib import Path
from queue import Queue

from DrissionPage import ChromiumPage, ChromiumOptions

from _ljp.mb.base import Get_Product as BaseStep4


class Get_Product(BaseStep4):
    """Target parser adapted from the template; cache/output are owned by BaseStep4."""

    def __init__(
        self,
        *args,
        variant_cache_path=None,
        variant_cache_save_num=1,
        save_html=True,
        html_save_dir=None,
        **kwargs,
    ):
        """Create a Target detail collector.

        ``variant_cache_path`` stores prices that have already been read for a
        partially processed product.  It is intentionally separate from the
        Step4 product cache: a product cache entry is only valid after every
        expected variation has been assembled into product rows.
        """
        self.variant_cache_path = variant_cache_path
        self.variant_cache_save_num = max(1, int(variant_cache_save_num))
        self.save_html = bool(save_html)
        self.html_save_dir = Path(html_save_dir) if html_save_dir else Path("html")
        self._variant_cache = {}
        self._variant_cache_changes_since_save = 0
        self._variant_cache_lock = threading.Lock()
        self._manual_verification_lock = threading.Lock()
        self._manual_verification_active = threading.Event()
        super().__init__(*args, **kwargs)

    def _init(self):
        super()._init()
        self._init_variant_cache()
        self.init()

    def _init_variant_cache(self):
        if self.variant_cache_path is None:
            index_file = Path(self.index_path)
            self.variant_cache_path = index_file.with_name(
                f"{index_file.stem}_variants{index_file.suffix or '.json'}"
            )
        self._variant_cache = self.Tool.File.load_json(
            self.variant_cache_path, default={}
        ) or {}
        if not isinstance(self._variant_cache, dict):
            self._variant_cache = {}

    @staticmethod
    def _has_price(value):
        return value is not None and bool(str(value).strip())

    def _cached_variant_data(self, url, expected_tcins):
        """Return cached purchasable and out-of-stock variant states."""
        with self._variant_cache_lock:
            entry = self._variant_cache.get(url, {})
            variants = entry.get("variants", {}) if isinstance(entry, dict) else {}
            return {
                str(tcin): {
                    "price": data.get("price", ""),
                    **({"stock": 0} if data.get("stock") == 0 else {}),
                }
                for tcin, data in variants.items()
                if str(tcin) in expected_tcins
                and isinstance(data, dict)
                and (
                    self._has_price(data.get("price"))
                    or data.get("stock") == 0
                )
            }

    def _save_variant_cache_locked(self):
        self.Tool.File.save_json(self._variant_cache, self.variant_cache_path)
        self._variant_cache_changes_since_save = 0

    def _cache_variant_price(self, url, tcin, price, stock=None):
        """Persist each successful or known-out-of-stock variant immediately."""
        if not self._has_price(price) and stock != 0:
            return
        data = {"price": price}
        if stock is not None:
            data["stock"] = stock
        with self._variant_cache_lock:
            entry = self._variant_cache.setdefault(url, {"variants": {}})
            variants = entry.setdefault("variants", {})
            if variants.get(str(tcin)) == data:
                return
            variants[str(tcin)] = data
            self._variant_cache_changes_since_save += 1
            if self._variant_cache_changes_since_save >= self.variant_cache_save_num:
                self._save_variant_cache_locked()

    def should_extract_all_variants(self, product_node, variations_dict):
        """Whether Target hierarchy entries should become variation rows.

        Subclasses can return ``False`` for sites whose response contains a
        non-purchasable hierarchy.  In that case the current product is
        exported as one simple product instead of treating the hierarchy as
        incomplete variations.
        """
        return True

    @staticmethod
    def _tcin_from_url(url):
        match = re.search(r"/A-(\d+)", str(url))
        return match.group(1) if match else "unknown"

    def _save_debug_html(self, page, parent_tcin, product_tcin):
        """Save the live DOM, including scripts, for failed-parse diagnosis."""
        if not self.save_html:
            return
        parent_id = re.sub(r"[^0-9A-Za-z_-]", "_", str(parent_tcin or "unknown"))
        product_id = re.sub(r"[^0-9A-Za-z_-]", "_", str(product_tcin or "unknown"))
        html_path = self.html_save_dir / parent_id / f"{product_id}.html"
        try:
            html = page.html
            if not html:
                html = page.run_js("return document.documentElement.outerHTML;")
            if not isinstance(html, str) or not html.strip():
                raise ValueError("页面 HTML 为空")
            self.Tool.HTML.save_raw(html, html_path)
            print(f"    [HTML] 已保存调试快照: {html_path}")
        except Exception as exc:
            self.Tool.print(f"保存调试 HTML 失败: {exc}", color="yellow")

    def init(self,proxy="127.0.0.1:7897", headless=False, wait_time=15,
                 num_threads=3, max_wait_price=12):
        self.proxy = proxy
        self.headless = headless
        self.wait_time = wait_time  # 初始页面加载等待（秒）
        self.max_wait_price = max_wait_price  # 智能等待价格元素出现的最长时间（秒）
        self.num_threads = num_threads  # 并行标签页数量


        self.browser = self._create_browser()
        self.tab_ls = [self.browser.new_tab() for _ in range(self.max_threads)]
        self._available_tabs = Queue()
        for tab in self.tab_ls:
            self._available_tabs.put(tab)
        self._worker_tab = threading.local()

    def _create_browser(self):
        """创建并配置 DrissionPage 浏览器"""
        co = ChromiumOptions()
        if self.proxy:
            co.set_proxy(f"http://{self.proxy}")
        co.headless(self.headless)
        co.set_argument("--disable-blink-features=AutomationControlled")
        co.set_argument("--no-first-run")
        co.set_argument("--no-default-browser-check")
        co.set_argument("--disable-infobars")
        # Keep Chromium's native UA and Client Hints aligned. A hard-coded UA
        # version can otherwise disagree with the installed browser version.
        return ChromiumPage(co)

    def get_tab(self):
        """Lease one tab to each request worker until that worker exits."""
        tab = getattr(self._worker_tab, "tab", None)
        if tab is None:
            tab = self._available_tabs.get()
            self._worker_tab.tab = tab
        return tab

    def _release_worker_tab(self):
        tab = getattr(self._worker_tab, "tab", None)
        if tab is not None:
            self._worker_tab.tab = None
            self._available_tabs.put(tab)

    def request_worker(self):
        try:
            super().request_worker()
        finally:
            self._release_worker_tab()



    def load_tasks(self):
        """Also accept the template's historical flat Target URL JSON input."""
        data = self.Tool.File.load_json(self.input_path)
        if isinstance(data, list):
            data = {"DefaultCategory": data}
        self._load_tasks_from_mapping(data)

    # ==================== 优化1: 智能等待价格元素出现 ====================
    def _wait_for_price_ready(self, page, timeout=None):
        """
        智能等待价格元素出现在DOM中。
        每0.5秒检查一次，出现就立即返回True，超时返回False。
        比固定sleep(15)快很多——大多数页面3-5秒就能加载好。
        """
        if timeout is None:
            timeout = self.max_wait_price
        check_js = """
            var el = document.querySelector('[data-test="product-price"]') ||
                     document.querySelector('[data-test="price"]') ||
                     document.querySelector('[class*="currentPriceFontSize"]') ||
                     document.querySelector('[class*="currentPrice"]');
            if (el && el.innerText.trim().match(/\\$[\\d,]+\\.?\\d*/)) return true;
            // 回退：检查任何含$价格的元素
            var allEls = document.querySelectorAll('[class*="price"], [class*="Price"]');
            for (var i = 0; i < allEls.length; i++) {
                var t = allEls[i].innerText.trim();
                if (t.match(/\\$[\\d,]+\\.?\\d*/) &&
                    !t.toLowerCase().includes('was') &&
                    !t.toLowerCase().includes('save')) return true;
            }
            return false;
        """
        elapsed = 0
        interval = 0.5
        while elapsed < timeout:
            try:
                ready = page.run_js(check_js)
                if ready:
                    return True
            except:
                pass
            time.sleep(interval)
            elapsed += interval
        return False

    def _verification_signal(self, page):
        """Return a visible verification signal, without treating normal copy as one."""
        try:
            details = page.run_js("""
                return JSON.stringify({
                    title: document.title || '',
                    text: (document.body && document.body.innerText || '').slice(0, 4000),
                    url: location.href || ''
                });
            """)
            if not details:
                return None
            page_details = json.loads(details)
            text = " ".join(str(value) for value in page_details.values()).lower()
        except Exception:
            return None

        signals = (
            "verify you are human",
            "verify that you are human",
            "are you a human",
            "security check",
            "unusual traffic",
            "access denied",
            "press and hold",
            "recaptcha",
            "hcaptcha",
            "cf-chl",
        )
        return next((signal for signal in signals if signal in text), None)

    def _wait_for_manual_verification(self, page, url):
        """Pause all newly started Target tasks until the operator clears a challenge."""
        while self._manual_verification_active.is_set():
            time.sleep(0.2)

        signal = self._verification_signal(page)
        if not signal:
            return

        with self._manual_verification_lock:
            signal = self._verification_signal(page)
            if not signal:
                return
            self._manual_verification_active.set()
            try:
                while signal:
                    self.Tool.print(
                        f"检测到浏览器验证（{signal}），已暂停新任务：{url}",
                        color="yellow",
                    )
                    try:
                        input("请在打开的浏览器中完成验证，然后按 Enter 继续：")
                    except EOFError as exc:
                        raise RuntimeError("需要人工完成浏览器验证，但当前运行没有交互式控制台。") from exc
                    time.sleep(1)
                    signal = self._verification_signal(page)
                    if signal:
                        self.Tool.print("验证页仍未通过，请完成验证后再次按 Enter。", color="yellow")
            finally:
                self._manual_verification_active.clear()

    def _extract_price_from_dom(self, page, retry=2):
        """
        从页面 DOM 提取当前显示的价格。
        优化: retry从3降到2，间隔从2秒降到1秒。
        """
        for attempt in range(retry):
            try:
                result = page.run_js("""
                    var priceEl = document.querySelector('[data-test="product-price"]');
                    if (!priceEl) priceEl = document.querySelector('[data-test="price"]');
                    if (!priceEl) {
                        priceEl = document.querySelector('[class*="currentPriceFontSize"]') ||
                                  document.querySelector('[class*="currentPrice"]');
                    }
                    if (!priceEl) {
                        var allEls = document.querySelectorAll('[class*="price"], [class*="Price"]');
                        for (var i = 0; i < allEls.length; i++) {
                            var t = allEls[i].innerText.trim().toLowerCase();
                            if (t && t.match(/\\$[\\d,]+\\.?\\d*/) &&
                                !t.includes('was') && !t.includes('reg ') &&
                                !t.includes('regular') && !t.includes('original') &&
                                !t.includes('save') && !t.includes('range')) {
                                priceEl = allEls[i];
                                break;
                            }
                        }
                    }
                    if (priceEl) {
                        var text = priceEl.innerText.trim();
                        var match = text.match(/\\$([\\d,]+\\.?\\d*)/);
                        if (match) return match[1].replace(',', '');
                    }
                    return null;
                """)
                if result:
                    return result
                if attempt < retry - 1:
                    time.sleep(1)
            except:
                if attempt < retry - 1:
                    time.sleep(1)
        return None

    def _format_price(self, price_str):
        """格式化价格为两位小数"""
        if not price_str:
            return ""
        try:
            return f"{float(price_str):.2f}"
        except (ValueError, TypeError):
            return price_str

    def _click_variant_chip(self, page, variant_value, option_name=None):
        """点击指定变体值的 chip 按钮"""
        try:
            escaped_value = (
                str(variant_value)
                .replace("\\", "\\\\")
                .replace("'", "\\'")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
            )
            escaped_name = (
                str(option_name or "")
                .replace("\\", "\\\\")
                .replace("'", "\\'")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
            )
            clicked = page.run_js(f"""
                var chips = document.querySelectorAll('button[class*="ndsChip"]');
                for (var chip of chips) {{
                var aria = (chip.getAttribute('aria-label') || '').trim();
                var parts = aria.split(',').map(function(part) {{ return part.trim(); }});
                var chipName = parts[0] || '';
                    var chipValue = (parts[1] || chip.innerText.trim())
                        .replace(/[ ]*-[ ]*out of stock[ ]*$/i, '').trim();
                    if (chipValue === '{escaped_value}' &&
                        (!'{escaped_name}' || chipName === '{escaped_name}')) {{
                        chip.click();
                        return true;
                    }}
                }}
                return false;
            """)
            return clicked
        except:
            return False

    def _get_variant_chip_values(self, page):
        """Read Target chips from accessibility labels, including image swatches."""
        try:
            result = page.run_js("""
                var chips = document.querySelectorAll('button[class*="ndsChip"]');
                var result = [];
                chips.forEach(function(btn) {
                    var classes = btn.className || '';
                    var aria = (btn.getAttribute('aria-label') || '').trim();
                    var parts = aria.split(',').map(function(part) { return part.trim(); });
                    var rawValue = parts[1] || btn.innerText.trim();
                    var isOutOfStock = /[ ]*-[ ]*out of stock[ ]*$/i.test(rawValue) ||
                        /styles_unavailable/.test(classes);
                    var isSelected = classes.includes('styles_selected') ||
                        classes.includes('styles_sel') ||
                        /,\\s*selected$/i.test(aria);
                    result.push({
                        text: rawValue.replace(/[ ]*-[ ]*out of stock[ ]*$/i, '').trim(),
                        name: parts[0] || '',
                        selected: isSelected,
                        disabled: btn.disabled,
                        out_of_stock: isOutOfStock
                    });
                });
                return JSON.stringify(result);
            """)
            if result:
                return json.loads(result)
        except:
            pass
        return []

    def _get_current_tcin_from_url(self, page):
        """从当前页面 URL 的 preselect 参数提取变体 tcin"""
        try:
            current_url = page.url
            match = re.search(r'preselect=(\d+)', current_url)
            if match:
                return match.group(1)
        except:
            pass
        return None

    def _extract_variant_data_from_dom(
        self, page, url, variations_dict, cached_data=None, parent_price=""
    ):
        """Select each variant's full option combination, then read its price."""
        all_tcins = {str(tcin) for tcin in variations_dict}
        variant_data = dict(cached_data or {})
        if all_tcins.issubset(variant_data):
            print(f"    复用 {len(variant_data)} 个已缓存变体价格")
            return variant_data

        chip_values = self._get_variant_chip_values(page)
        if not chip_values:
            return variant_data

        chip_display = [
            f"{chip.get('name', '')}:{chip['text']}" for chip in chip_values
        ]
        print(f"    找到 {len(chip_values)} 个变体 chip: {chip_display}")

        def normalize(value):
            return re.sub(r"\s+", "", str(value).strip().lower())

        def is_option(chip, name, value):
            return (
                normalize(chip.get("name", "")) == normalize(name)
                and normalize(chip.get("text", "")) == normalize(value)
            )

        def wait_until_selected(name, value):
            current_chips = []
            for _ in range(10):
                time.sleep(0.5)
                current_chips = self._get_variant_chip_values(page)
                if any(
                    chip["selected"] and is_option(chip, name, value)
                    for chip in current_chips
                ):
                    return current_chips
            return current_chips

        def select_variant(props_dict):
            # Color first: Target often enables valid size chips only after its
            # corresponding color swatch has been selected.
            desired_options = list(props_dict.items())
            desired_options.sort(
                key=lambda item: normalize(item[0]) not in {"color", "colour"}
            )
            is_out_of_stock = False
            for option_name, option_value in desired_options:
                current_chips = self._get_variant_chip_values(page)
                matches = [
                    chip for chip in current_chips
                    if is_option(chip, option_name, option_value)
                ]
                if not matches:
                    return False, f"页面没有 {option_name}={option_value}", False
                target_chip = matches[0]
                if target_chip["selected"]:
                    is_out_of_stock = is_out_of_stock or bool(
                        target_chip.get("out_of_stock") or target_chip.get("disabled")
                    )
                    continue
                is_out_of_stock = is_out_of_stock or bool(
                    target_chip.get("out_of_stock") or target_chip.get("disabled")
                )

                clicked = self._click_variant_chip(
                    page, target_chip["text"], target_chip.get("name")
                )
                if not clicked:
                    return False, f"无法点击 {option_name}={option_value}", is_out_of_stock
                self._wait_for_manual_verification(page, url)
                current_chips = wait_until_selected(option_name, option_value)
                if not any(
                    chip["selected"] and is_option(chip, option_name, option_value)
                    for chip in current_chips
                ):
                    return False, f"点击后未选中 {option_name}={option_value}", is_out_of_stock
            return True, "", is_out_of_stock

        selection_failures = {}
        for v_tcin, props_dict in variations_dict.items():
            v_tcin = str(v_tcin)
            if v_tcin in variant_data:
                continue
            selected, reason, is_out_of_stock = select_variant(props_dict)
            if not selected and not is_out_of_stock:
                selection_failures[v_tcin] = reason
                continue

            price = self._extract_price_from_dom(page, retry=1)
            if not price and is_out_of_stock:
                price = parent_price
            if not price:
                selection_failures[v_tcin] = "选中后未提取到价格"
                continue
            price = self._format_price(price)
            variant_data[v_tcin] = {
                "price": price,
                **({"stock": 0} if is_out_of_stock else {}),
            }
            self._cache_variant_price(
                url, v_tcin, price, stock=0 if is_out_of_stock else None
            )
            status = "[缺货变体]" if is_out_of_stock else "[变体]"
            print(f"    {status} tcin={v_tcin}, 价格=${price}")

        unmatched = all_tcins - set(variant_data)
        if unmatched:
            print(f"    [警告] {len(unmatched)} 个变体未匹配: {unmatched}")
            for v_tcin in sorted(unmatched):
                if v_tcin in selection_failures:
                    print(f"      {v_tcin}: {selection_failures[v_tcin]}")

        return variant_data

    def _validate_variant_data(self, variations_dict, variant_data):
        missing_tcins = sorted(
            str(tcin)
            for tcin in variations_dict
            if not self._has_price(variant_data.get(str(tcin), {}).get("price"))
            and variant_data.get(str(tcin), {}).get("stock") != 0
        )
        if missing_tcins:
            raise ValueError(
                "变体提取不完整，未写入商品缓存；缺少价格的 TCIN: "
                + ", ".join(missing_tcins)
            )

    def _extract_next_data(self, page):
        """从页面提取 __NEXT_DATA__ JSON"""
        try:
            result = page.run_js("""
                var script = document.getElementById('__NEXT_DATA__');
                if (script) return script.textContent;
                return null;
            """)
            if result:
                return json.loads(result)
        except:
            pass
        return None

    def _extract_product_node_from_next_data(self, next_data):
        """从 __NEXT_DATA__ 中提取产品节点"""
        if not next_data:
            return {}

        def iter_dicts(obj):
            if isinstance(obj, dict):
                yield obj
                for v in obj.values():
                    yield from iter_dicts(v)
            elif isinstance(obj, list):
                for v in obj:
                    yield from iter_dicts(v)

        for node in iter_dicts(next_data):
            product = node.get("product")
            if isinstance(product, dict) and product.get("tcin") and product.get("item"):
                return product
            data_node = node.get("data.json")
            if isinstance(data_node, dict):
                product = data_node.get("product")
                if isinstance(product, dict) and product.get("tcin") and product.get("item"):
                    return product
            data = node.get("data")
            if isinstance(data, dict):
                modules = data.get("data_source_modules", [])
                for mod in modules:
                    mod_data = mod.get("module_data", {}).get("data", {})
                    if isinstance(mod_data, dict) and mod_data.get("tcin") and mod_data.get("item"):
                        return mod_data
        return {}

    def _extract_images(self, item_data):
        """从 item 节点提取图片"""
        images = []
        img_info = item_data.get("enrichment", {}).get("images") or item_data.get("images", {})
        if img_info.get("primary_image_url"):
            images.append(img_info.get("primary_image_url"))
        images.extend(img_info.get("alternate_image_urls", []))
        image_info = item_data.get("enrichment", {}).get("image_info", {})
        primary_image = image_info.get("primary_image", {})
        if primary_image.get("url"):
            images.append(primary_image.get("url"))
        for image_item in image_info.get("alternate_images", []):
            if image_item.get("url"):
                images.append(image_item.get("url"))
        deduped = []
        seen = set()
        for img in images:
            if not img:
                continue
            if img.startswith("//"):
                img = "https:" + img
            if img in seen:
                continue
            seen.add(img)
            deduped.append(f"{img.split('?')[0]}?wid=1200&hei=1200")
        return deduped

    def _clean(self, txt):
        if not txt:
            return ""
        t = txt.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        t = re.sub(r'<[^>]+>', '', t)
        return html_parser.unescape(t).strip()

    def process_product(self, page, url):
        """处理单个商品页面，返回 CSV 行列表"""

        request_tcin = self._tcin_from_url(url)
        self._wait_for_manual_verification(page, url)
        page.get(url)
        self._wait_for_manual_verification(page, url)
        # 优化: 先等一个较短的基础时间让页面框架加载
        time.sleep(3)
        self._wait_for_manual_verification(page, url)
        # 智能等待价格元素出现（最多 max_wait_price 秒，通常3-5秒就好）
        self._wait_for_price_ready(page)
        self._wait_for_manual_verification(page, url)
        self._save_debug_html(page, request_tcin, request_tcin)
        next_data = self._extract_next_data(page)
        product_node = self._extract_product_node_from_next_data(next_data)
        if not product_node:
            raise ValueError("未找到产品节点")

        item_node = product_node.get("item", {})
        tcin = product_node.get("tcin") or re.search(r'/A-(\d+)', url)
        if isinstance(tcin, type(re.search(r'', ''))):
            tcin = tcin.group(1) if tcin else None


        dom_price = self._extract_price_from_dom(page)

        desc_node = item_node.get("product_description", {})
        product_name = desc_node.get("title") or item_node.get("title") or "Target Product"
        brand_name = (
            item_node.get("primary_brand", {}).get("name")
            or product_node.get("primary_brand", {}).get("name")
            or "clorox"
        )

        price_value = self._format_price(dom_price) if dom_price else ""

        parent_image_list = self._extract_images(item_node)

        child_images_map = {}
        for child in product_node.get("children", []):
            c_tcin = child.get("tcin")
            if c_tcin:
                c_item = child.get("item", {})
                c_images = self._extract_images(c_item)
                if c_images:
                    child_images_map[str(c_tcin)] = c_images

        variations_dict = {}
        def collect_variations(nodes, inherited_props=None):
            if inherited_props is None:
                inherited_props = []
            if not isinstance(nodes, list):
                return
            for v in nodes:
                if not isinstance(v, dict):
                    continue
                props = list(inherited_props)
                v_name = v.get("name")
                v_value = v.get("value")
                if v_name and v_value:
                    props.append((v_name, v_value))
                v_tcin = v.get("tcin")
                if v_tcin and props:
                    variations_dict.setdefault(str(v_tcin), {})
                    for prop_name, prop_value in props:
                        variations_dict[str(v_tcin)][prop_name] = prop_value
                child_nodes = v.get("variation_hierarchy") or v.get("children") or []
                collect_variations(child_nodes, props)
        collect_variations(product_node.get("variation_hierarchy", []))

        # Details
        detail_data = {"highlights": [], "description": ""}
        detail_data["highlights"] = desc_node.get("soft_bullets", {}).get("bullets", []) if desc_node.get("soft_bullets") else []
        raw_desc = desc_node.get("downstream_description") or ""
        if not detail_data["highlights"] or not raw_desc:
            for child in product_node.get("children", []):
                c_desc = child.get("item", {}).get("product_description", {})
                if not detail_data["highlights"]:
                    c_bullets = c_desc.get("soft_bullets", {}).get("bullets", [])
                    if c_bullets:
                        detail_data["highlights"] = c_bullets
                if not raw_desc:
                    c_desc_text = c_desc.get("downstream_description", "")
                    if c_desc_text:
                        raw_desc = c_desc_text
                if detail_data["highlights"] and raw_desc:
                    break
        detail_data["description"] = self._clean(raw_desc)

        # Nutrition
        nutrition = item_node.get("nutrition_facts") or item_node.get("enrichment", {}).get("nutrition_facts", {})
        label_info = {
            "ingredients": self._clean(nutrition.get("ingredients", "")),
            "allergens": self._clean(nutrition.get("warning", "")),
            "nutrition": {"size": "", "servings": "", "calories": "", "nutrients": []}
        }
        prep_list = nutrition.get("value_prepared_list", [])
        if prep_list:
            p = prep_list[0]
            label_info["nutrition"]["size"] = f"{p.get('serving_size', '')} {p.get('serving_size_unit_of_measurement', '')}".strip()
            label_info["nutrition"]["servings"] = p.get("servings_per_container", "")
            for n in p.get("nutrients", []):
                if n.get('name') == 'Calories':
                    label_info["nutrition"]["calories"] = n.get('quantity')
                else:
                    pct = n.get("percentage")
                    label_info["nutrition"]["nutrients"].append({
                        "name": n.get("name"),
                        "amount": f"{n.get('quantity', '')}{n.get('unit_of_measurement', '')}".strip(),
                        "dv": f"{pct}%" if pct is not None else ""
                    })

        # Specs
        specs_list = [self._clean(b) for b in desc_node.get("bullet_descriptions", [])]
        if tcin:
            specs_list.append(f"TCIN: {tcin}")
        upc = item_node.get("primary_barcode")
        if upc:
            specs_list.append(f"UPC: {upc}")
        dpci = product_node.get("dpci") or item_node.get("dpci")
        if dpci:
            specs_list.append(f"Item Number (DPCI): {dpci}")
        origin = item_node.get("handling", {}).get("import_designation_description")
        if origin:
            specs_list.append(f"Origin: {origin}")

        # HTML
        h_li = "".join([f"<li style='margin-bottom: 12px; color: #333;'>{h}</li>" for h in detail_data['highlights']])
        d_br = detail_data['description'].replace('\n', '<br>')
        html_details = f"""<div style="display: flex; flex-wrap: wrap; gap: 40px; padding: 20px 0;"><div style="flex: 1; min-width: 300px;"><h3 style="font-size: 18px; margin-bottom: 15px; color: #333;">Highlights</h3><ul style="padding-left: 20px; line-height: 1.5; font-size: 14px;">{h_li}</ul></div><div style="flex: 1; min-width: 300px;"><h3 style="font-size: 18px; margin-bottom: 15px; color: #333;">Description</h3><p style="line-height: 1.6; font-size: 14px; color: #333;">{d_br}</p></div></div>"""

        nutri = label_info['nutrition']
        n_rows = "".join([f"<tr><td style='padding: 10px 0; border-bottom: 1px solid #eee; font-size: 14px; color: #333;'><strong>{n['name']}</strong> {n['amount']}</td><td style='padding: 10px 0; border-bottom: 1px solid #eee; text-align: right; font-size: 14px; color: #333;'>{n['dv']}</td></tr>" for n in nutri['nutrients']])
        html_label = f"""<div style="display: flex; flex-wrap: wrap; gap: 60px; padding: 20px 0;"><div style="flex: 1; min-width: 300px; max-width: 450px;"><p style="margin: 4px 0; font-size: 14px; color: #333;"><strong>Serving Size:</strong> {nutri['size']}</p><p style="margin: 4px 0; font-size: 14px; color: #333;"><strong>Serving Per Container:</strong> {nutri['servings']}</p><p style="margin: 4px 0; font-size: 14px; color: #333;"><strong>Amount Per Serving:</strong></p><div style="border-bottom: 4px solid #e0e0e0; margin: 8px 0;"></div><p style="margin: 4px 0; font-size: 14px; color: #333;"><strong>Calories:</strong> {nutri['calories']}</p><table style="width: 100%; border-collapse: collapse; margin-top: 10px;"><tr><th colspan="2" style="text-align: right; border-bottom: 1px solid #333; padding-bottom: 4px; font-size: 12px; color: #333;">% Daily Value*</th></tr>{n_rows}</table><p style="font-size: 12px; margin-top: 8px; color: #333;">* Percentage of Daily Values are based on a 2,000 calorie diet.</p></div><div style="flex: 1; min-width: 300px;"><h3 style="font-size: 16px; margin-bottom: 10px; color: #333;">Ingredients:</h3><p style="line-height: 1.6; font-size: 14px; color: #333;">{label_info['ingredients']}</p><h3 style="font-size: 16px; margin-bottom: 10px; color: #333; margin-top: 20px;">Allergens:</h3><p style="line-height: 1.6; font-size: 14px; color: #333;">{label_info['allergens'] or 'N/A'}</p></div></div>"""

        s_li = ""
        for spec in specs_list:
            parts = spec.split(":", 1)
            formatted_spec = f"<strong>{parts[0]}:</strong>{parts[1]}" if len(parts) == 2 else spec
            s_li += f"<li style='padding: 16px 0; border-bottom: 1px solid #eaeaea; font-size: 14px; color: #333;'>{formatted_spec}</li>"
        html_specs = f"""<div style="padding: 20px 0;"><ul style="list-style: none; padding: 0; margin: 0;">{s_li}</ul><div style="margin-top: 24px;"><p style="font-weight: bold; margin-bottom: 4px; font-size: 14px; color: #333;">Grocery Disclaimer:</p><p style="font-size: 13px; line-height: 1.6; color: #333;">{self._clean(item_node.get("disclaimer", {}).get("description", ""))}</p></div></div>"""

        results = []
        parent_sku = str(tcin) if tcin else url.split('/')[-1]

        extract_all_variants = bool(variations_dict) and self.should_extract_all_variants(
            product_node, variations_dict
        )
        if not extract_all_variants:
            results.append({
                "Type": "simple", "SKU": parent_sku, "Name": product_name,
                "Description": html_details,
                "Label info (product.metafields.c_f.label_info)": html_label,
                "Specifications (product.metafields.c_f.specifications)": html_specs,
                "Sale price": price_value, "Regular price": price_value,
                "Categories": "DefaultCategory", "Tags": "",
                "Images": self.Tool.config.images_split.join(parent_image_list), "Parent": "",
                "brand": brand_name, "Stock": 1000.00, "is_upload": 0
            })
        else:
            print(f"    开始提取变体数据 (共 {len(variations_dict)} 个变体)...")
            expected_tcins = {str(tcin) for tcin in variations_dict}
            cached_data = self._cached_variant_data(url, expected_tcins)
            variant_data = self._extract_variant_data_from_dom(
                page, url, variations_dict, cached_data, parent_price=price_value
            )
            self._validate_variant_data(variations_dict, variant_data)

            for v_tcin, props_dict in variations_dict.items():
                props_items = list(props_dict.items())
                sku_suffix = "-".join([val for name, val in props_items])
                variation_sku = f"{parent_sku}-{sku_suffix}"

                v_info = variant_data.get(str(v_tcin), {})
                v_price = self._format_price(v_info["price"])

                v_images = child_images_map.get(str(v_tcin), [])
                if not v_images:
                    v_images = parent_image_list

                row = {
                    "Type": "variation", "SKU": variation_sku, "Name": product_name,
                    "Description": html_details,
                    "Label info (product.metafields.c_f.label_info)": html_label,
                    "Specifications (product.metafields.c_f.specifications)": html_specs,
                    "Sale price": v_price, "Regular price": v_price,
                    "Categories": "DefaultCategory",
                    "Images": self.Tool.config.images_split.join(v_images), "Parent": parent_sku,
                    "brand": brand_name, "Stock": v_info.get("stock", 1000.00), "is_upload": 0
                }
                if len(props_items) > 0:
                    row["Attribute 1 name"] = props_items[0][0]
                    row["Attribute 1 value(s)"] = props_items[0][1]
                if len(props_items) > 1:
                    row["Attribute 2 name"] = props_items[1][0]
                    row["Attribute 2 value(s)"] = props_items[1][1]
                results.append(row)

        return results

    def fetch_product(self, url, category):
        """Navigate with the configured DrissionPage backend, then parse unchanged template logic."""
        tab = self.get_tab()
        try:
            ls = self.process_product(tab, url)
            return ls
        except Exception as e:
            print(f'获取产品失败:{e}')
            return []


    def close(self):
        for tab in self.tab_ls:
            tab.close()

        try:
            self.browser.close()
        finally:
            pass

    def _flush_variant_cache(self):
        with self._variant_cache_lock:
            if self._variant_cache_changes_since_save:
                self._save_variant_cache_locked()


    def run(self):
        try:
            return super().run()
        finally:
            self._flush_variant_cache()
            self.close()




__all__ = ["Get_Product"]
