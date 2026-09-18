"""Deduplicate products and merge color-specific products into one family.

The crawler can return one Shopify product per color. After the normal SKU
dedupe, rows whose name looks like ``Product - Color`` are rebuilt as one
variable parent with color added as an attribute.
"""

import re

import pandas as pd

from config import Tool


input_file = Tool.File.path_add_site(r"res/result.csv")
sku_dedup_file = Tool.File.path_add_site(r"fwq/quchong_sku.csv")
output_file = Tool.File.path_add_site(r"fwq/quchong.csv")

COLOR_SEPARATOR = re.compile(r"\s+-\s+")


def merge_categories(group):
    """Return the first row, with all Categories values merged in order."""
    result = group.iloc[0:1].copy()
    if "Categories" not in group.columns:
        return result

    categories = []
    seen = set()
    for value in group["Categories"]:
        if pd.isna(value):
            continue
        for category in str(value).split(","):
            category = category.strip()
            if category and category not in seen:
                seen.add(category)
                categories.append(category)
    result["Categories"] = ",".join(categories)
    return result


def deduplicate_by_sku(df):
    """Deduplicate SKU rows while retaining the first-seen row order."""
    if "SKU" not in df.columns:
        raise KeyError(f"CSV 文件缺少必要列 SKU，实际列名: {df.columns.tolist()}")

    working = df.copy()
    working["SKU"] = working["SKU"].fillna("").astype(str)
    working["_original_order"] = range(len(working))

    rows = []
    for _, group in working.groupby("SKU", sort=False, dropna=False):
        row = merge_categories(group).iloc[0].to_dict()
        row["_original_order"] = int(group["_original_order"].min())
        rows.append(row)

    result = pd.DataFrame(rows)
    if result.empty:
        return working.drop(columns=["_original_order"])
    return result.sort_values("_original_order", kind="stable").drop(
        columns=["_original_order"]
    ).reset_index(drop=True)


def split_product_color(value):
    """Split the first ``Product - Color`` separator, if present."""
    text = "" if pd.isna(value) else str(value).strip()
    match = COLOR_SEPARATOR.search(text)
    if not match:
        return text, ""
    product = text[: match.start()].strip()
    color = text[match.end() :].strip()
    return (product, color) if product and color else (text, "")


def _unique_join(values, separator=","):
    result = []
    seen = set()
    for value in values:
        if pd.isna(value):
            continue
        for item in str(value).split(separator):
            item = item.strip()
            if item and item not in seen:
                seen.add(item)
                result.append(item)
    return separator.join(result)


def _attribute_slot(row):
    """Find an existing color attribute or the first unused attribute slot."""
    for i in range(1, 6):
        name = str(row.get(f"Attribute {i} name", "")).strip().lower()
        if name in {"color", "colour"}:
            return i
    for i in range(1, 6):
        if not str(row.get(f"Attribute {i} name", "")).strip():
            return i
    return 2


def merge_color_products(df):
    """Merge color-specific product families and rebuild parent/child rows."""
    if "Name" not in df.columns or "Type" not in df.columns:
        return df

    working = df.copy()
    working["Type"] = working["Type"].fillna("").astype(str)
    working["Name"] = working["Name"].fillna("").astype(str)
    working["_source_order"] = range(len(working))
    parsed = working["Name"].map(split_product_color)
    working["_base_name"] = parsed.map(lambda item: item[0])
    working["_color"] = parsed.map(lambda item: item[1])

    generated = []
    consumed = set()

    # Products without the separator remain untouched.
    color_rows = working[working["_color"] != ""]
    for base_name, group in color_rows.groupby("_base_name", sort=False):
        colors = list(dict.fromkeys(group["_color"].tolist()))

        indices = group.index.tolist()
        parent_rows = group[group["Type"].str.lower() == "variable"]
        template = (parent_rows.iloc[0] if not parent_rows.empty else group.iloc[0]).copy()
        parent_sku = str(template.get("SKU", "")).strip()
        if not parent_sku:
            parent_sku = re.sub(r"[^a-z0-9]+", "-", base_name.lower()).strip("-")
        slot = _attribute_slot(template)
        color_name_col = f"Attribute {slot} name"
        color_value_col = f"Attribute {slot} value(s)"

        parent = template.copy()
        parent["Type"] = "variable"
        parent["SKU"] = parent_sku
        parent["Parent"] = ""
        parent["Name"] = base_name
        parent[color_name_col] = "Color"
        parent[color_value_col] = _unique_join(colors)
        if "Images" in group.columns:
            parent["Images"] = _unique_join(group["Images"])
        if "Categories" in group.columns:
            parent["Categories"] = _unique_join(group["Categories"])
        parent["_source_order"] = int(group["_source_order"].min()) - 0.5
        generated.append(parent.to_dict())

        # Existing variation rows become children of the first product's
        # parent. A color-only simple row is also converted into a child.
        children = group[group["Type"].str.lower().isin({"variation", "simple"})]
        for _, source in children.iterrows():
            child = source.copy()
            child["Type"] = "variation"
            child["Parent"] = parent_sku
            child["Name"] = base_name
            child[color_name_col] = "Color"
            child[color_value_col] = source["_color"]
            if "Description" in child.index:
                child["Description"] = ""
            generated.append(child.to_dict())

        consumed.update(indices)

    # Restore untouched rows and generated families to their original order.
    for index, row in working.iterrows():
        if index not in consumed:
            generated.append(row.to_dict())

    result = pd.DataFrame(generated).sort_values("_source_order", kind="stable")
    return result.drop(
        columns=["_source_order", "_base_name", "_color"], errors="ignore"
    ).reset_index(drop=True)


def main():
    print(f"读取原始 CSV: {input_file}")
    raw = pd.read_csv(input_file, dtype=str, keep_default_na=False)

    print("按 SKU 首次去重...")
    sku_deduplicated = deduplicate_by_sku(raw)
    sku_deduplicated.to_csv(sku_dedup_file, index=False, encoding="utf-8-sig")

    # Reload the intermediate file so this stage can be inspected independently.
    deduped = pd.read_csv(sku_dedup_file, dtype=str, keep_default_na=False)
    print("按 Name 合并颜色并重建父子商品...")
    color_merged = merge_color_products(deduped)

    print("对重建后的父子商品再次按 SKU 去重...")
    final = deduplicate_by_sku(color_merged)
    final.to_csv(output_file, index=False, encoding="utf-8-sig")
    Tool.print(f"去重及颜色变体合并完成，已保存到 {output_file}", color="green")
    return final


if __name__ == "__main__":
    main()
