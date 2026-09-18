import pandas as pd
from config import Tool

input_file = Tool.File.path_add_site(r'res/result.csv')
output_file= Tool.File.path_add_site(r'fwq/quchong.csv')


def merge_categories(group):
    """
    合并相同商品的 Categories，保持目录键原样、原始顺序并去重。

    Tool.to_ml_data() 用逗号编码祖级显示名，不能再按逗号拆分。
    多个独立目录键使用 " | " 分隔。
    """
    all_categories = []
    seen = set()

    for categories in group['Categories']:
        if pd.isna(categories):
            continue
        category = str(categories).strip()
        if category and category not in seen:
            seen.add(category)
            all_categories.append(category)

    result = group.iloc[0:1].copy()
    result['Categories'] = ' | '.join(all_categories)
    return result

def main():
    print("[1/4] Reading source CSV and recording row order...")
    df = pd.read_csv(input_file)

    # 添加一个顺序列，用于保证合并后恢复原顺序
    df["OriginalOrder"] = range(len(df))

    print("Original row order recorded.")

    groupby_columns = ['SKU']
    for col in groupby_columns:
        if col in df.columns:
            df[col] = df[col].fillna('')
    print("\n[2/4] Merging Categories by SKU...")
    df_deduplicated = df.groupby(groupby_columns).apply(merge_categories).reset_index(drop=True)
    print("Category merge complete.")

    print("\n[3/4] Restoring original row order...")
    df_sorted = df_deduplicated.sort_values(by=['OriginalOrder'])

    # 删除临时列
    df_sorted = df_sorted.drop(columns=['OriginalOrder'])

    print("Original row order restored.")

    print("\n[4/4] Writing deduplicated CSV...")
    df_sorted.to_csv(output_file, index=False)
    print(f"Complete: {output_file}")


if __name__ == "__main__":
    main()
