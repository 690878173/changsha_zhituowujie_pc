import csv
import json
import os
import re
import threading
from queue import Queue
from urllib.parse import urlparse

from lxml import etree

from config import Tool, images_split

# ============================================================
# 运行配置
# ============================================================
max_threads = 1                   # 并发线程数
ts_num = None                     # 测试数据条数（None = 全部抓取）
BRAND_NAME = Tool.site       # 品牌名称

# ============================================================
# 文件路径
# ============================================================
input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site("data/result.csv")
fail_file = Tool.File.path_add_site("data/fail.json")
catch_path = Tool.File.path_add_site('hc/3.json')
output_ts_file = Tool.File.path_add_site('hc/result.csv')

# 跳过的 URL
skip_urls = [
    'https://www.roguefitness.com/rogue-curl-bar-stainless-steel',
    'https://www.roguefitness.com/rogue-hd-concrete-anchors',
    'https://www.roguefitness.com/monster-rig-2-0?sku=RF0330',
    'https://www.roguefitness.com/rogue-monster-lat-pull-low-row-trainer-add-on',
    'https://www.roguefitness.com/mutant-metals-handles?b=1136952',
    'https://www.roguefitness.com/slml-6-monster-weight-stack-slinger',
    'https://www.roguefitness.com/nunchuck-grips',
    'https://www.roguefitness.com/rogue-echo-rings',
    'https://www.roguefitness.com/bella-bar-custom',
    'https://www.roguefitness.com/ohio-bar-custom',
    'https://www.roguefitness.com/ohio-power-bar-custom',
    'https://www.roguefitness.com/monster-mass-storage',
    'https://www.roguefitness.com/rogue-loop-bands',
    'https://www.roguefitness.com/rml-390f-flat-foot-monster-lite-rack',
    'https://www.roguefitness.com/sml-1-rogue-70-monster-lite-squat-stand',
    'https://www.roguefitness.com/rogue-rm-6-bolt-together-monster-rack-2-0?b=1133879-1134832-3698-3700-3689-18851-1134828-67432',
    'https://www.roguefitness.com/goruck-basic-rucker?sku=GR0176-B',  # 背包
    'https://www.roguefitness.com/rogue-fml-hr-functional-trainer?b=1135882-1131818-7225-1133633-39347-1139612',
]

# 模糊匹配：URL 含这些关键词就跳过（定制商品、组合货架等）
skip_url_patterns = ['custom', 'ml-squat-stands']

fieldnames = [
    "Type", "SKU", "Name", "Description", "Sale price", "Regular price",
    "Categories", "Tags", "Images", "Parent",
    "Attribute 1 name", "Attribute 1 value(s)", "brand", "Attribute 2 name", "Attribute 2 value(s)",
    "Stock", "is_upload"
]

IMG_BASE_URL = 'https://assets.roguefitness.com/f_auto,q_auto,c_limit,w_1960,b_rgb:f8f8f8'

# ============================================================
# RogueFitness 专用：__INITIAL_STATE__ 解析辅助函数
# ============================================================

