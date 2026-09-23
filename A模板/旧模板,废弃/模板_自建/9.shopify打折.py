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