from copy import deepcopy

from curl_cffi import requests

import os
import time
import pandas as pd
from lxml import etree

from tqdm import tqdm

from config import Tool, zs, zdy_zd_name

detail_file__path = Tool.File.path_add_site('data/detail_url.json')
quchong_file__path = Tool.File.path_add_site('data/quchong_detail_url.json')

save_path = Tool.File.path_add_site('data/result.csv')

hc_path = Tool.File.path_add_site('hc/4.json')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Accept": "application/json"
}

ck = {
    "localization": "US",
    "cart_currency": "USD",
    "_shopify_y": "dabb39cc-bc89-497c-b340-31b2ede021e3",
    "_shopify_analytics": ":AZp2O1QkAAEAHztC69G-yFNChK1vfflUWudV0AhpFiNR6FOoG0JYh1QIeFwE0AplJXKB:",
    "__kla_id": "eyJjaWQiOiJZelJsTnpnNFltSXRaV1ZqWlMwMFkyUTNMV0ppTW1FdFkyUTJNalUxTVdFNE5XWTMifQ==",
    "_dcid": "dcid.1.1762920201737.993685852",
    "_fbp": "fb.1.1762920201752.1616510929",
    "_gtmeec": "e30%3D",
    "_ga": "GA1.1.360526338.1762920202",
    "FPID": "FPID2.2.gkxOzZt5mIdu%2BjM%2FENk%2BINUWEC8WFAK8VJr7qv9DiMI%3D.1762920202",
    "FPAU": "1.2.1363690192.1762920202",
    "_clck": "8r5450%5E2%5Eg13%5E0%5E2142",
    "FPLC": "LgBR2ZulVErPIfYUSJlzshz28PHJYpcZjaf0ttgQ%2BOKvoX%2FTytpvBT1gw9f8w3Skoaoji%2FPT80R%2BxMChx7HVjW9Jmb0vQwpLwbP7lGJTdH2cpIAbSo3WEf43r4%2BDBA%3D%3D",
    "_shg_session_id": "ee3abf4f-7d71-4f24-b659-5c90de46503d",
    "_shg_user_id": "b36c7c32-f288-42a9-b521-223b4178e2b3",
    "wishlist_id": "165828310s5ibxs5m1i",
    "bookmarkeditems": "{\"items\":[]}",
    "wishlist_customer_id": "0",
    "lantern": "34e4017a-dcd0-44ea-86cc-510f559707fd",
    "_ks_scriptVersionChecked": "true",
    "_ks_userCountryUnit": "0",
    "_ks_countryCodeFromIP": "US",
    "_shopify_essential": ":AZp2O1QXAAEAvyFsaVJ70tJgji5ZeWCZ_YjgxwRXjGxAB3b5N-WHhSnud69tQW0MrpYjCka6b3GqbBhR9Uz4BhF9KODipC_2NFZRmCTQFTmhAMAjGv-jGy4tjy0FmTHMickaBcTQYB9gyNeGMX1T3ZL2JQ1P2sZLYPZwXL-juXGHSYiFqr2Gmc3jlKNMgPuEzv0pxSUVdolOYxCzcSwmJ_JEgKtrg_dwrLM_tp1SdVStXGVGDxfT27-4a1Fn6pKOttW0ZLW4JluB7XDeVv2VuUk-0l_ZIXlIrOu1450YtgeUvAjU3fGxv8SJbsptfgcU-GQ7NmT1Nravs3DmiiAUo2_zvYu9sk8dE3QuA-QodGbtyvFwsh4qzVoX5oLuEgUKhsFrxGP3Le-BVpm8PXsJjtIp7D18HUY:",
    "_clsk": "z0wknv%5E1763344068385%5E8%5E1%5Es.clarity.ms%2Fcollect",
    "_shopify_s": "73b24c0d-a8d4-4416-9886-da6ff48b97ce",
    "_uetsid": "94037020c35611f0b6b471d9a3ac75ef",
    "_uetvid": "8406dea0bf7c11f089889339b77b1953",
    "FPGSID": "1.1763343715.1763344093.G-QSD4N22KEF.mFsL74_ybyYhfff-E83nSQ",
    "_ga_QSD4N22KEF": "GS2.1.s1763343714$o2$g1$t1763344100$j51$l0$h694839178",
    "kiwi-sizing-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI4YTliMTk0ZC1iZmY3LTQ3OTktYjMwYS01Zjc1ZWZjMGVjMjIiLCJpYXQiOjE3NjMzNDQxNDYsImV4cCI6MTc2MzM0Nzc0Nn0.6kThd-lf6VF4L_1otBoH8nlTuH0z9Nw5nF0akbIs4UU",
    "keep_alive": "eyJ2IjoyLCJ0cyI6MTc2MzM0NDE5NDYzOSwiZW52Ijp7IndkIjowLCJ1YSI6MSwiY3YiOjEsImJyIjoxfSwiYmh2Ijp7Im1hIjo2NCwiY2EiOjAsImthIjowLCJzYSI6Mywia2JhIjowLCJ0YSI6MCwidCI6MTEyLCJubSI6MSwibXMiOjAuNjMsIm1qIjowLjMyLCJtc3AiOjAuMzUsInZjIjowLCJjcCI6MCwicmMiOjAsImtqIjowLCJraSI6MCwic3MiOjAuMDEsInNqIjowLjAxLCJzc20iOjEsInNwIjoxLCJ0cyI6MCwidGoiOjAsInRwIjowLCJ0c20iOjB9LCJzZXMiOnsicCI6NSwicyI6MTc2MzM0MzcwNDY0MSwiZCI6NDgzfX0%3D"
}

