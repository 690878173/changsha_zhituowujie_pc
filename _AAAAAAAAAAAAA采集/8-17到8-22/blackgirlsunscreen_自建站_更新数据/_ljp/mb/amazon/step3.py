import json
import csv
import os
import threading
from pathlib import Path
from queue import Queue
import html
from lxml import etree

from curl_cffi import requests

from _ljp import File, HTML

cookies = {
    'session-id': '132-3456321-9266043',
    'session-id-time': '2082787201l',
    'sst-main': 'Sst1|PQJwelldPp1VATbkCI5NQBd2B_uo72_2LfD5kup-pQJvDWQ-irSenyp6-V0v05GR555ZFLSBqEFDFiwC9o1tPJ5zN6-uXlT0QpJf7yfDwq9xuQQYBY9bDpDpl1w666ggj1HnAClNQL_kaIYhitjLE5bm9OtUrP5SZuU7UfXcv_5ioVS8nzcdyoJehLdJN6DlJbm2x_fPsktp0nwvnuss7__QTveorqHKwV3Xyk7AyhWnI1bi3c6wh1XE1S6N2gVXx0wD',
    'i18n-prefs': 'USD',
    'lc-main': 'en_US',
    'ubid-main': '134-3297936-0384866',
    'rx': 'AQAGyoKZVSHB0RrnKdy+eCEIwag=@AW9bhmo=',
    'skin': 'noskin',
    'ak_bmsc': 'CC35891CED4359269881B143543BC750~000000000000000000000000000000~YAAQ1/EPFxWLhfmfAQAAq5iGNwAH5D3RpMGx8sH0x/XaguHTH5IOHYb6JLyooNZlQxPTNvXNv/DXVZm5zIVJWARxrADvIjrkymDcOpQlwgzA/CsrSjATP1FKir5YrlwdebXqTRFX255FDkDSvUGnFK9DX1Bj/59+Amvwbh+P1EtNZHl0ZEQSrJnErZ5aul4RI/x/+jVWBwge/oI02iw9c8Vqy2CKzIiQJREaED+8vlga06VXknME7m9ghGCbbb0LUl2pNAAmyq8EnyyFM3goJARRFCaeql5O3XDLwdGgUk16tEFLOxwGpgbqIf3YfsTTWnTxttyP4AUFk1CsmrVhcX+0tPmsswLHYOmwOj+MlbRXtIBb84FBKS1QN0i8lwsBLlwvwT/LMRIN5X/D',
    'bm_sv': '6BAABBA52E6698B130609963AC013EAB~YAAQ1/EPF0eNhfmfAQAAL/eGNwCLriAamjaX1cGm16HcnHqfCy3Xl7Wa8tX9eXLqrFnNZE3SMKPovfFekeeqQ3qhCTbDWjZnMm5E8rueQF43Ooqvtw3cMIMJMKlRkfw7qrgNk0aCCnkhimdzo9rX1typLc81Y3Vt7mIILctq7G4yM4s0GzhpVpDhqHT3MQI1k0Rqen8ZDqoVH7x/kc04dLrLcWVEx7RVtHunhBflnZpqtQVnBqcWBYgnC8HzWw2Tdw==~1',
    'session-token': 'e5UpdBGWoJ0P7Ix7/3Kf+CXHG6/0lnQHCYmch0in52S3zngT8YIbq0z+U7SsStCDn84L+DiXN0xQDHfLEh4lZ1/z1V86tce0uQH1HRYSpKyJX4PJpXCgTrAJZLUy1rkDRPBINX5MEh5x3ox3CIw2Ia0+4HJfiDiepevFDdBAPNqdCmemd+owB9tCyR6QeDwlTCHnkhwwbtyjHMNohFfJ2nSbECKtT0L8',
    'rxc': 'AGbPdBPaKw2643sXYX4',
    'csm-hit': 'tb:s-K996NT97AK6QV405R3EF|1787640203486&t:1787640204951&adb:adblk_yes',
}

