"""重组变体家族并清空子体重复字段，减小后续 CSV 体积。"""

from pathlib import Path

import pandas as pd

from config import Tool


input_path = Tool.File.path_add_site("fwq/variable.csv")
output_path = Tool.File.path_add_site("fwq/variable_cleaned.csv")


def repeated_parent_fields(columns):
    """Return fields that only need to be retained on the variable parent row."""
    return [
        column
        for column in columns
        if column == "Description" or "(product.metafields." in column.lower()
    ]


def unique_values(values, separator):
    """Join non-empty values in first-seen order without duplicates."""
    result = []
    seen = set()
    for value in values:
        for item in str(value).split(separator):
            item = item.strip()
            if item and item not in seen:
                seen.add(item)
                result.append(item)
    return separator.join(result)


def build_family(parent_sku, variations, parent_rows, repeated_fields, images_split):
    """Create one variable row followed by all of its variation rows."""
    template = parent_rows.iloc[0] if not parent_rows.empty else variations.iloc[0]
    parent = template.to_dict()
    parent["Type"] = "variable"
    parent["SKU"] = parent_sku
    parent["Parent"] = ""

    family_rows = pd.concat([parent_rows, variations], ignore_index=True)
    if "Categories" in family_rows:
        parent["Categories"] = unique_values(family_rows["Categories"], ",")
    if "Images" in family_rows:
        parent["Images"] = unique_values(family_rows["Images"], images_split)
    for column in (name for name in family_rows.columns if name.startswith("Attribute ") and name.endswith(" value(s)")):
        parent[column] = unique_values(family_rows[column], ",")
    for column in repeated_fields:
        values = family_rows[column]
        first_value = next((value for value in values if str(value).strip()), "")
        parent[column] = first_value

    children = variations.copy()
    children.loc[:, repeated_fields] = ""
    return [parent, *children.to_dict("records")]


def validate_family_order(data):
    """Raise before export if a child is not directly below its parent row."""
    expected_parent = None
    seen_parents = set()
    for index, row in data.iterrows():
        product_type = str(row["Type"]).strip().lower()
        if product_type == "variable":
            expected_parent = str(row["SKU"]).strip()
            if expected_parent in seen_parents:
                raise ValueError(f"第 {index + 1} 行重复 variable SKU: {expected_parent!r}")
            seen_parents.add(expected_parent)
        elif product_type == "variation" and str(row["Parent"]).strip() != expected_parent:
            raise ValueError(
                f"第 {index + 1} 行 variation 未紧跟父商品: Parent={row['Parent']!r}"
            )
        elif product_type != "variation":
            expected_parent = None


def clean_variant_fields(source=input_path, destination=output_path):
    data = pd.read_csv(source, dtype=str, keep_default_na=False)
    required = {"Type", "SKU", "Parent"}
    missing = required.difference(data.columns)
    if missing:
        raise KeyError(f"清洗变体字段缺少必要列：{sorted(missing)}")

    fields = repeated_parent_fields(data.columns)
    product_type = data["Type"].str.strip().str.lower()
    variations = data[product_type.eq("variation")].copy()
    variable_rows = data[product_type.eq("variable")].copy()
    other_rows = data[~product_type.isin(["variable", "variation"])].copy()
    empty_parent_rows = variations[variations["Parent"].str.strip().eq("")]
    if not empty_parent_rows.empty:
        raise ValueError(f"发现 {len(empty_parent_rows)} 条变体缺少 Parent")

    images_split = Tool.config.images_split or ","
    blocks = []
    for parent_sku, family_variations in variations.groupby("Parent", sort=False):
        parent_sku = str(parent_sku).strip()
        matching_parents = variable_rows[variable_rows["SKU"].str.strip().eq(parent_sku)]
        first_index = min(family_variations.index.min(), matching_parents.index.min() if not matching_parents.empty else family_variations.index.min())
        blocks.append((first_index, build_family(parent_sku, family_variations, matching_parents, fields, images_split)))
    for index, row in other_rows.iterrows():
        blocks.append((index, [row.to_dict()]))

    blocks.sort(key=lambda item: item[0])
    cleaned = pd.DataFrame([row for _, block in blocks for row in block], columns=data.columns)
    validate_family_order(cleaned)
    cleared_cells = int(variations[fields].ne("").sum().sum())
    duplicate_parents = len(variable_rows) - len(variations["Parent"].unique())

    Tool.File.save_csv(cleaned, destination)
    source_size = Path(source).stat().st_size
    destination_size = Path(destination).stat().st_size
    print(f"清洗字段：{fields}")
    print(f"清空变体重复单元格：{cleared_cells:,}")
    print(f"合并重复父商品：{duplicate_parents:,}")
    print(f"输出文件：{destination}")
    print(f"文件大小：{source_size / 1024 / 1024:.2f} MB -> {destination_size / 1024 / 1024:.2f} MB")
    return cleaned


if __name__ == "__main__":
    clean_variant_fields()
