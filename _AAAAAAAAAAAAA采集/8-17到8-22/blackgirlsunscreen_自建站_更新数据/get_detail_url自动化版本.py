import json
from urllib.parse import urljoin
from DrissionPage import Chromium


def load_url_dict_from_file(file_path):
    """从 JSON 文件加载 URL 字典"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件失败: {file_path}，错误: {e}")
        return {}


def get_detail_url(browser, url):
    """
    针对只有一页且不需要去重的分类页获取所有产品详情页 URL
    """
    # 💡 每一个分类 URL 在单窗体浏览器上开一个新标签页
    tab = browser.new_tab()
    product_urls = []

    try:
        tab.get(url)
        print("正在安全加载页面...")

        # 1. 精准等待：等待商品图片链接加载出来
        tab.wait.eles_loaded('css:a.wd-product-img-link', timeout=5)

        # 2. 直接抓取当前页的所有商品链接
        lis = tab.eles('css:a.wd-product-img-link')

        for li in lis:
            try:
                if not li:
                    continue
                href = li.attr('href')
                if href:
                    full_url = urljoin(tab.url, href)
                    # 💡 顺应需求：不再进行去重判定，抓到什么存什么
                    product_urls.append(full_url)
                    print(f"成功获取: {full_url}")
            except Exception:
                continue

        print(f"本页抓取完成，共提取到 {len(product_urls)} 条数据。")

    except Exception as global_e:
        print(f"标签页内部发生致命崩溃: {global_e}")

    finally:
        if tab:
            print("正在关闭当前分类标签页...")
            tab.close()

    return product_urls


if __name__ == "__main__":
    # 加载你的 url.json
    url_dict = load_url_dict_from_file('data/url.json')
    result = {}

    # 💡 核心修复点 1：在大循环外部统一开启浏览器环境
    print("正在初始化全局浏览器...")
    browser = Chromium()

    try:
        for name, url_data in url_dict.items():
            print(f"\n====== 正在处理分类：{name} ======")
            result[name] = []

            # 判断 url_data 是单个字符串还是列表
            if isinstance(url_data, str):
                url_list = [url_data]  # 如果是字符串，包装成列表
            else:
                url_list = url_data  # 如果本来就是列表，直接使用

            # 遍历每个分类下的初始 URL
            for url in url_list:
                try:
                    print(f"正在分析 URL: {url}")
                    # 💡 核心修复点 2：传入外部已经初始化好的 browser 对象以及 url
                    detail_urls = get_detail_url(browser, url)
                    if detail_urls:
                        # 保持顺序扩展结果
                        result[name].extend(detail_urls)
                        print(f"  分类【{name}】成功获取到 {len(detail_urls)} 条详情页链接")
                    else:
                        print(f"  URL: {url} 未获取到任何数据")
                except Exception as e:
                    print(f"  URL: {url} 处理中途中断: {e}")

        # 保存结果
        with open('data/detail_url.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        total_count = sum(len(v) for v in result.values())
        print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 detail_url.json")

    finally:
        # 💡 核心修复点 3：当所有任务执行完毕时，清理并关闭浏览器资源
        if browser:
            print("\n正在关闭并清理全局浏览器资源...")
            browser.quit()