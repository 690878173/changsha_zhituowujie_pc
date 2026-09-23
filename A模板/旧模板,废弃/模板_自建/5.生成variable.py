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

    # 1. 记录原始顺序（关键步骤！）
    # 给每一行一个身份证号，0, 1, 2, 3...
    df["_original_sort_index"] = df.index

    required_cols = ["Type", "Parent", "SKU"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"CSV 文件缺少必要列: {col}，实际列名: {df.columns.tolist()}")

    # 分离数据
    variation_df = df[df["Type"] == "variation"].copy()
    other_df = df[df["Type"] != "variation"].copy()

    result_rows = []

    group_fields = ["Parent"]
    if "Categories" in df.columns:
        # 填充空分类防止分组丢失
        variation_df["Categories"] = variation_df["Categories"].fillna("")
        group_fields.append("Categories")

    # 保持分组时的顺序性
    variation_group = variation_df.groupby(group_fields, sort=False, dropna=False)

    for group_key, group in variation_group:
        parent_sku = group["Parent"].iloc[0]

        # 获取该组中最小的索引值（即第一行变体的位置）
        min_index = group["_original_sort_index"].min()

        # ========== 1. 构建 variable (父商品) 行 ==========
        variable_row = group.iloc[0].copy()
        variable_row["Type"] = "variable"
        variable_row["SKU"] = parent_sku
        variable_row["Parent"] = ""  # 记得清空父商品的 Parent

        # 核心技巧：让父商品排在第一行变体的前面一点点
        # 比如第一行变体是 10，父商品就是 9.5
        variable_row["_original_sort_index"] = min_index - 0.5

        # merge_fields 多值合并
        for field in merge_fields:
            if field not in df.columns:
                continue
            all_values = []
            # 过滤空值并转换成字符串
            raw_series = group[field].dropna().astype(str)
            for v in raw_series:
                split_values = [x.strip() for x in v.split(",") if x.strip()]
                for val in split_values:
                    if val not in all_values:
                        all_values.append(val)
            variable_row[field] = ",".join(all_values)

        # desc_like_fields：只保留第一条
        for field in desc_like_fields:
            if field in df.columns:
                first_value = group[field].dropna()
                variable_row[field] = first_value.iloc[0] if len(first_value) > 0 else ""

        result_rows.append(variable_row.to_dict())

        # ========== 2. 处理 variation (子变体) 行 ==========
        for _, row in group.iterrows():
            row_dict = row.to_dict()

            # merge_fields 取第一条值
            for field in merge_fields:
                if field in df.columns and pd.notna(row_dict[field]):
                    row_dict[field] = str(row_dict[field]).split(",")[0].strip()

            # desc_like_fields 清空
            for field in desc_like_fields:
                if field in df.columns:
                    row_dict[field] = ""

            # 子变体保持原有的 _original_sort_index 不变
            result_rows.append(row_dict)

    # 3. 合并所有数据
    # 将生成的父子数据 + 之前分离出去的 simple 数据合并
    final_df = pd.DataFrame(result_rows)
    if not other_df.empty:
        final_df = pd.concat([final_df, other_df], ignore_index=True)

    # 4. 核心步骤：按照 _original_sort_index 排序
    # 这样 Simple 商品会回到原来的位置，Variable 父商品会插在它的子变体正上方
    final_df = final_df.sort_values(by="_original_sort_index")

    # 5. 删除辅助排序列
    final_df = final_df.drop(columns=["_original_sort_index"])

    # 保存
    final_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ 处理完成，数据顺序已还原，结果保存到 {output_file}")


def main():
    process_csv(merge_fields, desc_like_fields)




# 运行示例
if __name__ == "__main__":
    main()
    for i in range(3):
        Tool.print(f'当前使用变体字段：{merge_fields}\n使用父体字段:{desc_like_fields}')