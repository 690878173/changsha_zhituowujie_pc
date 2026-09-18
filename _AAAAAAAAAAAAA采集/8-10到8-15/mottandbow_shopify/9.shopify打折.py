import pandas as pd
from config import Tool

# 原始 CSV 路径
input_path = Tool.File.path_add_site('data/wp_to_shopify.csv')
# 输出 CSV 路径
output_path = Tool.File.dz_path()

Tool.File.create_dir(output_path)


# 读取 CSV
df = pd.read_csv(input_path, dtype=str).fillna("")

# 确保价格列为浮点数
df['Variant Compare At Price'] = pd.to_numeric(df['Variant Compare At Price'], errors='coerce')

# 如果某个商品的任意子类价格为 0，删除该商品的父类和所有子类数据
zero_price_handles = df.loc[df['Variant Compare At Price'].eq(0), 'Handle'].unique()
deleted_count = df['Handle'].isin(zero_price_handles).sum()
if len(zero_price_handles) > 0:
    df = df[~df['Handle'].isin(zero_price_handles)].copy()

print(f"检测到价格为 0 的商品 {len(zero_price_handles)} 个，共删除父类和子类数据 {deleted_count} 行")

# 打五折（50% 的价格）
df['Variant Price'] = df['Variant Compare At Price'] * Tool.zk

# 可选：保留两位小数
df['Variant Price'] = df['Variant Price'].round(2)

# 保存到新的 CSV
df.to_csv(output_path, index=False)

print(f"处理完成，新文件已保存到: {output_path}")

Tool.print(f'当前使用折扣:{Tool.zk}')

source_columns = pd.read_csv(output_path, nrows=0).columns
Tool.print(f'当前字段:{source_columns}')


'''
=====>当前字段:Index(['Handle', 'Title', 'Body (HTML)', 'Vendor', 'Type', 'Tags', 'Published',
       'Option1 Name', 'Option1 Value', 'Option2 Name', 'Option2 Value',
       'Option3 Name', 'Option3 Value', 'Variant SKU', 'Variant Grams',
       'Variant Inventory Tracker', 'Variant Inventory Qty',
       'Variant Inventory Policy', 'Variant Fulfillment Service',
       'Variant Price', 'Variant Compare At Price',
       'Variant Requires Shipping', 'Variant Taxable', 'Variant Barcode',
       'Image Src', 'Image Position', 'Image Alt Text', 'Gift Card',
       'SEO Title', 'SEO Description',
       'Google Shopping / Google Product Category', 'Google Shopping / Gender',
       'Google Shopping / Age Group', 'Google Shopping / MPN',
       'Google Shopping / AdWords Grouping',
       'Google Shopping / AdWords Labels', 'Google Shopping / Condition',
       'Google Shopping / Custom Product', 'Google Shopping / Custom Label 0',
       'Google Shopping / Custom Label 1', 'Google Shopping / Custom Label 2',
       'Google Shopping / Custom Label 3', 'Google Shopping / Custom Label 4',
       'Variant Image', 'Variant Weight Unit', 'Variant Tax Code',
       'Cost per item', 'Status'],
      dtype='object')



'''