"""
WooCommerce → Shopify CSV 转换
- 流式：yield + csv.DictWriter，内存稳定，每 chunk 内不累积
- itertuples() 替代 iterrows()，速度提升 10x+
"""
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

# ---- 列名映射：把含空格/特殊字符的列名改成 itertuples 可用的属性名 ----
COLUMN_RENAME_MAP = {
    'Sale price': 'sale_price',
    'Regular price': 'regular_price',
    'Attribute 1 name': 'attr_1_name',
    'Attribute 1 value(s)': 'attr_1_value',
    'Attribute 2 name': 'attr_2_name',
    'Attribute 2 value(s)': 'attr_2_value',
    'Attribute 3 name': 'attr_3_name',
    'Attribute 3 value(s)': 'attr_3_value',
    'Attribute 4 name': 'attr_4_name',
    'Attribute 4 value(s)': 'attr_4_value',
    # NOTE
}
def _to_name(col):
    return re.sub(r'[^a-zA-Z0-9_]', '_', col)

for i in EXTRA_META_COLUMNS:
    COLUMN_RENAME_MAP[i] = _to_name(i)

# ---- 工具函数 ----

def _safe_int(value):
    """安全转 int，失败返回 0"""
    try:
        v = str(value).strip()
        return int(float(v)) if v else 0
    except (ValueError, TypeError):
        return 0


def _make_handle(title, brand=None, sku=None):
    """生成 handle 前缀（不含去重后缀）"""
    parts = [str(title)]
    if brand:
        parts.append(str(brand))
    if sku:
        parts.append(str(sku))
    return re.sub(r'[^a-zA-Z0-9]+', '-', '-'.join(parts).lower()).strip('-')


# ---- 核心生成器（流式 yield）----