if_wp = False
brand = Tool.site

# 图片分隔符
images_split = ','


@zs('重写=>请求详细页面，以求获取自定义字段')
def get_zd(url):
    # 返回字典形式
    # res = Tool.get(url)
    # html = etree.HTML(res.text)
    #
    # d = html.xpath('pv-description js-product-description is-active')

    return None


@zs('未查找到用法，考虑删除')
def get_collection_products(collection_url, page=1, limit=250):
    """获取Shopify集合中的产品"""
    # 确保URL以/结尾
    if not collection_url.endswith('/'):
        collection_url += '/'
    # 构建API URL
    products_url = f"{collection_url}products.json?page={page}&limit={limit}"
    try_times = 5
    # (此处的 header/cookie 保留了你原有的配置)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    }

    for i in range(try_times):
        print(f"请求 URL: {products_url} 尝试 {i + 1}/{try_times}")
        try:
            response = requests.get(products_url, headers=headers, impersonate="firefox")
            response.raise_for_status()  # 如果请求失败则抛出异常
            return response.json()['products']
        except requests.exceptions.RequestException as e:
            print(f"获取产品时出错: {e}")
            print(f"请求重试")
    return []


@zs('将Shopify产品格式转换为WooCommerce格式')
def convert_to_woocommerce_format(shopify_product, custom_categories=None):
    """将Shopify产品格式转换为WooCommerce格式"""
    if if_wp:
        woo_product = {
            'ID': '', 'Type': '', 'SKU': '', 'Name': '', 'Published': '1', 'Is featured?': '0',
            'Visibility in catalog': 'visible', 'Short description': '', 'Description': '',
            'Date sale price starts': '', 'Date sale price ends': '', 'Tax status': 'taxable',
            'Tax class': '', 'In stock?': '1', 'Stock': '1000', 'Backorders allowed?': '1',
            'Sold individually?': '0', 'Weight (lbs)': '', 'Length (in)': '', 'Width (in)': '',
            'Height (in)': '', 'Allow customer reviews?': '1', 'Purchase note': '',
            'Sale price': '', 'Regular price': '', 'Categories': '', 'Tags': '',
            'Shipping class': '', 'Images': '', 'Download limit': '', 'Download expiry days': '',
            'Parent': '', 'Grouped products': '', 'Upsells': '', 'Cross-sells': '',
            'External URL': '', 'Button text': '', 'Position': '0', 'Meta: _wpcom_is_markdown': '',
            'Download 1 name': '', 'Download 1 URL': '', 'Download 2 name': '',
            'Download 2 URL': '', 'is_upload': 0, 'brand': f'{brand}'
        }
    else:
        woo_product = {
            'ID': '', 'Type': '', 'SKU': '', 'Name': '', 'Description': '', 'Stock': '1000',
            'Sale price': '', 'Regular price': '', 'Categories': '', 'Tags': '',
            'Images': '', 'Parent': '', 'is_upload': 0, 'brand': f'{brand}'
        }

    has_options = shopify_product.get('options') and any(
        len(option.get('values', [])) >= 1 for option in shopify_product.get('options', []))

    woo_product['Type'] = 'variable' if has_options else 'simple'
    woo_product['SKU'] = shopify_product.get('handle', '')
    woo_product['Description'] = shopify_product.get('body_html', '')
    woo_product['Name'] = shopify_product.get('title', '')

    # 填写是否有库存
    if woo_product['Type'] == 'simple':
        stock = shopify_product.get('variants')[0].get('available')
        woo_product['In stock?'] = 1 if stock else 0

    # 填写分类
    if custom_categories:
        if isinstance(custom_categories, list):
            categories = ','.join([cat.strip() for cat in custom_categories if cat.strip()])
        else:
            categories = custom_categories
    else:
        categories = shopify_product.get('product_type', '')
    woo_product['Categories'] = categories

    # 填写价格
    if shopify_product.get('variants'):
        first_variant = shopify_product['variants'][0]
        woo_product['Regular price'] = first_variant.get('price', '')
        woo_product['Sale price'] = first_variant.get('price', '')
        if first_variant.get('compare_at_price') and float(first_variant.get('compare_at_price', 0)) >= float(
                first_variant.get('price', 0)):
            regular_price = first_variant.get('compare_at_price', '')
            woo_product['Regular price'] = regular_price
            woo_product['Sale price'] = regular_price

    # 填写图片url
    image_urls = [image.get('src', '') for image in shopify_product.get('images', [])]
    woo_product['Images'] = images_split.join(image_urls)

    # 填写属性
    if shopify_product.get('options'):
        for i, option in enumerate(shopify_product.get('options', [])):
            attr_num = i + 1
            woo_product[f'Attribute {attr_num} name'] = option.get('name', '')
            woo_product[f'Attribute {attr_num} value(s)'] = ','.join(option.get('values', []))
            woo_product[f'Attribute {attr_num} visible'] = 0
            woo_product[f'Attribute {attr_num} global'] = 1
    # 添加自定义字段到父类
    zdy_data = shopify_product.get(zdy_zd_name, {})
    if zdy_data:
        for key, value in zdy_data.items():
            k = f'{key}(product.c_f.{key.lower().replace(" ", "_")})'
            woo_product[k] = value
    return woo_product


