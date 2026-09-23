
from _ljp.mb.amazon.step3 import YMXStep3

from config import Tool
input_path = Tool.File.path_add_site('data/2.json')
output_path = Tool.File.path_add_site('res/res.csv')
fail_file = Tool.File.path_add_site('fail/2.csv')
catch_path = Tool.File.path_add_site('hc/3/catch.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')





class S3(YMXStep3):
    def _validate_rows_before_cache(self, rows):
        """Apply Type-specific cache requirements immediately before persistence."""
        requirements = {
            "simple": ("SKU", "Name", "Images"),
            "variable": ("SKU", "Name", "Description", "Images"),
            "variation": ("SKU", "Name", "Parent"),
        }
        for position, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise ValueError(f"商品第 {position} 行不是字典，未写入缓存")

            product_type = str(row.get("Type") or "simple").strip().casefold()
            if product_type not in requirements:
                raise ValueError(
                    f"商品第 {position} 行 Type 无效，未写入缓存: {row.get('Type')!r}"
                )

            missing = [
                field
                for field in requirements[product_type]
                if not self._has_required_cache_value(row.get(field))
            ]
            if missing:
                raise ValueError(
                    f"商品第 {position} 行 {product_type} 必要字段缺失，未写入缓存: "
                    + ", ".join(missing)
                )

            if product_type != "variable":
                invalid_prices = [
                    field
                    for field in ("Sale price", "Regular price")
                    if not self._has_positive_price(row.get(field))
                ]
                if invalid_prices:
                    raise ValueError(
                        f"商品第 {position} 行 {product_type} 价格无效，未写入缓存: "
                        + ", ".join(invalid_prices)
                    )
            row["Stock"] = 1000
if __name__ == "__main__":
    S3(tool=Tool,
             input_path=input_path,
             output_path=output_path,
             fail_file=fail_file,
             catch_path=catch_path,
             index_path=index_path,
             output_ts_file=output_ts_file
             ).run()
