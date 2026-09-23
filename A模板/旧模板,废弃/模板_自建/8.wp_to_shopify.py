import pandas as pd
import csv
import re
from collections import defaultdict

from config import Tool

# ================= 维护区：自定义字段写在这里 =================
EXTRA_META_COLUMNS = [

]

input_csv = Tool.File.path_add_site(r"res/picture.csv")
output_csv = Tool.File.path_add_site(r"data/wp_to_shopify.csv")



# =============================================================

def generate_unique_handle(title, brand=None, sku=None, counter=None):
    base = re.sub(r'[^a-zA-Z0-9]+', '-', str(title).lower()).strip('-')
    if brand:
        base += '-' + re.sub(r'[^a-zA-Z0-9]+', '-', str(brand).lower()).strip('-')
    if sku:
        base += '-' + re.sub(r'[^a-zA-Z0-9]+', '-', str(sku).lower()).strip('-')

    if counter is not None:
        if base not in counter:
            counter[base] = 1
            return base
        else:
            new_base = f"{base}-{counter[base]}"
            counter[base] += 1
            return new_base
    return base


def generate_shopify_rows(df):
    df['Parent'] = df['Parent'].astype(str).replace({'nan': ''}).str.replace('.0', '', regex=False)
    df['SKU'] = df['SKU'].astype(str).replace({'nan': ''}).str.replace('.0', '', regex=False)

    parent_products = df[df['Type'] == 'variable']
    variants = df[df['Type'] == 'variation']
    simple_products = df[df['Type'] == 'simple']

    handle_counter = defaultdict(int)

    # 1. 处理 variable 类型
    for _, parent in parent_products.iterrows():
        parent_sku = parent['SKU']
        product_variants = variants[variants['Parent'] == parent_sku]
        handle = generate_unique_handle(parent['Name'], parent.get('brand'), parent_sku, handle_counter)

        all_images = [img.strip() for img in str(parent.get('Images', '')).split(',') if img.strip()]

        option_names = []
        for i in range(1, 5):
            name_col = f'Attribute {i} name'
            if pd.notna(parent.get(name_col)) and parent[name_col]:
                option_names.append(parent[name_col])

        for i, (_, variant) in enumerate(product_variants.iterrows()):
            row = {}
            if i == 0:
                row.update({
                    'Handle': handle,
                    'Title': parent['Name'],
                    'Body (HTML)': parent['Description'],
                    'Vendor': parent.get('brand', ''),
                    'Type': parent.get('Tags', ''),
                    'Tags': parent.get('Categories', ''),
                    'Published': 'TRUE',
                    'Status': 'active'
                })
                for col in EXTRA_META_COLUMNS:
                    row[col] = parent.get(col, '')
                for j, option_name in enumerate(option_names):
                    row[f'Option{j + 1} Name'] = option_name
            else:
                row['Handle'] = handle
                row['Status'] = 'active'

            row.update({
                'Variant SKU': variant.get('SKU', ''),
                'Variant Inventory Qty': int(float(variant['Stock'])) if pd.notna(variant.get('Stock')) and variant[
                    'Stock'] != '' else 0,
                'Variant Price': variant.get('Sale price', ''),
                'Variant Compare At Price': variant.get('Regular price', ''),
                'Variant Inventory Policy': 'deny',
                'Variant Requires Shipping': 'TRUE',
                'Variant Taxable': 'False',
                'Variant Weight Unit': 'kg',
                'Variant Fulfillment Service': 'manual'
            })

            for j in range(len(option_names)):
                val_col = f'Attribute {j + 1} value(s)'
                if val_col in variant and pd.notna(variant[val_col]):
                    row[f'Option{j + 1} Value'] = variant[val_col]

            if i < len(all_images):
                row['Image Src'] = all_images[i]
                row['Image Position'] = i + 1
            if pd.notna(variant.get('Images')):
                row['Variant Image'] = variant['Images']

            yield row

        for img_idx in range(len(product_variants), len(all_images)):
            yield {'Handle': handle, 'Image Src': all_images[img_idx], 'Image Position': img_idx + 1,
                   'Status': 'active'}

    # 2. 处理 simple 类型
    for _, product in simple_products.iterrows():
        handle = generate_unique_handle(product['Name'], product.get('brand'), product.get('SKU'), handle_counter)
        row = {
            'Handle': handle,
            'Title': product['Name'],
            'Body (HTML)': product.get('Description', ''),
            'Vendor': product.get('brand', ''),
            'Type': product.get('Tags', ''),
            'Tags': product.get('Categories', ''),
            'Published': 'TRUE',
            'Variant SKU': product.get('SKU', ''),
            'Variant Inventory Qty': int(float(product['Stock'])) if pd.notna(product.get('Stock')) and product[
                'Stock'] != '' else 0,
            'Variant Price': product.get('Sale price', ''),
            'Variant Compare At Price': product.get('Regular price', ''),
            'Variant Inventory Policy': 'deny',
            'Variant Requires Shipping': 'TRUE',
            'Variant Taxable': 'False',
            'Variant Weight Unit': 'kg',
            'Variant Fulfillment Service': 'manual',
            'Status': 'active'
        }
        for col in EXTRA_META_COLUMNS:
            row[col] = product.get(col, '')

        all_images = [img.strip() for img in str(product.get('Images', '')).split(',') if img.strip()]
        if all_images:
            row['Image Src'] = all_images[0]
            row['Image Position'] = 1
        yield row

        for img_idx in range(1, len(all_images)):
            yield {'Handle': handle, 'Image Src': all_images[img_idx], 'Image Position': img_idx + 1,
                   'Status': 'active'}