class ProductManager:
    """管理从 __INITIAL_STATE__ 解析出的全部产品数据。

    - 保留每个产品的完整原始数据
    - 支持按 ID 查找产品、子产品、父产品
    - 自动构建 parent 反向索引（子 → 父）
    """

    def __init__(self, products: dict):
        self._products: dict[str, dict] = {str(k): v for k, v in products.items()}
        self._parent_of: dict[str, str] = {}
        for pid, p in self._products.items():
            for child_id in p.get('childrenIds', []):
                self._parent_of[str(child_id)] = pid

    # ---- 基础查询 ----

    def get(self, product_id) -> dict | None:
        """按 ID 获取产品完整原始数据"""
        return self._products.get(str(product_id))

    def __getitem__(self, product_id):
        return self._products[str(product_id)]

    def __contains__(self, product_id):
        return str(product_id) in self._products

    def __len__(self):
        return len(self._products)

    def iter_all(self):
        return self._products.values()

    # ---- 父子关系 ----

    def get_children(self, product_id) -> list[dict]:
        """获取直接子产品列表（保留完整数据）"""
        product = self.get(product_id)
        if not product:
            return []
        return [
            self._products[str(cid)]
            for cid in product.get('childrenIds', [])
            if str(cid) in self._products
        ]

    def get_children_by_name(self, product_id) -> dict[str, dict]:
        """获取子产品，按 name 索引"""
        return {c['name']: c for c in self.get_children(product_id)}

    def get_parent(self, product_id) -> dict | None:
        """获取父产品（完整数据）"""
        parent_id = self._parent_of.get(str(product_id))
        return self._products.get(parent_id) if parent_id else None

    def get_root(self, product_id) -> dict:
        """沿 parent 链向上找到最顶层产品"""
        current = self[str(product_id)]
        while True:
            parent = self.get_parent(current['productId'])
            if parent is None:
                return current
            current = parent

    def get_lineage(self, product_id) -> list[dict]:
        """获取从根到当前产品的完整链路"""
        chain = [self[str(product_id)]]
        while True:
            parent = self.get_parent(chain[-1]['productId'])
            if parent is None:
                break
            chain.append(parent)
        chain.reverse()
        return chain

    # ---- 解析辅助 ----

    def parse_product_tree(self, product_id, code_ls: list[str], rt_dict: dict | None = None) -> dict:
        """递归解析产品树，返回简化结构的嵌套 dict（兼容旧 parse_child 输出格式）"""
        if rt_dict is None:
            rt_dict = {}

        product = self[str(product_id)]
        node = {
            'name':       product['name'],
            'sku':        product['sku'],
            'imgs':       [i for i in [product.get('image', '')] + [i['link'] for i in product.get('gallery', [])] if i],
            'price':      product['price'],
            'type':       product['type'],
            'childs':     {},
            'attributes': {code: product['attributes'].get(code) for code in code_ls},
        }

        if product['type'] != 'simple' and product.get('childrenIds'):
            node['childs_id'] = [str(cid) for cid in product['childrenIds']]
            for child_id in node['childs_id']:
                node['childs'][child_id] = self.parse_product_tree(child_id, code_ls)[child_id]

        rt_dict[str(product_id)] = node
        return rt_dict

def resolve(flat_data: list, idx, cache: dict):
    """递归解引用：从 flat_data 的 idx 位置取出值并还原为嵌套结构，增加缓存避免重复解析。"""
    if not isinstance(idx, int):
        return idx

    if idx in cache:
        return cache[idx]

    value = flat_data[idx]
    if isinstance(value, list):
        parsed = [resolve(flat_data, item, cache) for item in value]
        cache[idx] = parsed
        return parsed
    if isinstance(value, dict):
        parsed = {k: resolve(flat_data, v, cache) for k, v in value.items()}
        cache[idx] = parsed
        return parsed

    # 基础类型直接缓存
    cache[idx] = value
    return value