headers = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'device-memory': '16',
    'downlink': '10',
    'dpr': '1.5',
    'ect': '4g',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.amazon.com',
    'rtt': '200',
    'sec-ch-device-memory': '16',
    'sec-ch-dpr': '1.5',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-full-version-list': '"Not=A?Brand";v="99.0.0.0", "Microsoft Edge";v="151.0.4129.107", "Chromium";v="151.0.7922.174"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"15.0.0"',
    'sec-ch-viewport-height': '274',
    'sec-ch-viewport-width': '1699',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    'viewport-width': '1699',
    'x-requested-with': 'XMLHttpRequest',
    # 'cookie': 'session-id=132-3456321-9266043; session-id-time=2082787201l; sst-main=Sst1|PQJwelldPp1VATbkCI5NQBd2B_uo72_2LfD5kup-pQJvDWQ-irSenyp6-V0v05GR555ZFLSBqEFDFiwC9o1tPJ5zN6-uXlT0QpJf7yfDwq9xuQQYBY9bDpDpl1w666ggj1HnAClNQL_kaIYhitjLE5bm9OtUrP5SZuU7UfXcv_5ioVS8nzcdyoJehLdJN6DlJbm2x_fPsktp0nwvnuss7__QTveorqHKwV3Xyk7AyhWnI1bi3c6wh1XE1S6N2gVXx0wD; i18n-prefs=USD; lc-main=en_US; ubid-main=134-3297936-0384866; rx=AQAGyoKZVSHB0RrnKdy+eCEIwag=@AW9bhmo=; skin=noskin; ak_bmsc=CC35891CED4359269881B143543BC750~000000000000000000000000000000~YAAQ1/EPFxWLhfmfAQAAq5iGNwAH5D3RpMGx8sH0x/XaguHTH5IOHYb6JLyooNZlQxPTNvXNv/DXVZm5zIVJWARxrADvIjrkymDcOpQlwgzA/CsrSjATP1FKir5YrlwdebXqTRFX255FDkDSvUGnFK9DX1Bj/59+Amvwbh+P1EtNZHl0ZEQSrJnErZ5aul4RI/x/+jVWBwge/oI02iw9c8Vqy2CKzIiQJREaED+8vlga06VXknME7m9ghGCbbb0LUl2pNAAmyq8EnyyFM3goJARRFCaeql5O3XDLwdGgUk16tEFLOxwGpgbqIf3YfsTTWnTxttyP4AUFk1CsmrVhcX+0tPmsswLHYOmwOj+MlbRXtIBb84FBKS1QN0i8lwsBLlwvwT/LMRIN5X/D; bm_sv=6BAABBA52E6698B130609963AC013EAB~YAAQ1/EPF0eNhfmfAQAAL/eGNwCLriAamjaX1cGm16HcnHqfCy3Xl7Wa8tX9eXLqrFnNZE3SMKPovfFekeeqQ3qhCTbDWjZnMm5E8rueQF43Ooqvtw3cMIMJMKlRkfw7qrgNk0aCCnkhimdzo9rX1typLc81Y3Vt7mIILctq7G4yM4s0GzhpVpDhqHT3MQI1k0Rqen8ZDqoVH7x/kc04dLrLcWVEx7RVtHunhBflnZpqtQVnBqcWBYgnC8HzWw2Tdw==~1; session-token=e5UpdBGWoJ0P7Ix7/3Kf+CXHG6/0lnQHCYmch0in52S3zngT8YIbq0z+U7SsStCDn84L+DiXN0xQDHfLEh4lZ1/z1V86tce0uQH1HRYSpKyJX4PJpXCgTrAJZLUy1rkDRPBINX5MEh5x3ox3CIw2Ia0+4HJfiDiepevFDdBAPNqdCmemd+owB9tCyR6QeDwlTCHnkhwwbtyjHMNohFfJ2nSbECKtT0L8; rxc=AGbPdBPaKw2643sXYX4; csm-hit=tb:s-K996NT97AK6QV405R3EF|1787640203486&t:1787640204951&adb:adblk_yes',
}

