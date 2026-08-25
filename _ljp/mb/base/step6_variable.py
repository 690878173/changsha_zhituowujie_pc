"""Create WooCommerce-style variable parent rows from variation rows."""

import pandas as pd


class Step6Variable:
    """Insert one ``variable`` row before each family of variation rows."""

    DEFAULT_MERGE_FIELDS = ("Images", "Attribute 1 value(s)", "Attribute 2 value(s)")
    DEFAULT_DESCRIPTION_FIELDS = ("Description",)

    def __init__(self, tool, input_file=None, output_file=None, *, merge_fields=None,
                 description_fields=None):
        self.tool = tool
        self.Tool = tool
        self.input_file = input_file or tool.File.path_add_site("res/quchong.csv")
        self.output_file = output_file or tool.File.path_add_site("fwq/variable.csv")
        self.merge_fields = tuple(merge_fields or self.DEFAULT_MERGE_FIELDS)
        self.description_fields = tuple(description_fields or self.DEFAULT_DESCRIPTION_FIELDS)

    def _split_value(self, value, field):
        text = str(value)
        if field != "Images":
            return text.split(",")
        configured = self.Tool.config.images_split
        separator = configured if configured and configured in text else ","
        return text.split(separator)

    def _join_unique(self, values, field):
        separator = ","
        collected = []
        for value in values:
            for part in self._split_value(value, field):
                part = part.strip()
                if part and part not in collected:
                    collected.append(part)
        return separator.join(collected)

    def run(self):
        df = pd.read_csv(self.input_file, dtype=str).fillna("")
        required = {"Type", "SKU", "Parent"}
        missing = required.difference(df.columns)
        if missing:
            raise KeyError(f"生成父商品缺少字段：{sorted(missing)}")

        df["_ljp_order"] = range(len(df))
        variations = df[(df["Type"].str.lower() == "variation") & (df["Parent"] != "")]
        other_rows = df.drop(variations.index)
        generated = []

        group_fields = ["Parent"]
        if "Categories" in variations.columns:
            group_fields.append("Categories")
        for _, group in variations.groupby(group_fields, sort=False, dropna=False):
            parent = group.iloc[0].copy()
            parent["Type"] = "variable"
            parent["SKU"] = parent["Parent"]
            parent["Parent"] = ""
            parent["_ljp_order"] = group["_ljp_order"].min() - 0.5
            for field in self.merge_fields:
                if field in group.columns:
                    parent[field] = self._join_unique(group[field], field)
            for field in self.description_fields:
                if field in group.columns:
                    parent[field] = group[field].iloc[0]
            generated.append(parent.to_dict())

            for _, row in group.iterrows():
                child = row.copy()
                for field in self.merge_fields:
                    if field in child and child[field]:
                        child[field] = self._split_value(child[field], field)[0].strip()
                for field in self.description_fields:
                    if field in child:
                        child[field] = ""
                generated.append(child.to_dict())

        result = pd.DataFrame(generated)
        if not other_rows.empty:
            result = pd.concat([result, other_rows], ignore_index=True)
        if result.empty:
            result = df.drop(columns=["_ljp_order"])
        else:
            result = result.sort_values("_ljp_order").drop(columns=["_ljp_order"])
        self.Tool.File.save_csv(result, self.output_file)
        self.Tool.print(f"父商品生成完成，保存至 {self.output_file}", color="green")
        return result