def process_woocommerce_to_shopify_stream(input_file, output_file, chunksize=50000):
    # 补全了老版本中所有的 Google Shopping 相关字段
    shopify_columns = [
        "Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published",
        "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value",
        "Option3 Name", "Option3 Value", "Variant SKU", "Variant Grams",
        "Variant Inventory Tracker", "Variant Inventory Qty", "Variant Inventory Policy",
        "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price",
        "Variant Requires Shipping", "Variant Taxable", "Variant Barcode",
        "Image Src", "Image Position", "Image Alt Text", "Gift Card", "SEO Title",
        "SEO Description",
        "Google Shopping / Google Product Category",
        "Google Shopping / Gender",
        "Google Shopping / Age Group",
        "Google Shopping / MPN",
        "Google Shopping / AdWords Grouping",
        "Google Shopping / AdWords Labels",
        "Google Shopping / Condition",
        "Google Shopping / Custom Product",
        "Google Shopping / Custom Label 0",
        "Google Shopping / Custom Label 1",
        "Google Shopping / Custom Label 2",
        "Google Shopping / Custom Label 3",
        "Google Shopping / Custom Label 4",
        "Variant Image", "Variant Weight Unit", "Variant Tax Code",
        "Cost per item", "Status"
    ]

    # 动态把自定义列合并进去
    shopify_columns += EXTRA_META_COLUMNS

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=shopify_columns)
        writer.writeheader()

        total_rows = 0
        # 建议调大 chunksize 或者如果内存够直接不带 chunksize 读，防止跨块丢失变体
        for chunk in pd.read_csv(input_file, chunksize=chunksize, dtype=str, keep_default_na=False):
            for row in generate_shopify_rows(chunk):
                filtered_row = {k: v for k, v in row.items() if k in shopify_columns}
                writer.writerow(filtered_row)
                total_rows += 1
            print(f"已处理 {total_rows:,} 行...")

    print(f"✅ 转换完成！输出文件：{output_file}")


if __name__ == "__main__":
    process_woocommerce_to_shopify_stream(input_csv, output_csv)
    Tool.print('注意自定义字段是否写入列表')
    Tool.print('注意自定义字段是否写入列表')
    df = pd.read_csv(input_csv).columns
    Tool.print(f'当前字段:{df}')