class Crawler:
    def __init__(self, input_file, output_file, fail_file,img_split=','):
        self.input_file = input_file
        self.output_file = output_file
        self.fail_file = fail_file

        self.img_split = img_split

        self.task_queue = Queue()
        self.result_queue = Queue()
        self.failures = {}
        self.total_tasks = 0
        self.completed_tasks = 0
        self.lock = threading.Lock()

        # 初始化 curl_cffi 会话，模拟 Chrome 指纹
        self.session = requests.Session(impersonate="chrome120")
        self.cookies = cookies

        self.headers = headers


    def set_us_location(self):
        """模拟切换到美国邮编 10001 以获取美元价格"""
        print("--- 正在初始化美国配送环境 (Zip: 10001) ---")
        try:
            self.session.get("https://www.amazon.com/?currency=USD&language=en_US", headers=self.headers, timeout=15)
            url = "https://www.amazon.com/portal-migration/hz/glow/address-change"
            data = {
                "locationType": "LOCATION_INPUT",
                "zipCode": "10001",
                "storeContext": "generic",
                "deviceType": "web",
                "pageType": "Gateway",
                "actionSource": "glow"
            }
            ajax_headers = self.headers.copy()
            ajax_headers.update({
                "content-type": "application/json",
                "x-requested-with": "XMLHttpRequest",
                "referer": "https://www.amazon.com/"
            })
            resp = self.session.post(url, data=json.dumps(data), headers=ajax_headers, cookies=self.cookies, timeout=10)
            if resp.status_code == 200 and "10001" in resp.text:
                print("--- 成功：环境已锁定为美国 (USD) ---")
                return True
            else:
                print("--- 失败：环境非美国 10001 ---")
        except Exception as e:
            print(f"--- 切换地址异常: {e} ---")
        return False

    def load_tasks(self):
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.total_tasks = sum(len(urls) for urls in data.values())
            seq_id = 0
            for category, urls in data.items():
                for url in urls:
                    self.task_queue.put((seq_id, category, url))
                    seq_id += 1
        except Exception as e:
            print(f"读取输入文件失败: {e}")

    def fetch_page_source(self, url):
        try:
            target_url = f"https://www.amazon.com/dp/{url}?language=en_US&currency=USD"
            resp = self.session.get(target_url, headers=self.headers, cookies=self.cookies, timeout=15)
            if resp.status_code == 200:
                if "api-services-support@amazon.com" in resp.text:
                    print(f"[Captcha] {url} 触发验证码")
                    return None
                return resp.text
            return None
        except Exception as e:
            print(f"[Network Error] {url}: {e}")
            return None

    def get_amazon_price_api(self, url):
        """通过 Ajax 接口获取价格"""
        try:
            params = {
                'isDimensionSlotsAjax': '1',
                'asinList': url,
                'asin': url,
                'parentAsin': url,
                'landingAsin': url,
                'deviceType': 'web',
            }
            ajax_headers = self.headers.copy()
            ajax_headers.update({
                'referer': f'https://www.amazon.com/dp/{url}',
                'x-requested-with': 'XMLHttpRequest'
            })
            res = self.session.get(
                'https://www.amazon.com/gp/product/ajax/twisterDimensionSlotsDefault',
                params=params,
                headers=ajax_headers,
                timeout=10
            )
            if res.status_code == 200:
                price_data = res.json()
                price = price_data.get('Value', {}).get('content', {}).get('twisterSlotJson', {}).get('price')
                return price
        except:
            pass
        return None

    def process_response(self, html_source, category, url):
        """核心解析逻辑：增加了多级价格抓取"""
        tree = etree.HTML(html_source)

        # --- 价格抓取策略 ---
        price = self.get_amazon_price_api(url)  # 策略 1: API

        if not price:
            # 策略 2: 从指定的隐藏 input 标签获取 (用户提供的逻辑)
            hidden_price = tree.xpath('//input[@id="items[0.base][customerVisiblePrice][amount]"]/@value')
            if hidden_price:
                price = hidden_price[0]



        if not price:
            print(f"[Skip] {url} 所有渠道均未获取到价格")
            return None

        # 解析标题
        name_node = tree.xpath('//span[@id="productTitle"]/text()') or tree.xpath('//h1[@id="pqv-title"]/text()')
        if not name_node:
            return None
        name = name_node[0].strip()

        # 解析变体属性
        item_details = {}
        attr_nodes = tree.xpath(
            '//div[@class="a-section a-spacing-none a-padding-none inline-twister-dim-title-value-truncate-expanded"]')
        for i, item in enumerate(attr_nodes, 1):
            item_details[f"Attribute {i} name"] = item.xpath('string(./span[1])').strip().rstrip(':')
            item_details[f"Attribute {i} value(s)"] = item.xpath('string(./span[2])').strip()

        # 解析图片
        image_list = []
        nodes = tree.xpath('//ul[contains(@class, "maintain-height")]//*[@data-a-dynamic-image]')
        for node in nodes:
            try:
                high_res = node.xpath('./@data-old-hires')
                if high_res and high_res[0]:
                    image_list.append(high_res[0])
                    continue
                img_json_str = node.xpath('./@data-a-dynamic-image')[0]
                img_dict = json.loads(html.unescape(img_json_str))
                if img_dict:
                    image_list.append(list(img_dict.keys())[-1])
            except:
                continue
        image_list = list(dict.fromkeys([u for u in image_list if u]))

        # 获取详情 HTML
        def get_node_html(xpath_str):
            nodes = tree.xpath(xpath_str)
            if nodes:
                raw = etree.tostring(nodes[0], method='html', encoding='utf-8').decode()
                return raw.replace('style="display:none"', '')
            return ''

        info_list = {
            "important_information(product.metafields.c_f.important_information)": get_node_html('//div[@id="important-information"]'),
            "productDescription(product.metafields.c_f.productdescription)": get_node_html('//div[@id="productDescription"]'),
            "Product_details(product.metafields.c_f.product_details)": get_node_html('//div[@id="detailBulletsWrapper_feature_div"]'),
            "About_this_item(product.metafields.c_f.about_this_item)": get_node_html('//div[@id="feature-bullets"]'),
        }

        # 构建最终行
        result = {
            "Type": "variation" if item_details else "simple",
            "SKU": f"{url}-variation" if item_details else url,
            "Description": "",
            "Name": name,
            "Sale price": price,
            "Regular price": price,
            "Categories": category,
            "Images": self.img_split.join(image_list),
            "Parent": url if item_details else "",
            "brand": "clarol",
            "Stock": 1000.0,
            "is_upload": 0
        }
        result.update(item_details)
        result.update(info_list)
        return [result]

    def worker(self):
        while not self.task_queue.empty():
            try:
                seq_id, category, url = self.task_queue.get_nowait()
            except:
                break

            final_data = None
            try:
                html_code = self.fetch_page_source(url)
                if html_code:
                    final_data = self.process_response(html_code, category, url)
                    if final_data:
                        self.result_queue.put((seq_id, final_data))
                    else:
                        self.failures.setdefault(category, []).append(url)
                        self.result_queue.put((seq_id, []))
                else:
                    self.failures.setdefault(category, []).append(url)
                    self.result_queue.put((seq_id, []))
            except Exception as e:
                print(f"[Fatal] {url} 错误: {e}")
                self.failures.setdefault(category, []).append(url)
                self.result_queue.put((seq_id, []))
            finally:
                with self.lock:
                    self.completed_tasks += 1
                    p = final_data[0].get('Sale price') if final_data else 'None'
                    print(f"进度: {self.completed_tasks}/{self.total_tasks} | {url} | 价格: {p}")
                self.task_queue.task_done()

    def writer_worker(self):
        all_rows = []
        next_seq = 0
        buffer = {}
        while True:
            item = self.result_queue.get()
            if item is None: break
            seq_id, rows = item
            buffer[seq_id] = rows
            while next_seq in buffer:
                all_rows.extend(buffer.pop(next_seq))
                next_seq += 1
            self.result_queue.task_done()

        if all_rows:
            fieldnames = []
            for row in all_rows:
                for key in row.keys():
                    if key not in fieldnames: fieldnames.append(key)

            Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(all_rows)
            print(f"--- 任务完成，数据已保存至: {self.output_file} ---")

    def run(self):
        self.load_tasks()
        self.set_us_location()

        t_writer = threading.Thread(target=self.writer_worker, daemon=True)
        t_writer.start()

        # 如果需要提速，可以增加线程数，例如：
        # threads = []
        # for _ in range(3):
        #     t = threading.Thread(target=self.worker)
        #     t.start()
        #     threads.append(t)
        # for t in threads: t.join()

        self.worker()  # 目前是单线程执行，稳定第一

        self.result_queue.put(None)
        t_writer.join()

        if self.failures:
            self.fail_file = Path(self.fail_file)
            self.fail_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.fail_file, "w", encoding="utf-8") as f:
                json.dump(self.failures, f, ensure_ascii=False, indent=4)