@zs('为Shopify产品创建变体产品')
def create_variation_products(shopify_product, parent_product):
    """为Shopify产品创建变体产品"""
    variations = []
    has_options = shopify_product.get('options') and any(
        len(option.get('values', [])) >= 1 for option in shopify_product.get('options', []))

    if not has_options:
        return variations

    parent_product['Type'] = 'variable'
    parent_sku = parent_product['SKU']

    # 添加变体图片
    variant_images = {}
    for image in shopify_product.get('images', []):
        image_url = image.get('src', '')
        for variant_id in image.get('variant_ids', []):
            if str(variant_id) not in variant_images:
                variant_images[str(variant_id)] = []
            variant_images[str(variant_id)].append(image_url)

    for variant in shopify_product.get('variants', []):
        variation = parent_product.copy()
        # 变体不需要自定义字段值，置空
        zdy_data = shopify_product.get(zdy_zd_name, {})
        if zdy_data:
            for key in zdy_data:
                variation[key] = ''
        variant_id = str(variant.get('id', ''))
        variation['Type'] = 'variation'
        variation['SKU'] = variant_id
        variation['Regular price'] = variant.get('price', '')
        variation['Sale price'] = variant.get('price', '')
        variation['Parent'] = parent_sku

        if variant.get('compare_at_price') and float(variant.get('compare_at_price', 0)) >= float(
                variant.get('price', 0)):
            regular_price = variant.get('compare_at_price', '')
            variation['Regular price'] = regular_price
            variation['Sale price'] = regular_price

        variation['In stock?'] = '1' if variant.get('available', True) else '0'
        variation['Stock'] = str(variant.get('inventory_quantity', 1000))

        for i, option in enumerate(shopify_product.get('options', [])):
            option_key = f"option{i + 1}"
            if variant.get(option_key):
                variation[f'Attribute {i + 1} value(s)'] = variant.get(option_key, '')

        if variant_id in variant_images and variant_images[variant_id]:
            variation['Images'] = ','.join(variant_images[variant_id])
        else:
            variation['Images'] = ''

        variation['Description'] = ''
        variations.append(variation)

    return variations


