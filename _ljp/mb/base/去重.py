"""步骤5：按 SKU 去重合并分类模板

通用流程：读取 result.csv -> 按 SKU 分组合并 Categories -> 恢复原顺序 -> 输出 quchong.csv
该步骤两个模板逻辑一致，完全通用，无需子类覆写。
"""
import pandas as pd


class Quchong:
    """SKU 去重合并基类"""

    def __init__(self, tool, input_file, output_file):
        self.tool = tool
        self.Tool = tool
        self.input_file = input_file
        self.output_file = output_file

    def merge_categories(self, group):
        """合并相同商品的 Categories，保持原始顺序并去重，只返回一行"""
        base_categories = group['Categories'].iloc[0]
        other_categories = group['Categories'].iloc[1:].dropna().unique()

        if pd.isna(base_categories):
            base_categories = other_categories[0] if len(other_categories) > 0 else ''
            other_categories = other_categories[1:]

        all_categories = []
        seen = set()

        if not pd.isna(base_categories):
            for cat in base_categories.split(','):
                cat = cat.strip()
                if cat and cat not in seen:
                    seen.add(cat)
                    all_categories.append(cat)

        for categories in other_categories:
            if not pd.isna(categories):
                for cat in categories.split(','):
                    cat = cat.strip()
                    if cat and cat not in seen:
                        seen.add(cat)
                        all_categories.append(cat)

        # 检查同 SKU 不同行的数据差异（除 Categories/url/SKU 外）
        if len(group) > 1:
            skip_cols = {'Categories', 'OriginalOrder', 'SKU', 'url'}
            compare_cols = [c for c in group.columns if c not in skip_cols]
            first = group.iloc[0]
            for i in range(1, len(group)):
                current = group.iloc[i]
                for col in compare_cols:
                    v1 = str(first[col]) if pd.notna(first[col]) else ''
                    v2 = str(current[col]) if pd.notna(current[col]) else ''
                    if v1 != v2:
                        self.Tool.print(
                            f'[SKU重复差异] SKU={first["SKU"]} 字段 [{col}] 不一致: '
                            f'"{v1}" != "{v2}"，可能上游数据有误',
                            'yellow',
                        )

        result = group.iloc[0:1].copy()
        result['Categories'] = ','.join(all_categories)
        return result

    def run(self):
        df = pd.read_csv(self.input_file)
        df["OriginalOrder"] = range(len(df))

        groupby_columns = ['SKU']
        for col in groupby_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')

        df_deduplicated = df.groupby(groupby_columns).apply(
            self.merge_categories
        ).reset_index(drop=True)

        df_sorted = df_deduplicated.sort_values(by=['OriginalOrder'])
        df_sorted = df_sorted.drop(columns=['OriginalOrder'])
        df_sorted.to_csv(self.output_file, index=False)

        self.Tool.print(f"去重合并完成，已保存到 {self.output_file}", color='green')
        return df_sorted
