import pandas as pd
from config import Tool

input_file = Tool.File.path_add_site(r'res/result.csv')
output_file= Tool.File.path_add_site(r'fwq/quchong.csv')


def merge_categories(group):
    """
    合并相同商品的Categories和Images，保持原始顺序并去重，只返回一行数据
    """
    # 获取第一个非空值作为基础
    base_categories = group['Categories'].iloc[0]
    other_categories = group['Categories'].iloc[1:].dropna().unique()

    # 如果基础值为空，使用第一个非空值
    if pd.isna(base_categories):
        base_categories = other_categories[0] if len(other_categories) > 0 else ''
        other_categories = other_categories[1:]

    # 合并所有Categories，保持顺序
    all_categories = []
    seen = set()

    # 首先添加base_categories中的类别
    if not pd.isna(base_categories):
        for cat in base_categories.split(','):
            cat = cat.strip()
            if cat and cat not in seen:
                seen.add(cat)
                all_categories.append(cat)

    # 然后添加other_categories中的类别
    for categories in other_categories:
        if not pd.isna(categories):
            for cat in categories.split(','):
                cat = cat.strip()
                if cat and cat not in seen:
                    seen.add(cat)
                    all_categories.append(cat)

    result = group.iloc[0:1].copy()
    result['Categories'] = ','.join(all_categories)
    if 'Images' in group.columns:
        # 同一 SKU 可能因多个分类产生多行；图片也要按原始顺序合并，
        # 否则后续链接变体合并阶段无法恢复被首行覆盖的图片。
        separator = getattr(Tool.config, 'images_split', ',') or ','
        all_images = []
        seen_images = set()
        for images in group['Images']:
            value = '' if pd.isna(images) else str(images)
            for image in value.split(separator):
                image = image.strip()
                if image and image not in seen_images:
                    seen_images.add(image)
                    all_images.append(image)
        result['Images'] = separator.join(all_images)
    return result

def main():
    print("🔧【步骤 1】读取原始 CSV，记录行顺序...")
    df = pd.read_csv(input_file)

    # 添加一个顺序列，用于保证合并后恢复原顺序
    df["OriginalOrder"] = range(len(df))

    print("✔ 已记录原始顺序。")

    groupby_columns = ['SKU']
    for col in groupby_columns:
        if col in df.columns:
            df[col] = df[col].fillna('')
    print("\n🔧【步骤 2】按 SKU 合并 Categories 和 Images...")
    df_deduplicated = df.groupby(groupby_columns).apply(merge_categories).reset_index(drop=True)
    print("✔ 合并完成。")

    print("\n🔧【步骤 3】按原顺序恢复数据，不再按 Name/Type 排序...")
    df_sorted = df_deduplicated.sort_values(by=['OriginalOrder'])

    # 删除临时列
    df_sorted = df_sorted.drop(columns=['OriginalOrder'])

    print("✔ 已恢复原有顺序。保证导入 Shopify 后产品顺序保持一致。")

    print("\n🔧【步骤 4】保存 CSV...")
    df_sorted.to_csv(output_file, index=False)
    print(f"🎉 完成！文件已保存为 {output_file}")


if __name__ == "__main__":
    main()
