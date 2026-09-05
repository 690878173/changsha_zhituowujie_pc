"""
File        : 搜索接口.py
Author      : 张占帅
Created     : 2026/3/24 11:10
Description :
"""
import json
import os
import re
import time
import random
from DrissionPage import ChromiumPage, ChromiumOptions
from lxml import etree





def scrape_amazon_to_custom_json(search_keyword,output_path):
    dir_path = os.path.dirname(output_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    # 1. 配置浏览器
    co = ChromiumOptions()
    co.no_imgs(True)  # 禁止加载图片，提高速度
    page_obj = ChromiumPage(co)

    # 用于存储所有抓取到的 ASIN
    all_asins = []
    total_pages = 6

    try:
        for page_num in range(1, total_pages + 1):
            print(f"正在爬取第 {page_num} 页...")

            # 2. 构造翻页 URL
            url = f"https://www.amazon.com/s?k={search_keyword}&i=grocery&page={page_num}&ref=sr_pg_{page_num}"
            page_obj.get(url)

            # 等待页面加载，并模拟随机滚动
            time.sleep(random.uniform(3, 5))
            page_obj.scroll.to_half()

            # 3. 获取源码并使用 XPath 解析
            html_source = page_obj.html
            tree = etree.HTML(html_source)

            # 提取当前页的 ASIN (过滤掉广告和空值)
            page_asins = tree.xpath('//div[@role="listitem" and @data-asin]/@data-asin')

            # 去重并加入总列表
            for asin in page_asins:
                if asin and asin not in all_asins:
                    all_asins.append(asin)

            print(f"第 {page_num} 页采集完成，目前累计 ASIN 数量: {len(all_asins)}")

        # 4. 按照你要求的格式构造最终数据
        # 键名为 shop，值为 ASIN 字符串列表
        final_data = {
            "Home": all_asins
        }

        # 5. 写入 JSON 文件
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)

        print(f"\n任务成功！结果已保存至 amazon_asins.json，共计 {len(all_asins)} 个 ASIN。")

    except Exception as e:
        print(f"采集出错: {e}")
    finally:
        page_obj.quit()




STEP1 = scrape_amazon_to_custom_json




class YMXStep1:
    def __init__(self,search_keyword,output_path,all_num=6):
        self.search_keyword = search_keyword
        self.output_path = output_path
        self.all_num = all_num

    def get_url(self,page_num,search_keyword):
        url = f"https://www.amazon.com/s?k={self.search_keyword}&i=grocery&page={page_num}&ref=sr_pg_{page_num}"
        return url

    def run(self):
        co = ChromiumOptions()
        co.no_imgs(True)  # 禁止加载图片，提高速度
        page_obj = ChromiumPage(co)

        all_asins = {}
        total_pages = self.all_num

        best_sale_num = 6

        try:
            for page_num in range(1, total_pages + 1):
                print(f"正在爬取第 {page_num} 页...")

                # 2. 构造翻页 URL
                # https://www.amazon.com/s?k=huckberry&i=grocery&page=1&ref=sr_pg_1
                url = self.get_url(page_num,self.search_keyword)
                page_obj.get(url)

                # 等待页面加载，并模拟随机滚动
                time.sleep(random.uniform(3, 5))
                page_obj.scroll.to_half()

                # 3. 获取源码并使用 XPath 解析
                html_source = page_obj.html
                tree = etree.HTML(html_source)

                # 提取当前页的 ASIN (过滤掉广告和空值)
                page_asins = tree.xpath('//div[@role="listitem" and @data-asin]/@data-asin')

                xpath_expr = './/div[@class="a-row a-size-small]/span[2]/div/a/@aria-label"'

                xpath_expr = './/div[@class="a-row a-size-small"]//*/text()'
                for page_div in tree.xpath('//div[@role="listitem" and @data-asin]'):
                    asin = page_div.get('data-asin')
                    if asin and asin not in all_asins:

                        best_saller = page_div.xpath(xpath_expr)
                        num = 0
                        try:
                            for i in best_saller:
                                if ('(' in i) and (')' in i):
                                    text = i
                                    # text = best_saller[0].text_content()
                                    m = re.search(r'([\d,]+)', text)
                                    num = int(m.group(1).replace(',', '')) if m else 0
                        except Exception as e:
                            print(e)
                            pass

                        all_asins[asin] = num


                # # 去重并加入总列表
                # for asin in page_asins:
                #     if asin and asin not in all_asins:
                #         all_asins.append(asin)

                print(f"第 {page_num} 页采集完成，目前累计 ASIN 数量: {len(all_asins)}")

            sorted_list = sorted(all_asins.items(), key=lambda item: item[1], reverse=True)
            # 4. 按照你要求的格式构造最终数据
            # 键名为 shop，值为 ASIN 字符串列表

            final_data = {}

            for asin, num in sorted_list:
                if best_sale_num >0 and num>0:
                    final_data.setdefault('Best Sale??????', []).append(asin)
                    best_sale_num -= 1
                    print(f'{asin} sale: {num}')

                final_data.setdefault('Home', []).append(asin)
            # final_data = {
            #     "Home": all_asins
            # }
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)

            print(f"\n任务成功！结果已保存至 {self.output_path}，共计 {len(all_asins)} 个 ASIN。")

        except Exception as e:
            print(f"采集出错: {e}")
        finally:
            page_obj.quit()