def to_shopify_rows(chunk):
    """
    从一个 chunk 中 yield shopify 行。
    要求：variable + 其变体必须在同一 chunk 内。
    """
    # 重命名含空格的列，使之适配 itertuples
    rename_cols = {k: v for k, v in COLUMN_RENAME_MAP.items() if k in chunk.columns}
    chunk = chunk.rename(columns=rename_cols)

    # 批量清洗 SKU / Parent（向量化）
    chunk['Parent'] = (
        chunk['Parent'].astype(str)
        .str.replace(r'\.0$', '', regex=True)
        .replace({'nan': '', 'None': ''})
    )
    chunk['SKU'] = (
        chunk['SKU'].astype(str)
        .str.replace(r'\.0$', '', regex=True)
        .replace({'nan': '', 'None': ''})
    )

    parents = chunk[chunk['Type'] == 'variable']
    variants_all = chunk[chunk['Type'] == 'variation']
    simples = chunk[chunk['Type'] == 'simple']

    handle_counter = defaultdict(int)

    # ===== 1. Variable 产品（外层 itertuples，内层 itertuples）=====
    for parent in parents.itertuples(index=False, name='ParentRow'):
        child_mask = variants_all['Parent'] == parent.SKU
        # 用 mask 取子集 avoids repeated boolean indexing copy
        child_df = variants_all[child_mask]

        # handle 生成 + 去重
        base = _make_handle(parent.Name, getattr(parent, 'brand', None), parent.SKU)
        handle_counter[base] += 1
        handle = base if handle_counter[base] == 1 else f"{base}-{handle_counter[base] - 1}"

        # 图片列表
        raw_imgs = getattr(parent, 'Images', '')
        all_images = [img.strip() for img in str(raw_imgs).split(',') if img.strip()]

        # Option Names
        option_names = []
        for i in range(1, 5):
            val = getattr(parent, f'attr_{i}_name', None)
            if pd.notna(val) and val:
                option_names.append(val)

        num_opts = len(option_names)
        num_vars = len(child_df)

        for idx, var in enumerate(child_df.itertuples(index=False, name='VarRow')):
            row = {}

            if idx == 0:
                # 第一行带上产品级信息
                row.update({
                    'Handle': handle, 'Status': 'active',
                    'Title': parent.Name,
                    'Body (HTML)': getattr(parent, 'Description', ''),
                    'Vendor': getattr(parent, 'brand', ''),
                    'Type': getattr(parent, 'Tags', ''),
                    'Tags': getattr(parent, 'Categories', ''),
                    'Published': 'TRUE',
                })
                for col in EXTRA_META_COLUMNS:
                    new_col = COLUMN_RENAME_MAP[col]
                    row[col] = getattr(parent, new_col, '')
                for j, oname in enumerate(option_names):
                    row[f'Option{j + 1} Name'] = oname
            else:
                row['Handle'] = handle
                row['Status'] = 'active'

            # 变体字段
            row.update({
                'Variant SKU': getattr(var, 'SKU', ''),
                'Variant Inventory Qty': _safe_int(getattr(var, 'Stock', '')),
                'Variant Price': getattr(var, 'sale_price', ''),
                'Variant Compare At Price': getattr(var, 'regular_price', ''),
                'Variant Inventory Policy': 'deny',
                'Variant Requires Shipping': 'TRUE',
                'Variant Taxable': 'False',
                'Variant Weight Unit': 'kg',
                'Variant Fulfillment Service': 'manual',
            })

            # Option Values
            for j in range(num_opts):
                val = getattr(var, f'attr_{j + 1}_value', None)
                if pd.notna(val) and val:
                    row[f'Option{j + 1} Value'] = val

            # 图片分配
            if idx < len(all_images):
                row['Image Src'] = all_images[idx]
                row['Image Position'] = idx + 1

            variant_img = getattr(var, 'Images', None)
            if pd.notna(variant_img):
                row['Variant Image'] = variant_img

            yield row

        # 多余图片
        for img_idx in range(num_vars, len(all_images)):
            yield {
                'Handle': handle, 'Status': 'active',
                'Image Src': all_images[img_idx],
                'Image Position': img_idx + 1,
            }

    # ===== 2. Simple 产品（itertuples）=====
    for prod in simples.itertuples(index=False, name='SimpleRow'):
        base = _make_handle(prod.Name, getattr(prod, 'brand', None), getattr(prod, 'SKU', None))
        handle_counter[base] += 1
        handle = base if handle_counter[base] == 1 else f"{base}-{handle_counter[base] - 1}"

        row = {
            'Handle': handle, 'Status': 'active',
            'Title': prod.Name,
            'Body (HTML)': getattr(prod, 'Description', ''),
            'Vendor': getattr(prod, 'brand', ''),
            'Type': getattr(prod, 'Tags', ''),
            'Tags': getattr(prod, 'Categories', ''),
            'Published': 'TRUE',
            'Variant SKU': getattr(prod, 'SKU', ''),
            'Variant Inventory Qty': _safe_int(getattr(prod, 'Stock', '')),
            'Variant Price': getattr(prod, 'sale_price', ''),
            'Variant Compare At Price': getattr(prod, 'regular_price', ''),
            'Variant Inventory Policy': 'deny',
            'Variant Requires Shipping': 'TRUE',
            'Variant Taxable': 'False',
            'Variant Weight Unit': 'kg',
            'Variant Fulfillment Service': 'manual',
        }
        for col in EXTRA_META_COLUMNS:
            new_col = COLUMN_RENAME_MAP[col]
            row[col] = getattr(prod, new_col, '')

        raw_imgs = getattr(prod, 'Images', '')
        all_images = [img.strip() for img in str(raw_imgs).split(',') if img.strip()]
        if all_images:
            row['Image Src'] = all_images[0]
            row['Image Position'] = 1
        yield row

        for img_idx in range(1, len(all_images)):
            yield {
                'Handle': handle, 'Status': 'active',
                'Image Src': all_images[img_idx],
                'Image Position': img_idx + 1,
            }


# ===== 主流程 =====

def process_woocommerce_to_shopify_stream(input_file, output_file, chunksize=200000):
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
    ] + EXTRA_META_COLUMNS

    # set 查找比 list 快
    col_set = set(shopify_columns)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=shopify_columns)
        writer.writeheader()

        total_rows = 0
        for chunk in pd.read_csv(input_file, chunksize=chunksize, dtype=str, keep_default_na=False):
            for row in to_shopify_rows(chunk):
                writer.writerow({k: v for k, v in row.items() if k in col_set})
                total_rows += 1
            print(f"已处理 {total_rows:,} 行...")

    print(f"转换完成！输出：{output_file}")


if __name__ == "__main__":
    process_woocommerce_to_shopify_stream(input_csv, output_csv)
    Tool.print('注意自定义字段是否写入列表')
    df = pd.read_csv(input_csv).columns
    Tool.print(f'当前字段:{df}')
