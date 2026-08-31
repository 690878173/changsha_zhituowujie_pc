import pandas as pd

from config import Tool

input_file = Tool.File.path_add_site('res/quchong.csv')
output_file = Tool.File.path_add_site('fwq/variable.csv')




# images,size,color
# 变体字段
merge_fields = [
        "Images",
        "Attribute 1 value(s)",
        "Attribute 2 value(s)"
    ]

# 存放到父体的字段
desc_like_fields = [
]

def process_csv(merge_fields=None, desc_like_fields=None):
    if merge_fields is None:
        merge_fields = ["Images"]

    if desc_like_fields is None:
        desc_like_fields = ["Description"]

    print(f"🔄 正在读取文件: {input_file} ...")
    df = pd.read_csv(input_file)
    df.columns = df.columns.str.strip()

    required_cols = ["Type", "Parent", "SKU"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"CSV 文件缺少必要列: {col}，实际列名: {df.columns.tolist()}")


    # 记录原始行顺序（排序索引）
    df["_original_order"] = df.index

    # 分离变体行与其他行（simple 类型）
    is_variation = df["Type"] == "variation"
    variation_df = df[is_variation].copy()
    other_df = df[~is_variation].copy()



    group_fields = ["Parent"]
    if "Categories" in df.columns:
        # 填充空分类防止分组丢失
        variation_df["Categories"] = variation_df["Categories"].fillna("")
        group_fields.append("Categories")

    # 保持分组时的顺序性
    grouped = variation_df.groupby(group_fields, sort=False, dropna=False)

    result_rows = []

    for _, group in grouped:
        # 组内第一个变体作为父商品模板
        first_row = group.iloc[0]
        parent_sku = first_row["Parent"]
        min_order = group["_original_order"].min()

        # ----- 构建父商品（variable）行 -----
        parent_row = first_row.copy()
        parent_row["Type"] = "variable"
        parent_row["SKU"] = parent_sku
        parent_row["Parent"] = ""  # 清空父商品的 Parent

        # 父商品排在所属变体组的最前面（比最小索引小0.5）
        parent_row["_original_order"] = min_order - 0.5

        # 合并 merge_fields：去重合并
        for field in merge_fields:
            if field not in df.columns:
                continue
            # 确定分隔符（图片用特殊分隔符，其他用逗号）
            separator = Tool.config.images_split if field == "Images" else ","
            # 收集该组所有变体的该字段值（去重）
            unique_vals = set()
            for val in group[field].dropna().astype(str):
                for item in val.split(separator):
                    item = item.strip()
                    if item:
                        unique_vals.add(item)
            parent_row[field] = separator.join(sorted(unique_vals))  # 排序保证一致性

        # 处理 desc_like_fields：只取第一个变体的值
        for field in desc_like_fields:
            if field in df.columns:
                first_val = group[field].dropna()
                parent_row[field] = first_val.iloc[0] if not first_val.empty else ""

        result_rows.append(parent_row.to_dict())

        # ----- 处理每个子变体（variation）行 -----
        for _, row in group.iterrows():
            child_row = row.copy()
            # merge_fields 只保留第一个值（按分隔符分割）
            for field in merge_fields:
                if field in df.columns and pd.notna(child_row[field]):
                    separator = Tool.config.images_split if field == "Images" else ","
                    parts = str(child_row[field]).split(separator)
                    child_row[field] = parts[0].strip() if parts else ""
            # desc_like_fields 清空
            for field in desc_like_fields:
                if field in df.columns:
                    child_row[field] = ""
            # 子变体保持原顺序索引
            result_rows.append(child_row.to_dict())

    # 合并所有行（父商品+子变体+其他行）
    final_df = pd.DataFrame(result_rows)
    if not other_df.empty:
        final_df = pd.concat([final_df, other_df], ignore_index=True)

    # 按 _original_order 排序，恢复原始顺序
    final_df = final_df.sort_values("_original_order").drop(columns=["_original_order"])

    # 保存
    final_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ 处理完成，结果保存到 {output_file}")


def main():
    process_csv(merge_fields, desc_like_fields)




# 运行示例
if __name__ == "__main__":
    main()
    for i in range(3):
        Tool.print(f'当前使用变体字段：{merge_fields}\n使用父体字段:{desc_like_fields}')