def resolve_all(filepath):
    """读取 JSON 文件并还原所有模块数据。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    flat_data = json.loads(raw['pinia'])
    index = flat_data[0]

    result = {}
    cache = {}
    for module_name, start_idx in index.items():
        result[module_name] = resolve(flat_data, start_idx, cache)

    return result


def _par_reviews(data, pm: ProductManager):
    """从 reviews 数据中反向查找主产品 ID"""
    sku = list(data['reviews']['reviews'].keys())[0]
    for product in pm.iter_all():
        if str(product['sku']) == str(sku):
            return str(product['productId'])
    return None


def _parse_tabs(nodes):
    """从配置选项卡中提取属性 code 列表"""
    code_ls = []
    for div in nodes:
        for cfg in div.xpath('./div[@class="configure"]/div[@class="configuration"]/div'):
            code = cfg.get('data-attr')
            if code:
                code_ls.append(code)
    return code_ls


def _should_skip_url(url):
    """检查是否需要跳过该 URL（精确匹配 + 模糊匹配）"""
    if url in skip_urls:
        return True
    if any(pattern in url for pattern in skip_url_patterns):
        return True
    return False


def _find_product_by_url(url, pm: ProductManager) -> str | None:
    """兜底：通过 URL 路径在产品数据中匹配产品 ID。
    
    RogueFitness URL 格式: https://www.roguefitness.com/{product-handle}
    尝试将 URL handle 与产品 name 做模糊匹配（转小写、空格换横线）。
    """
    path = urlparse(url).path.strip('/')
    if not path:
        return None
    handle = path.split('/')[-1].lower()

    for product in pm.iter_all():
        name_slug = product.get('name', '').lower().replace(' ', '-').replace('/', '-')
        if handle in name_slug or name_slug in handle:
            return str(product['productId'])

    return None


def _fallback_parse_tree(pm: ProductManager, product_id, url, desc):
    """兜底提取：HTML 结构无法识别时，直接用 __INITIAL_STATE__ 解析产品树。
    
    不依赖 HTML 属性 code，捕获完整的父子产品关系（name/sku/price/images）。
    """
    Tool.print(f'兜底解析(无HTML变体信息):{url}')
    root = pm.get_root(product_id)
    root_id = str(root['productId'])
    # 空 code_ls：不按属性过滤，保留全部子产品
    res = pm.parse_product_tree(root_id, [])
    Tool.File.save_json(res, 'cs/product_res_fallback.json')
    return res

def get_detail_page(url, category, res_text) -> list[dict] | None:
    """RogueFitness 站点解析

    页面类型（由 id_div class 区分）：
      product-card         → Set/Pair 套装（_parse_grouped_variants）
      rhpa type-simple     → 简单单SKU商品（直接返回）
      rhpa type-configurable → 标准多选项商品（parse_product_tree）
      rhpa-child 无分隔符   → 普通分组子产品（parse_product_tree）
      rhpa-child 有分隔符   → 组合商品（跳过）
      其他                  → 未知定制商品（跳过）
    """

    # ---- 0. 前置过滤 ----
    if _should_skip_url(url):
        return None

    html = etree.HTML(res_text)

    # ---- 1. 提取描述 ----
    desc = ''
    need_ls = ['Product Description', 'Gear Specs']
    try:
        tab_dic = {}
        for i in need_ls:
            _tag = html.xpath(f'//div[@tab="{i}"]')
            if _tag:
                tab_dic[i] = Tool.HTML.del_a_href_to_str(_tag[0])
        desc = tab_dic.get('Product Description', '')
    except Exception:
        Tool.print(f'获取详细页面失败:url:{url}')

    # ---- 2. 解析 __INITIAL_STATE__ ----
    pattern = re.compile(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*', re.DOTALL)
    match = pattern.search(res_text)
    if not match:
        Tool.print("未匹配到__INITIAL_STATE__，静态页面无内嵌数据！")
        return None

    json_raw = match.group(1)
    data = json.loads(json_raw)
    Tool.File.save_json(data, 'cs/raw.json')

    try:
        data = resolve_all(Tool.File.path_add_site('cs/raw.json'))
    except Exception as e:
        Tool.print(f'读取json失败,数据结构不同,原因:{e},url:{url}')
        return None

    Tool.File.save_json(data, 'cs/解析数据.json')
    pm = ProductManager(data['products']['products'])

    # ---- 3. 获取产品 ID ----
    product_id = None
    id_divs = html.xpath('//div[@data-cnstrc-item-id]')
    if not id_divs:
        # 兜底：没有 id_div，尝试用 URL 反查产品
        product_id = _find_product_by_url(url, pm)
        if product_id:
            Tool.print(f'无id标签,URL反查成功:{url}')
            return _fallback_parse_tree(pm, product_id, url, desc)
        Tool.print(f'没有id标签且URL反查失败:{url}')
        return None

    id_div = id_divs[0]
    product_id = str(id_div.get('data-cnstrc-item-id'))
    id_div_name = id_div.get('class')

    # ---- 4. 查找产品数据 ----
    try:
        product = pm[product_id]
    except KeyError:
        # 尝试通过 reviews 反查产品 ID
        product_id = _par_reviews(data, pm)
        if not product_id:
            # 兜底：URL 反查
            product_id = _find_product_by_url(url, pm)
            if product_id:
                Tool.print(f'找不到产品id,URL反查成功:{url}')
                return _fallback_parse_tree(pm, product_id, url, desc)
            Tool.print(f'找不到产品id且URL反查失败:{url}')
            return None
        return _parse_grouped_variants(html, pm, product_id, url, data, desc, category)

    # ---- 5. 按页面类型分发 ----
    code_ls = []

    if id_div_name == 'product-card':
        return _parse_grouped_variants(html, pm, product_id, url, data, desc, category)

    elif id_div_name == 'rhpa type-simple':
        price = id_div.get('data-cnstrc-item-price')
        return Tool.Product.build_products(
            name=product['name'], sku=product['sku'], desc=desc,
            price=price, url=url, category=category,
            common_images=_build_images(product), combos=None,
        )

    elif id_div_name == 'rhpa type-configurable':
        rhpa_opts = id_div.xpath('.//div[@class="rhpa-body"]/div[@class="rhpa-opts"]')
        code_ls.extend(_parse_tabs(rhpa_opts))

    elif id_div_name == 'rhpa-child':
        id_div_parent = id_div.getparent()
        if id_div_parent.get('class') != 'rhpa-opts option grouped-rhpa':
            # 兜底：非标准 grouped 子产品
            return _fallback_parse_tree(pm, product_id, url, desc)

        _parent = id_div_parent.getparent()

        if _parent.xpath('./div[@class="divider"]'):
            # 兜底：组合商品（有分隔符），HTML 结构太复杂，用 INITIAL_STATE 兜底
            return _fallback_parse_tree(pm, product_id, url, desc)

        # 无分隔符 = 普通分组子产品
        tabs = _parent.xpath('./div[@class="rhpa-opts option grouped-rhpa"]')
        code_ls.extend(_parse_tabs(tabs))

    else:
        # 兜底：未知页面类型
        return _fallback_parse_tree(pm, product_id, url, desc)

    # ---- 6. 递归解析产品树 ----
    code_ls = list(set(code_ls))
    res = pm.parse_product_tree(product_id, code_ls)
    Tool.File.save_json(res, 'cs/product_res.json')
    return res


def _build_images(product: dict) -> list[str]:
    """拼接产品图片 URL 列表"""
    gallery = [i['link'] for i in product.get('gallery', [])]
    sources = [product.get('image', '')] + gallery
    return [IMG_BASE_URL + src for src in sources if src]


def _parse_grouped_variants(html, pm: ProductManager, product_id, url, data, desc, category):
    """解析 Set/Pair 套装类产品的变体信息（KeyError 和 product-card 分支共用）"""
    fl_product = pm[product_id]
    fl_name = fl_product['name']
    fl_sku = fl_product['sku']
    fl_price = fl_product['price']
    fl_imgs = _build_images(fl_product)

    sam_dic = {}
    sam_type = ''
    samp_products = pm.get_children_by_name(product_id)
    opts = html.xpath(
        '//div[@class="rhpa-opts option grouped-rhpa"]'
        '//div[@class="rhpa-child"]//div[@class="top"]'
    )
    _size = 'size'
    _num = 'Num'
    _set = 'Set'
    sam_type_dic = {
        'Rogue JC' : _size,
        'Climbing Rope':_size,
        'Set' : _set,
        "Pair": "Pair",
        'Rogue Ring' : _num,
        'CrossFit Games - Used Color Competition Plate' :_size,
        # '2020 CrossFit Games - Used Color Competition Plate' : _size,
        # '2016 CrossFit Games - Used Color Competition Plate':_size,
        # '2023 CrossFit Games - Used Color Competition Plate':_size,
        'Monster Plate Storage Channe': _num,
        'Ohio Power Bar' : _size,
        'Monster Lite/Infinity': 'Way',
        'Boneyard': _set,
        'Rogue 2014 Legacy Plate': _size,
        'Mutt Bar - 22':_size,
        'Competition Plate - From Games':_size,
        'CrossFit Games - Color Competition Plate':_size,
        'Plate Storage':_size,
        'Tier Universal Storage System 2.0':_size,
        'Monster Lite Strap Safety System 2.0':_size,
        'Crossmember':_size,
        'Powermax Speed Rope':_size,
        'Rogue Kettlebell':_size,
        'Strongman Sandbag':_size,
        'Medicine Ball':_size,
        'Echo Slam Ball':_size

    }
    for opt in opts:
        samp_name = ''.join(opt.xpath('./div[@class="simple-name"]//span//text()')).strip()
        samp_product = samp_products.get(samp_name)
        if not samp_product:
            Tool.print(f'未获取到对应子产品信息:{samp_name},{url}',color='yellow')
            sku = None
        else:
            sku = samp_product['sku']

        samp_price = opt.xpath('.//div[@class="price"]//text()')
        samp_type = None
        for k,v in sam_type_dic.items():
            if k in samp_name:
                samp_type = v
                break


        if not samp_type:
            set_url_ls = ['https://www.roguefitness.com/mass-storage-accessories','https://www.roguefitness.com/rogue-28mm-boneyard-bars','https://www.roguefitness.com/rogue-monster-crossmembers']
            size_url_ls = ['https://www.roguefitness.com/rogue']
            if url in set_url_ls :
                samp_type = _set
            elif any(url for i in size_url_ls if i in url):
                samp_type = _size



            if not samp_type:
                Tool.print(f'未知命名:{samp_name},url:{url}')

        sam_dic.setdefault(sam_type, []).append({
            'name': samp_name, 'price': samp_price,
            'sku': sku, 'Parent': fl_sku,
        })

    Tool.File.save_json(data, 'cs/t1.json')

    ls = []
    for att in sam_dic:
        for v in sam_dic[att]:
            ls.append(Tool.Product.VariantCombo(
                attrs={att: v['name']}, price=v['price'], sku=v['sku'],
            ))

    return Tool.Product.build_products(
        name=fl_name, desc=desc, price=fl_price, url=url,
        common_images=fl_imgs, sku=fl_sku, category=category, combos=ls,
    )

class Crawler:
    def __init__(self, max_threads=10):
        self.input_file = input_file
        self.fail_file = fail_file
        self.max_threads = max_threads

        self.task_queue = Queue()
        self.result_queue = Queue()
        self.failures = {}
        self.total_tasks = 0
        self.completed_tasks = 0
        self.lock = threading.Lock()

    def load_tasks(self):
        data = Tool.File.load_json(self.input_file)
        self.total_tasks = sum(len(urls) for urls in data.values())

        seq_id = 0
        for category, urls in data.items():
            for url in urls:
                self.task_queue.put((seq_id, category, url))
                seq_id += 1
                if isinstance(ts_num, int) and seq_id >= ts_num:
                    Tool.print('启动测试条数')
                    return

    def worker(self, buffer):
        while True:
            try:
                seq_id, category, url = self.task_queue.get_nowait()
            except Exception:
                break
            if str(seq_id) in buffer and buffer[str(seq_id)]:
                continue
            if _should_skip_url(url):
                Tool.print(f'跳过url:{url}')
                self.total_tasks -= 1
                continue

            rows_to_write = []
            error_type = None

            try:
                res = Tool.get(url)
                if not res:
                    error_type = "请求失败"
                    self.failures.setdefault(category, []).append(url)
                else:
                    res_text = res.text
                    try:
                        data = get_detail_page(url, category, res_text)
                        if data is None:
                            continue
                        rows_to_write = data
                    except Exception as e:
                        error_type = "关键字段为空"
                        print(e)
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

    def my_writer_worker(self, catch_path):
        if os.path.exists(catch_path):
            with open(catch_path, "r", newline="", encoding="utf-8") as f:
                buffer = json.load(f)
        else:
            buffer = {}

        num = 0
        while True:
            item = self.result_queue.get()
            if item is None:
                break

            seq_id, rows = item
            buffer[str(seq_id)] = rows
            num += 1
            if num == 20:
                num = 0
                Tool.File.save_json(buffer, catch_path)

            self.result_queue.task_done()

        Tool.File.save_json(buffer, catch_path)

    def run(self):
        self.load_tasks()
        if not os.path.exists(catch_path):
            Tool.File.save_json({}, catch_path)

        buffer = Tool.File.load_json(catch_path)
        self.completed_tasks = len(buffer)
        writer_thread = threading.Thread(target=self.my_writer_worker, args=(catch_path,))
        writer_thread.start()

        threads = []
        for _ in range(self.max_threads):
            t = threading.Thread(target=self.worker, args=(buffer,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.result_queue.put(None)
        writer_thread.join()

        buffer = Tool.File.load_json(catch_path)
        buffer = Tool.sort_data(buffer)

        with open(output_ts_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames + ['url'])
            writer.writeheader()
            for rows in buffer.values():
                writer.writerows(rows)

        bf = Tool.json_del_url(buffer)
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rows in bf.values():
                writer.writerows(rows)

        Tool.File.save_json(self.failures, fail_file)


def main():
    crawler = Crawler(max_threads=max_threads)
    crawler.run()


if __name__ == '__main__':
    main()