@zs('通过 Shopify product handle 获取产品数据，带有精确的 429 处理机制')
def get_product_by_handle(session, handle, retries=5):
    """
    通过 Shopify product handle 获取产品数据，带有精确的 429 处理机制
    """
    # 建议加上 www，避免服务器进行额外的 301 重定向消耗资源
    url = f"https://www.{brand}.com/products/{handle}.json"

    for attempt in range(retries):
        try:
            # 统一使用传入的 session
            r = session.get(url, headers=headers, timeout=15, cookies=ck)
            # 🎯 核心修复：拦截 429 Too Many Requests
            if r.status_code == 429:
                wait_time = 5 + (attempt * 3)  # 每次被限流，休眠时间递增 (5s, 8s, 11s...)
                tqdm.write(f"\n[⚠️ 429 频率限制] 请求过快，强制休眠 {wait_time} 秒... ({handle})")
                time.sleep(wait_time)
                continue  # 重试当前 handle

            # 拦截 404 页面不存在
            if r.status_code == 404:
                tqdm.write(f"\n[INFO] {handle} 页面不存在 (404)")
                return None

            r.raise_for_status()
            data = r.json()

            zdy_data = get_zd(url.replace('.json', ''))

            # 🎯 核心修复：成功请求后必须强制延迟，维持频率在 Shopify 允许的安全范围内
            time.sleep(1.5)
            shopify_product = data.get("product")
            shopify_product[zdy_zd_name] = zdy_data
            shopify_product['__url'] = url

            return shopify_product

        except requests.exceptions.RequestException as e:
            tqdm.write(f"\n[WARN] {handle} 网络异常: {e}, 第 {attempt + 1}/{retries} 次重试")
            time.sleep(3 + attempt)
        except Exception as e:
            tqdm.write(f"\n[ERROR] {handle} 未知异常: {e}")
            time.sleep(3)

    return None


def save_woocommerce_products_csv(products):
    """将WooCommerce格式的产品数据保存为CSV文件"""
    output_file = save_path
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df = pd.DataFrame(products)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"成功保存 {len(products)} 个产品到 {output_file}")
    print(f"其中包含 {sum(1 for p in products if p['Type'] == 'variable')} 个主产品")
    print(f"其中包含 {sum(1 for p in products if p['Type'] == 'variation')} 个变体产品")


def main():
    # ===============================
    # 1️ 读取产品 URL 列表
    # ===============================

    product_urls = Tool.File.load_json(quchong_file__path)
    if not product_urls:
        return
    print(f"产品 URL 数量: {len(product_urls)}")

    # ===============================
    # 2️读取 URL 顺序文件
    # ===============================

    url_order_config = Tool.File.load_json(detail_file__path)
    if not url_order_config:
        return
    print(f"顺序分类数: {len(url_order_config)}")

    # ===============================
    # 3️按 URL 列表抓取 Shopify 产品
    # ===============================
    handle_to_product = Tool.File.load_json(hc_path)
    print("\n开始按 URL 直接抓取产品...")

    session = requests.Session(impersonate="firefox")

    for url in tqdm(product_urls):
        handle = Tool.URL.get_handle(url)
        if not handle or handle in handle_to_product:
            continue

        # 🚀 核心修复：移除了多余的 5 次 try-except 循环，交给 get_product_by_handle 内部处理
        product = get_product_by_handle(session, handle)
        if product:
            handle_to_product[handle] = product

    print(f"\n共抓取到 Shopify 产品: {len(handle_to_product)}")
    Tool.File.save_json(handle_to_product, hc_path)

    # ===============================
    # 4️ 按顺序写 CSV
    # ===============================

    ordered_products = []
    missing_handles = []
    _ts_products = []

    print("\n开始按 URL 顺序生成 CSV 数据...")

    for category_path, urls in url_order_config.items():
        for url in urls:
            handle = Tool.URL.get_handle(url)
            shopify_product = handle_to_product.get(handle)
            if not shopify_product:
                missing_handles.append(handle)
                continue

            woo_product = convert_to_woocommerce_format(
                shopify_product,
                custom_categories=category_path
            )

            variations = create_variation_products(shopify_product, woo_product)

            ordered_products.append(woo_product)

            if variations:
                ordered_products.extend(variations)

            ts_woo_product = deepcopy(woo_product)
            ts_woo_product['__url'] = shopify_product['__url']
            _ts_products.append(ts_woo_product)
            if variations:
                _ts_products.extend(variations)


    # ===============================
    # 5️ 保存 CSV
    # ===============================
    if ordered_products:
        save_woocommerce_products_csv(ordered_products)
    else:
        print("未生成任何产品")


if __name__ == "__main__":
    main()