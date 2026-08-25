"""步骤8：WooCommerce → Shopify CSV 转换模板

通用流程：读取 picture.csv -> 逐行生成 Shopify 产品/变体/图片行 -> 流式写出 wp_to_shopify.csv。
两个模板输出列完全一致，差异仅在于：
    自建版   ：iterrows 逐行遍历，chunksize=50000
    Shopify版：itertuples 遍历（更快），chunksize=200000

本基类统一采用 itertuples 流式实现（输出一致且性能更优），并保留迭代/字段扩展点：
    EXTRA_META_COLUMNS     自定义元数据列（子类覆写）
    to_shopify_rows        行生成器（默认 itertuples，子类可覆写）
"""
import csv
import re
from collections import defaultdict

import pandas as pd

from _ljp import HTML


class Step8WpToShopify:
    """WP -> Shopify 转换基类"""

    # 自定义字段列（子类在维护区覆写）
    EXTRA_META_COLUMNS = []

    # 含空格/特殊字符列名 -> itertuples 属性名映射
    COLUMN_RENAME_MAP = {
        "Sale price": "sale_price",
        "Regular price": "regular_price",
        "Attribute 1 name": "attr_1_name",
        "Attribute 1 value(s)": "attr_1_value",
        "Attribute 2 name": "attr_2_name",
        "Attribute 2 value(s)": "attr_2_value",
        "Attribute 3 name": "attr_3_name",
        "Attribute 3 value(s)": "attr_3_value",
        "Attribute 4 name": "attr_4_name",
        "Attribute 4 value(s)": "attr_4_value",
    }

    SHOPIFY_COLUMNS = [
        "Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published",
        "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value",
        "Option3 Name", "Option3 Value", "Variant SKU", "Variant Grams",
        "Variant Inventory Tracker", "Variant Inventory Qty", "Variant Inventory Policy",
        "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price",
        "Variant Requires Shipping", "Variant Taxable", "Variant Barcode",
        "Image Src", "Image Position", "Image Alt Text", "Gift Card", "SEO Title",
        "SEO Description",
        "Google Shopping / Google Product Category",
        "Google Shopping / Gender",
        "Google Shopping / Age Group",
        "Google Shopping / MPN",
        "Google Shopping / AdWords Grouping",
        "Google Shopping / AdWords Labels",
        "Google Shopping / Condition",
        "Google Shopping / Custom Product",
        "Google Shopping / Custom Label 0",
        "Google Shopping / Custom Label 1",
        "Google Shopping / Custom Label 2",
        "Google Shopping / Custom Label 3",
        "Google Shopping / Custom Label 4",
        "Variant Image", "Variant Weight Unit", "Variant Tax Code",
        "Cost per item", "Status",
    ]

    CHUNKSIZE = 200000

    def __init__(self, tool, input_file=None, output_file=None):
        self.tool = tool
        self.Tool = tool
        self.input_file = input_file or tool.File.path_add_site("res/picture.csv")
        self.output_file = output_file or tool.File.path_add_site("data/wp_to_shopify.csv")
        self._handle_counter = defaultdict(int)

    # ================= 通用工具函数 =================

    @staticmethod
    def _to_name(col):
        return re.sub(r"[^a-zA-Z0-9_]", "_", col)

    def _build_rename_map(self):
        rename = dict(self.COLUMN_RENAME_MAP)
        for col in self.EXTRA_META_COLUMNS:
            rename[col] = self._to_name(col)
        return rename

    @staticmethod
    def _safe_int(value):
        try:
            v = str(value).strip()
            return int(float(v)) if v else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _make_handle(title, brand=None, sku=None):
        parts = [str(title)]
        if brand:
            parts.append(str(brand))
        if sku:
            parts.append(str(sku))
        return re.sub(r"[^a-zA-Z0-9]+", "-", "-".join(parts).lower()).strip("-")

    def _split_images(self, value):
        text = str(value)
        configured = self.Tool.config.images_split
        separator = configured if configured and configured in text else ","
        return [img.strip() for img in text.split(separator) if img.strip()]

    # ================= 专有逻辑（子类可覆写） =================

    def to_shopify_rows(self, chunk):
        """从单个 chunk 中逐行 yield Shopify 行字典（默认 itertuples 实现）。"""
        rename = self._build_rename_map()
        rename_cols = {k: v for k, v in rename.items() if k in chunk.columns}
        chunk = chunk.rename(columns=rename_cols)

        chunk["Parent"] = (
            chunk["Parent"].astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .replace({"nan": "", "None": ""})
        )
        chunk["SKU"] = (
            chunk["SKU"].astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .replace({"nan": "", "None": ""})
        )

        parents = chunk[chunk["Type"] == "variable"]
        variants_all = chunk[chunk["Type"] == "variation"]
        simples = chunk[chunk["Type"] == "simple"]

        extra = self.EXTRA_META_COLUMNS
        extra_attrs = {col: self._to_name(col) for col in extra}

        # 1. variable 产品
        for parent in parents.itertuples(index=False, name="ParentRow"):
            child_df = variants_all[variants_all["Parent"] == parent.SKU]

            base = self._make_handle(parent.Name, getattr(parent, "brand", None), parent.SKU)
            self._handle_counter[base] += 1
            handle = base if self._handle_counter[base] == 1 else f"{base}-{self._handle_counter[base] - 1}"

            all_images = self._split_images(getattr(parent, "Images", ""))

            option_names = []
            for i in range(1, 5):
                val = getattr(parent, f"attr_{i}_name", None)
                if pd.notna(val) and val:
                    option_names.append(val)

            num_opts = len(option_names)
            num_vars = len(child_df)

            for idx, var in enumerate(child_df.itertuples(index=False, name="VarRow")):
                row = {}
                if idx == 0:
                    row.update({
                        "Handle": handle, "Status": "active",
                        "Title": parent.Name,
                        "Body (HTML)": getattr(parent, "Description", ""),
                        "Vendor": getattr(parent, "brand", ""),
                        "Type": getattr(parent, "Tags", ""),
                        "Tags": getattr(parent, "Categories", ""),
                        "Published": "TRUE",
                    })
                    for col in extra:
                        row[col] = self.Tool.HTML.clean_product_desc_str(getattr(parent, extra_attrs[col], ""))
                    for j, oname in enumerate(option_names):
                        row[f"Option{j + 1} Name"] = oname
                else:
                    row["Handle"] = handle
                    row["Status"] = "active"

                row.update({
                    "Variant SKU": getattr(var, "SKU", ""),
                    "Variant Inventory Qty": self._safe_int(getattr(var, "Stock", "")),
                    "Variant Price": getattr(var, "sale_price", ""),
                    "Variant Compare At Price": getattr(var, "regular_price", ""),
                    "Variant Inventory Policy": "deny",
                    "Variant Requires Shipping": "TRUE",
                    "Variant Taxable": "False",
                    "Variant Weight Unit": "kg",
                    "Variant Fulfillment Service": "manual",
                })

                for j in range(num_opts):
                    val = getattr(var, f"attr_{j + 1}_value", None)
                    if pd.notna(val) and val:
                        row[f"Option{j + 1} Value"] = val

                if idx < len(all_images):
                    row["Image Src"] = all_images[idx]
                    row["Image Position"] = idx + 1

                variant_img = getattr(var, "Images", None)
                if pd.notna(variant_img):
                    row["Variant Image"] = variant_img

                yield row

            for img_idx in range(num_vars, len(all_images)):
                yield {
                    "Handle": handle, "Status": "active",
                    "Image Src": all_images[img_idx],
                    "Image Position": img_idx + 1,
                }

        # 2. simple 产品
        for prod in simples.itertuples(index=False, name="SimpleRow"):
            base = self._make_handle(prod.Name, getattr(prod, "brand", None), getattr(prod, "SKU", None))
            self._handle_counter[base] += 1
            handle = base if self._handle_counter[base] == 1 else f"{base}-{self._handle_counter[base] - 1}"

            row = {
                "Handle": handle, "Status": "active",
                "Title": prod.Name,
                "Body (HTML)": getattr(prod, "Description", ""),
                "Vendor": getattr(prod, "brand", ""),
                "Type": getattr(prod, "Tags", ""),
                "Tags": getattr(prod, "Categories", ""),
                "Published": "TRUE",
                "Variant SKU": getattr(prod, "SKU", ""),
                "Variant Inventory Qty": self._safe_int(getattr(prod, "Stock", "")),
                "Variant Price": getattr(prod, "sale_price", ""),
                "Variant Compare At Price": getattr(prod, "regular_price", ""),
                "Variant Inventory Policy": "deny",
                "Variant Requires Shipping": "TRUE",
                "Variant Taxable": "False",
                "Variant Weight Unit": "kg",
                "Variant Fulfillment Service": "manual",
            }
            for col in extra:
                row[col] = self.Tool.HTML.clean_product_desc_str(getattr(prod, extra_attrs[col], ""))

            all_images = self._split_images(getattr(prod, "Images", ""))
            if all_images:
                row["Image Src"] = all_images[0]
                row["Image Position"] = 1
            yield row

            for img_idx in range(1, len(all_images)):
                yield {
                    "Handle": handle, "Status": "active",
                    "Image Src": all_images[img_idx],
                    "Image Position": img_idx + 1,
                }

    # ================= 通用主流程 =================

    @staticmethod
    def _split_completed_groups(chunk, pending):
        """Keep the final variable product group until its next parent or EOF.

        Source rows are product-family ordered: one ``variable`` row followed
        by its ``variation`` rows. A CSV chunk may end midway through that
        family, so emitting the entire chunk would lose children in the next
        chunk. Simple rows are safe to emit as soon as they precede a retained
        final family.
        """
        data = pd.concat([pending, chunk], ignore_index=True) if pending is not None else chunk
        starts = data.index[data['Type'].eq('variable')].tolist()
        if not starts:
            # Plain simple-product feeds have no family boundary to wait for.
            return (data, None) if pending is None else (None, data)
        last_start = starts[-1]
        # A simple product after the last parent also closes that parent family.
        # Product rows are ordered by family, so it is safe to emit all rows.
        if data.index[(data.index > last_start) & data['Type'].eq('simple')].tolist():
            return data, None
        if last_start == 0:
            return None, data
        return data.iloc[:last_start].copy(), data.iloc[last_start:].copy()

    def run(self, input_file=None, output_file=None, chunksize=None):
        input_file = input_file or self.input_file
        output_file = output_file or self.output_file
        chunksize = chunksize or self.CHUNKSIZE

        columns = self.SHOPIFY_COLUMNS + self.EXTRA_META_COLUMNS
        col_set = set(columns)
        self._handle_counter = defaultdict(int)

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            total_rows = 0
            pending = None
            for chunk in pd.read_csv(input_file, chunksize=chunksize, dtype=str, keep_default_na=False):
                if 'Type' not in chunk.columns:
                    raise ValueError('Input CSV must contain a "Type" column.')
                complete, pending = self._split_completed_groups(chunk, pending)
                if complete is None or complete.empty:
                    continue
                for row in self.to_shopify_rows(complete):
                    writer.writerow({k: v for k, v in row.items() if k in col_set})
                    total_rows += 1
                print(f"已处理 {total_rows:,} 行...")

            if pending is not None and not pending.empty:
                for row in self.to_shopify_rows(pending):
                    writer.writerow({k: v for k, v in row.items() if k in col_set})
                    total_rows += 1
                print(f"已处理 {total_rows:,} 行...")

        print(f"转换完成！输出：{output_file}")

        self.Tool.print('注意自定义字段是否写入列表')
        source_columns = pd.read_csv(input_file, nrows=0).columns
        self.Tool.print(f'当前字段:{source_columns}')
        return output_file
