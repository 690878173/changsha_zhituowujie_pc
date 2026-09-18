import pandas as pd

from config import Tool
from _ljp.mb.base import Quchong


input_file = Tool.File.path_add_site("res/result.csv")
output_file = Tool.File.path_add_site("fwq/quchong.csv")


class Pc(Quchong):
    """Preserve literal SKUs and atomic category paths during deduplication."""

    def merge_categories(self, group):
        categories = []
        for value in group["Categories"].dropna():
            category = str(value).strip()
            if category and category not in categories:
                categories.append(category)
        row = group.iloc[0:1].copy()
        row["Categories"] = " | ".join(categories)
        return row

    def run(self):
        df = pd.read_csv(self.input_file, dtype=str, keep_default_na=False)
        df["_ljp_order"] = range(len(df))
        result = (
            df.groupby(["SKU"], sort=False, dropna=False)
            .apply(self.merge_categories)
            .reset_index(drop=True)
            .sort_values("_ljp_order")
            .drop(columns=["_ljp_order"])
        )
        self.Tool.File.save_csv(result, self.output_file)
        self.Tool.print(f"去重合并完成，已保存到 {self.output_file}", color="green")
        return result


if __name__ == "__main__":
    Pc(Tool, input_file, output_file).run()