from _ljp.mb.base import Get_Product
class YMXStep3(Get_Product):

    def set_us_location(self):
        """模拟切换到美国邮编 10001 以获取美元价格"""
        print("--- 正在初始化美国配送环境 (Zip: 10001) ---")
        try:
            self.Tool.get("https://www.amazon.com/?currency=USD&language=en_US", headers=headers,cookies=cookies, timeout=15)
            url = "https://www.amazon.com/portal-migration/hz/glow/address-change"
            data = {
                "locationType": "LOCATION_INPUT",
                "zipCode": "10001",
                "storeContext": "generic",
                "deviceType": "web",
                "pageType": "Gateway",
                "actionSource": "glow"
            }
            ajax_headers = headers.copy()
            ajax_headers.update({
                "content-type": "application/json",
                "x-requested-with": "XMLHttpRequest",
                "referer": "https://www.amazon.com/"
            })
            resp = self.Tool.post(url, data=json.dumps(data), headers=ajax_headers, cookies={}, timeout=10)
            if resp.status_code == 200 and "10001" in resp.text:
                print("--- 成功：环境已锁定为美国 (USD) ---")
                return True
            else:
                print(f"--- 失败：环境非美国 10001 ---,状态码:{resp.status_code},已保存响应结果")
                self.Tool.HTML.save(resp.text)
        except Exception as e:
            print(f"--- 切换地址异常: {e} ---")
        return False

    def get_amazon_price_api(self, url):
        """通过 Ajax 接口获取价格"""
        try:
            params = {
                'isDimensionSlotsAjax': '1',
                'asinList': url,
                'asin': url,
                'parentAsin': url,
                'landingAsin': url,
                'deviceType': 'web',
            }
            ajax_headers = headers.copy()
            ajax_headers.update({
                'referer': f'https://www.amazon.com/dp/{url}',
                'x-requested-with': 'XMLHttpRequest'
            })
            res = self.Tool.get(
                'https://www.amazon.com/gp/product/ajax/twisterDimensionSlotsDefault',
                params=params,
                headers=ajax_headers,
                timeout=10
            )
            if res.status_code == 200:
                price_data = res.json()
                price = price_data.get('Value', {}).get('content', {}).get('twisterSlotJson', {}).get('price')
                return price
        except:
            pass
        return None

    def process_response(self, html_source, category, url):
        """核心解析逻辑：增加了多级价格抓取"""
        tree = etree.HTML(html_source)

        # --- 价格抓取策略 ---
        price = self.get_amazon_price_api(url)  # 策略 1: API

        if not price:
            # 策略 2: 从指定的隐藏 input 标签获取 (用户提供的逻辑)
            hidden_price = tree.xpath('//input[@id="items[0.base][customerVisiblePrice][amount]"]/@value')
            if hidden_price:
                price = hidden_price[0]



        if not price:
            print(f"[Skip] {url} 所有渠道均未获取到价格")
            return None

        # 解析标题
        name_node = tree.xpath('//span[@id="productTitle"]/text()') or tree.xpath('//h1[@id="pqv-title"]/text()')
        if not name_node:
            return None
        name = name_node[0].strip()

        # 解析变体属性
        item_details = {}
        attr_nodes = tree.xpath(
            '//div[@class="a-section a-spacing-none a-padding-none inline-twister-dim-title-value-truncate-expanded"]')

        child_sku_qz = ''
        for i, item in enumerate(attr_nodes, 1):
            v_name = item.xpath('string(./span[1])').strip().rstrip(':')
            v_value = item.xpath('string(./span[2])').strip()
            item_details[f"Attribute {i} name"] = v_name
            item_details[f"Attribute {i} value(s)"] = v_value

            child_sku_qz += f'_{v_name}_{v_value}'

        # 解析图片
        image_list = []
        nodes = tree.xpath('//ul[contains(@class, "maintain-height")]//*[@data-a-dynamic-image]')
        for node in nodes:
            try:
                high_res = node.xpath('./@data-old-hires')
                if high_res and high_res[0]:
                    image_list.append(high_res[0])
                    continue
                img_json_str = node.xpath('./@data-a-dynamic-image')[0]
                img_dict = json.loads(html.unescape(img_json_str))
                if img_dict:
                    image_list.append(list(img_dict.keys())[-1])
            except:
                continue
        image_list = list(dict.fromkeys([u for u in image_list if u]))

        # 获取详情 HTML
        def get_node_html(xpath_str):
            nodes = tree.xpath(xpath_str)
            if nodes:
                raw = etree.tostring(nodes[0], method='html', encoding='utf-8').decode()
                return raw.replace('style="display:none"', '')
            return ''

        info_list = {
            "important_information(product.metafields.c_f.important_information)": get_node_html('//div[@id="important-information"]'),
            "productDescription(product.metafields.c_f.productdescription)": get_node_html('//div[@id="productDescription"]'),
            "Product_details(product.metafields.c_f.product_details)": get_node_html('//div[@id="detailBulletsWrapper_feature_div"]'),
            "About_this_item(product.metafields.c_f.about_this_item)": get_node_html('//div[@id="feature-bullets"]'),
        }


        Parent = self.ys_dic.get(url,url) if item_details else ""
        if Parent == url:
            sku = f"{url}-{child_sku_qz}"

        elif Parent == "":
            sku = f"{url}"
        else:
            sku = url
        # 构建最终行
        result = {
            "Type": "variation" if item_details else "simple",
            "SKU": sku,
            "Description": "",
            "Name": name,
            "Sale price": price,
            "Regular price": price,
            "Categories": category,
            "Images": self.Tool.config.images_split.join(image_list),
            "Parent": Parent,
            "brand": "clarol",
            "Stock": 1000.0,
            "is_upload": 0
        }
        result.update(item_details)
        result.update(info_list)
        return [result]

    def _init(self):
        super()._init()
        self.set_us_location()

        self.ys_dic = self.tool.File.load_json(self.Tool.File.path_add_site('data/变体id映射表.json'))
        self.set_not_parent()

    def set_not_parent(self,no=False):
        if no:
            self.yc_dic = {}

    def fetch_product(self, url, category) -> list[dict]:
        try:
            target_url = f"https://www.amazon.com/dp/{url}?language=en_US&currency=USD"
            resp = self.Tool.get(target_url, headers=headers, cookies=cookies, timeout=15)
            if resp.status_code == 200:
                if "api-services-support@amazon.com" in resp.text:
                    print(f"[Captcha] {url} 触发验证码")
                    return []
                try:
                    return self.process_response(resp.text,category,url) or []
                except Exception as e:
                    return []
            return []
        except Exception as e:
            print(f"[Network Error] {url}: {e}")
            return []

Step3 = Crawler
if __name__ == "__main__":
    crawler = Crawler(
        input_file=r"data/detail_url.json",
        output_file=r"data/result.csv",
        fail_file=r"data/fail.json"
    )
    crawler.run()