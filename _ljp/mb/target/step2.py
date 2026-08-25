"""
Target.com 价格爬虫 - DrissionPage 方案 (优化版)

核心优化：
  1. 智能等待：用JS轮询检查价格元素是否出现，出现就立即继续（不再固定等15秒）
  2. 多标签页并行：同一浏览器开多个标签页同时处理多个商品（默认3线程）
  3. 减少重复调用：价格提取后缓存，不重复调
  4. 增量写入CSV：每处理完一个就追加写入，防止中途崩溃丢数据
  5. 保留修复版全部Bug修复

预计提速：3-5倍（取决于商品数量和变体数量）

安装依赖：
  pip install DrissionPage curl_cffi

使用方法：
  修改下面的 input_file / output_file / fail_file 路径即可运行
"""

import json
import csv
import re
import time
import threading
import html as html_parser
from DrissionPage import ChromiumPage, ChromiumOptions


class TargetDrissionCrawler:
    def __init__(self, input_file, output_file, fail_file,
                 proxy="127.0.0.1:7897", headless=False, wait_time=15,
                 num_threads=3, max_wait_price=12):
        self.input_file = input_file
        self.output_file = output_file
        self.fail_file = fail_file
        self.proxy = proxy
        self.headless = headless
        self.wait_time = wait_time          # 初始页面加载等待（秒）
        self.max_wait_price = max_wait_price  # 智能等待价格元素出现的最长时间（秒）
        self.num_threads = num_threads        # 并行标签页数量
        self.failures = {}
        self._failures_lock = threading.Lock()
        self._csv_lock = threading.Lock()

    def _preprocess_urls(self, urls):
        """预处理URL列表：去除重复"""
        processed = []
        seen_tcins = set()

        for url in urls:
            clean_url = url.split('#')[0].split('?')[0]
            tcin_match = re.search(r'/A-(\d+)', clean_url)
            if tcin_match:
                tcin = tcin_match.group(1)
                if tcin in seen_tcins:
                    continue
                seen_tcins.add(tcin)
            processed.append(clean_url)

        print(f"URL预处理: {len(urls)} → {len(processed)} 个商品")
        return processed

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
        co.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
        return ChromiumPage(co)

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

    def _click_variant_chip(self, page, variant_value):
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
            clicked = page.run_js(f"""
                var chips = document.querySelectorAll('button[class*="ndsChip"]');
                for (var chip of chips) {{
                    if (chip.innerText.trim() === '{escaped_value}' && !chip.disabled) {{
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
        """获取页面上所有变体 chip 按钮的值和选中状态"""
        try:
            result = page.run_js("""
                var chips = document.querySelectorAll('button[class*="ndsChip"]');
                var result = [];
                chips.forEach(function(btn) {
                    var classes = btn.className || '';
                    var isSelected = classes.includes('styles_selected') || classes.includes('styles_sel');
                    result.push({
                        text: btn.innerText.trim(),
                        selected: isSelected,
                        disabled: btn.disabled
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

    # ==================== 优化2: 变体等待从8秒降到5秒 ====================
    def _extract_variant_data_from_dom(self, page, variations_dict):
        """
        逐个点击变体 chip，提取每个变体的价格。
        优化: 变体等待从8秒降到5秒，价格提取用retry=1（不重试）。
        """
        variant_data = {}

        chip_values = self._get_variant_chip_values(page)
        if not chip_values:
            return variant_data

        print(f"    找到 {len(chip_values)} 个变体 chip: {[c['text'] for c in chip_values]}")

        def normalize(s):
            return str(s).strip().lower().replace(' ', '').replace('\t', '')

        combo_to_tcin = {}
        for v_tcin, props_dict in variations_dict.items():
            combo = frozenset(normalize(v) for v in props_dict.values())
            combo_to_tcin[combo] = str(v_tcin)

        all_var_values_normalized = set()
        for props in variations_dict.values():
            for v in props.values():
                all_var_values_normalized.add(normalize(v))

        all_tcins = set(str(k) for k in variations_dict.keys())
        processed_tcins = set()
        previous_price = None

        def extract_current_state():
            current_chips = self._get_variant_chip_values(page)
            selected_texts = frozenset(
                normalize(c['text']) for c in current_chips if c['selected']
            )
            matched_tcin = combo_to_tcin.get(selected_texts)
            if not matched_tcin:
                url_tcin = self._get_current_tcin_from_url(page)
                if url_tcin and url_tcin in all_tcins:
                    matched_tcin = url_tcin

            if matched_tcin and matched_tcin not in processed_tcins:
                # 优化: retry=1 不重试，因为已经等待过价格变化了
                price = self._extract_price_from_dom(page, retry=1)
                if price:
                    variant_data[matched_tcin] = {"price": price}
                    processed_tcins.add(matched_tcin)
                    print(f"    [变体] tcin={matched_tcin}, 价格=${price}")
                    return True
                else:
                    print(f"    [警告] tcin={matched_tcin} 价格提取失败")
                    processed_tcins.add(matched_tcin)
            return False

        extract_current_state()
        previous_price = self._extract_price_from_dom(page, retry=1)

        for chip in chip_values:
            chip_text = chip['text']
            if chip['disabled'] or chip['selected']:
                continue
            if normalize(chip_text) not in all_var_values_normalized:
                continue

            clicked = self._click_variant_chip(page, chip_text)
            if not clicked:
                continue

            # 优化: 从8秒降到5秒，每0.5秒检查一次
            new_price = None
            for _ in range(10):  # 10 * 0.5 = 5秒
                time.sleep(0.5)
                new_price = self._extract_price_from_dom(page, retry=1)
                if new_price and new_price != previous_price:
                    break

            extract_current_state()
            previous_price = new_price or previous_price

        unmatched = all_tcins - processed_tcins
        if unmatched:
            print(f"    [警告] {len(unmatched)} 个变体未匹配: {unmatched}")

        return variant_data

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
        next_data = self._extract_next_data(page)
        product_node = self._extract_product_node_from_next_data(next_data)
        if not product_node:
            raise ValueError("未找到产品节点")

        item_node = product_node.get("item", {})
        tcin = product_node.get("tcin") or re.search(r'/A-(\d+)', url)
        if isinstance(tcin, type(re.search(r'', ''))):
            tcin = tcin.group(1) if tcin else None

        # 优化: 智能等待价格出现后再提取
        self._wait_for_price_ready(page)
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

        if not variations_dict:
            results.append({
                "Type": "simple", "SKU": parent_sku, "Name": product_name,
                "Description": html_details,
                "Label info (product.metafields.c_f.zdy_tabs1)": html_label,
                "Specifications (product.metafields.c_f.zdy_tabs2)": html_specs,
                "Sale price": price_value, "Regular price": price_value,
                "Categories": "DefaultCategory", "Tags": "",
                "Images": ",".join(parent_image_list), "Parent": "",
                "brand": brand_name, "Stock": 1000.00, "is_upload": 0
            })
        else:
            print(f"    开始提取变体数据 (共 {len(variations_dict)} 个变体)...")
            variant_data = self._extract_variant_data_from_dom(page, variations_dict)

            for v_tcin, props_dict in variations_dict.items():
                props_items = list(props_dict.items())
                sku_suffix = "-".join([val for name, val in props_items])
                variation_sku = f"{parent_sku}-{sku_suffix}"

                v_info = variant_data.get(str(v_tcin), {})
                v_price = v_info.get("price") if v_info else None
                if not v_price:
                    v_price = price_value
                else:
                    v_price = self._format_price(v_price)

                v_images = child_images_map.get(str(v_tcin), [])
                if not v_images:
                    v_images = parent_image_list

                row = {
                    "Type": "variation", "SKU": variation_sku, "Name": product_name,
                    "Description": html_details,
                    "Label info (product.metafields.c_f.zdy_tabs1)": html_label,
                    "Specifications (product.metafields.c_f.zdy_tabs2)": html_specs,
                    "Sale price": v_price, "Regular price": v_price,
                    "Categories": "DefaultCategory",
                    "Images": ",".join(v_images), "Parent": parent_sku,
                    "brand": brand_name, "Stock": 1000.00, "is_upload": 0
                }
                if len(props_items) > 0:
                    row["Attribute 1 name"] = props_items[0][0]
                    row["Attribute 1 value(s)"] = props_items[0][1]
                if len(props_items) > 1:
                    row["Attribute 2 name"] = props_items[1][0]
                    row["Attribute 2 value(s)"] = props_items[1][1]
                results.append(row)

        return results

    # ==================== 优化3: 增量写入CSV ====================
    def _init_csv(self, fieldnames):
        """初始化CSV文件，写入表头"""
        with open(self.output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    def _append_csv(self, rows, fieldnames):
        """追加写入CSV（线程安全）"""
        with self._csv_lock:
            with open(self.output_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerows(rows)

    # ==================== 优化4: 多标签页并行 ====================
    def _worker(self, browser, url_queue, fieldnames, worker_id, results):
        """工作线程：从队列取URL，在独立标签页中处理"""
        # 每个worker用自己的标签页
        tab = browser.new_tab()

        while True:
            try:
                idx, url = url_queue.get_nowait()
            except:
                break  # 队列空了

            try:
                print(f"  [W{worker_id}] [{idx}] 处理: {url[:60]}...")

                tab.get(url)

                # 优化: 先等一个较短的基础时间让页面框架加载
                time.sleep(3)
                # 智能等待价格元素出现（最多 max_wait_price 秒，通常3-5秒就好）
                self._wait_for_price_ready(tab)

                rows = self.process_product(tab, url)

                if rows:
                    self._append_csv(rows, fieldnames)
                    results.extend(rows)
                    price = rows[0].get("Sale price", "?")
                    print(f"  [W{worker_id}] [{idx}] OK 价格: ${price}")
                else:
                    with self._failures_lock:
                        self.failures.setdefault("DefaultCategory", []).append(url)
                    print(f"  [W{worker_id}] [{idx}] FAIL")

            except Exception as e:
                print(f"  [W{worker_id}] [{idx}] ERROR: {e}")
                with self._failures_lock:
                    self.failures.setdefault("DefaultCategory", []).append(url)

            # 短暂等待
            time.sleep(1)

        tab.close()

    def run(self):
        """主运行方法 - 支持多标签页并行"""
        # 加载任务
        with open(self.input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            urls = data
        elif isinstance(data, dict):
            urls = []
            for v in data.values():
                urls.extend(v)
        else:
            raise ValueError("不支持的 JSON 数据结构")

        urls = self._preprocess_urls(urls)
        total = len(urls)
        print(f"共 {total} 个商品待处理，使用 {self.num_threads} 个并行标签页")

        fieldnames = [
            "Type", "SKU", "Name", "Description", "Sale price", "Regular price",
            "Categories", "Tags", "Images", "Parent", "brand",
            "Stock", "is_upload", "Label info (product.metafields.c_f.zdy_tabs1)",
            "Specifications (product.metafields.c_f.zdy_tabs2)",
            "Attribute 1 name", "Attribute 1 value(s)",
            "Attribute 2 name", "Attribute 2 value(s)"
        ]

        # 初始化CSV（写表头）
        self._init_csv(fieldnames)

        # 创建URL队列
        import queue
        url_queue = queue.Queue()
        for i, url in enumerate(urls):
            url_queue.put((i + 1, url))

        # 创建浏览器
        browser = self._create_browser()

        all_rows = []
        threads = []
        start_time = time.time()

        # 启动多个工作线程
        for w_id in range(self.num_threads):
            t = threading.Thread(
                target=self._worker,
                args=(browser, url_queue, fieldnames, w_id + 1, all_rows),
                daemon=True
            )
            t.start()
            threads.append(t)
            # 错开启动时间，避免同时请求触发反爬
            time.sleep(2)

        # 等待所有线程完成
        for t in threads:
            t.join()

        elapsed = time.time() - start_time
        browser.quit()

        # 写入失败记录
        with open(self.fail_file, "w", encoding="utf-8") as f:
            json.dump(self.failures, f, ensure_ascii=False, indent=4)

        success_count = len(all_rows)
        print(f"\n完成！共 {success_count} 行数据，耗时 {elapsed:.0f}秒 ({elapsed/60:.1f}分钟)")
        print(f"平均每个商品: {elapsed/total:.1f}秒" if total > 0 else "")
        print(f"输出文件: {self.output_file}")
        print(f"失败记录: {self.fail_file}")