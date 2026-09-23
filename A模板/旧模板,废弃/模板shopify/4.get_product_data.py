from curl_cffi import requests
import time
from tqdm import tqdm
from config import Tool


detail_file__path = Tool.File.path_add_site('data/detail_url.json')
quchong_file__path = Tool.File.path_add_site('data/quchong_detail_url.json')

save_path = Tool.File.path_add_site('res/result.csv')

# NOTE 缓存策略
hc_path = Tool.File.path_add_site('hc/4_hc.json')
hc_save_num = 20
# NOTE

ts_num = None
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
clean_desc = True
time_sleep = 1.5
_mk = Tool.make_counter(ts_num)
@Tool.zs('重写=>请求详细页面，以求获取自定义字段')
def get_zd(url):
    _zdy_zd = Tool.custom_key
    dic = {}
    # 返回字典形式
    # res = Tool.get(url)
    # html = etree.HTML(res.text)

    # ds = html.xpath('//div[@class="product-tabs"]/div')
    # for d in ds:
    #     d_name = d.xpath('./div[@class="product-tab__heading"]//text()')
    #
    #     d_name = ''.join(d_name).strip()
    #     if 'Care instructions' in d_name:
    #         continue
    #
    #     d_df = d.xpath('./div[@class="product-tab__content-container"]/div')
    #
    #     d_df = Tool.HTML.clean_product_desc(d_df)
    #
    #     dic[d_name] = d_df

    return dic

@Tool.zs(f'清洗desc样式')
def _cl_desc(desc):
    if clean_desc:
        return Tool.HTML.clean_product_desc_str(desc)
    else:
        return desc

@Tool.zs('通过 Shopify product handle 获取产品数据，带有精确的 429 处理机制')
def get_product_by_handle(session, handle, retries=5):

    url = f"https://www.{brand}.com/products/{handle}.json"

    for attempt in range(retries):
        try:
            r = session.get(url, headers=headers, timeout=15, cookies=ck)
            if r.status_code == 429:
                wait_time = 5 + (attempt * 3)  # 每次被限流，休眠时间递增 (5s, 8s, 11s...)
                tqdm.write(f"\n[⚠️ 429 频率限制] 请求过快，强制休眠 {wait_time} 秒... ({handle})")
                time.sleep(wait_time)
                continue

            if r.status_code == 404:
                tqdm.write(f"\n[INFO] {handle} 页面不存在 (404),url:{url}")
                return None

            r.raise_for_status()
            data = r.json()

            zdy_data = get_zd(url.replace('.json', ''))

            time.sleep(time_sleep)
            shopify_product = data.get("product")
            shopify_product[Tool.custom_key] = zdy_data
            shopify_product['__url'] = url

            return shopify_product

        except requests.exceptions.RequestException as e:
            tqdm.write(f"\n[WARN] {handle} 网络异常: {e}, 第 {attempt + 1}/{retries} 次重试")
            time.sleep(time_sleep + 1.5 + attempt)
        except Exception as e:
            tqdm.write(f"\n[ERROR] {handle} 未知异常: {e}")
            time.sleep(time_sleep + 1.5)

    return None

@Tool.zs('将Shopify产品格式转换为WooCommerce格式')
def shopify_to_woocommerce(shopify_product, custom_categories=None):
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
    woo_product['Images'] = Tool.config.images_split.join(image_urls)

    # 填写属性
    if shopify_product.get('options'):
        for i, option in enumerate(shopify_product.get('options', [])):
            attr_num = i + 1
            woo_product[f'Attribute {attr_num} name'] = option.get('name', '')
            woo_product[f'Attribute {attr_num} value(s)'] = ','.join(option.get('values', []))
            woo_product[f'Attribute {attr_num} visible'] = 0
            woo_product[f'Attribute {attr_num} global'] = 1
    # 添加自定义字段到父类
    zdy_data = shopify_product.get(Tool.custom_key, {})
    if zdy_data:
        for key, value in zdy_data.items():
            k = Tool.Product.build_custom_field_name(key)
            woo_product[k] = value
    return woo_product

@Tool.zs('为Shopify产品创建变体产品')
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

        # 变体不需要自定义字段值，置空
        zdy_data = shopify_product.get(Tool.custom_key, {})
        if zdy_data:
            for key in zdy_data:
                k = Tool.Product.build_custom_field_name(key)
                variation[k] = ''
        variations.append(variation)

    return variations

def main():

    product_urls = Tool.File.load_json(quchong_file__path)
    if not product_urls:
        return
    print(f"产品 URL 数量: {len(product_urls)}")

    detail_url_data = Tool.File.load_json(detail_file__path)
    if not detail_url_data:
        return
    print(f"顺序分类数: {len(detail_url_data)}")

    _hc_data = Tool.File.load_json(hc_path)
    print("\n开始按 URL 直接抓取产品...")

    session = requests.Session(impersonate="firefox")

    num = 0
    for url in tqdm(product_urls):
        handle = Tool.URL.get_handle(url)
        if not handle or handle in _hc_data:
            continue
        product = get_product_by_handle(session, handle)




        _cur = _mk()
        if _cur == 0:
            Tool.print(f'测试结束')
            break

        if product:
            num += 1
            _hc_data[handle] = product

            if num == hc_save_num:
                num = 0
                Tool.File.save_json(_hc_data,hc_path)

            zdy_df = product[Tool.custom_key]

            if len(zdy_df) > 0:
                print(url)
                print(zdy_df.keys())

    print(f"\n共抓取到 Shopify 产品: {len(_hc_data)}")
    Tool.File.save_json(_hc_data,hc_path)


    _products = []
    missing_handles = []

    print("\n开始按 URL 顺序生成 CSV 数据...")

    for category_path, urls in detail_url_data.items():
        for url in urls:
            handle = Tool.URL.get_handle(url)
            shopify_product = _hc_data.get(handle)
            if not shopify_product:
                missing_handles.append(handle)
                continue
            shopify_product['body_html'] = _cl_desc(shopify_product['body_html'])
            woo_product = shopify_to_woocommerce(
                shopify_product,
                custom_categories=category_path
            )

            variations = create_variation_products(shopify_product, woo_product)

            _products.append(woo_product)

            if variations:
                _products.extend(variations)

    if _products:
        Tool.File.save_csv(_products,save_path)
        print(f"成功保存 {len(_products)} 个产品到 {save_path}")
        print(f"其中包含 {sum(1 for p in _products if p['Type'] == 'variable')} 个主产品")
        print(f"其中包含 {sum(1 for p in _products if p['Type'] == 'variation')} 个变体产品")
    else:
        print("未生成任何产品")


if __name__ == "__main__":
    main()
    Tool.print(f'当前是否清洗desc:{clean_desc}')