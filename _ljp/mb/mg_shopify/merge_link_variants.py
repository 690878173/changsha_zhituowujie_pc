"""Merge magic-Shopify products whose variant selection is split by URL."""

from __future__ import annotations

import hashlib
from collections import OrderedDict

import pandas as pd


class MergeLinkVariants:
    """Merge ``Product | Variant`` URL products into WooCommerce families.

    Some Hydrogen storefronts publish every color or style as a separate
    product URL, while other options such as size remain normal Shopify
    variants. The merger first deduplicates source SKU rows and categories,
    then merges only title-prefix groups with at least two URL products.
    """

    title_separator = " | "
    fallback_option_name = "Variant"
    max_attributes = 4

    def __init__(self, tool, input_file, output_file):
        self.tool = tool
        self.input_file = input_file
        self.output_file = output_file

    @staticmethod
    def _text(value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @classmethod
    def _merge_categories(cls, values) -> str:
        result = []
        seen = set()
        for value in values:
            for category in cls._text(value).split(","):
                category = category.strip()
                if category and category not in seen:
                    seen.add(category)
                    result.append(category)
        return ",".join(result)

    @classmethod
    def _merge_images(cls, values, separator: str) -> str:
        result = []
        seen = set()
        for value in values:
            for image in cls._text(value).split(separator):
                image = image.strip()
                if image and image not in seen:
                    seen.add(image)
                    result.append(image)
        return separator.join(result)

    @classmethod
    def _split_title(cls, title: str) -> tuple[str, str]:
        name, variant = cls._text(title).split(cls.title_separator, 1)
        return name.strip(), variant.strip()

    @staticmethod
    def _parent_sku(name: str) -> str:
        digest = hashlib.sha1(name.casefold().encode("utf-8")).hexdigest()[:12]
        return f"split-family-{digest}"

    def _attribute_map(self, row: pd.Series) -> OrderedDict[str, str]:
        attributes = OrderedDict()
        for index in range(1, self.max_attributes + 1):
            name = self._text(row.get(f"Attribute {index} name", ""))
            value = self._text(row.get(f"Attribute {index} value(s)", ""))
            if name and name.casefold() != "title" and name not in attributes:
                attributes[name] = value
        return attributes

    def _dedupe_skus(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        # Older A_3 caches may contain Storefront variants with an empty
        # merchant SKU.  An empty string cannot be a global dedupe key: it
        # would merge unrelated variants into one row.  Build a deterministic
        # fallback from the parent and exported variation identity instead.
        parent_skus = {
            self._text(row["SKU"])
            for _, row in data[data["Type"].str.casefold() == "variable"].iterrows()
        }
        for index, row in data.iterrows():
            is_variation = self._text(row.get("Type", "")).casefold() == "variation"
            sku = self._text(row.get("SKU", ""))
            if sku and not (is_variation and sku in parent_skus):
                continue
            identity = "\x1f".join(
                self._text(row.get(column, ""))
                for column in (
                    "Parent", "Name", "Attribute 1 value(s)",
                    "Attribute 2 value(s)", "Attribute 3 value(s)",
                    "Attribute 4 value(s)", "Sale price", "Images",
                )
            )
            digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:16]
            data.at[index, "SKU"] = f"missing-sku-{digest}"
        rows = []
        for _, group in data.groupby("SKU", sort=False, dropna=False):
            row = group.iloc[0].copy()
            row["Categories"] = self._merge_categories(group["Categories"])
            rows.append(row)
        return pd.DataFrame(rows, columns=data.columns)

    def _families(self, data: pd.DataFrame):
        families = OrderedDict()
        variations = data[data["Type"].str.casefold() == "variation"]
        for _, parent in data[data["Type"].str.casefold() == "variable"].iterrows():
            parent_sku = self._text(parent["SKU"])
            children = variations[
                variations["Parent"].map(self._text) == parent_sku
            ].copy()
            families[parent_sku] = (parent, children)
        return families

    def _is_split_link(self, parent: pd.Series, children: pd.DataFrame) -> bool:
        return self.title_separator in self._text(parent.get("Name", "")) and not children.empty

    def _native_option_names(self, candidates) -> list[str]:
        names = []
        seen = set()
        for parent, children in candidates:
            for row in [parent, *(children.iloc[index] for index in range(len(children)))]:
                for name in self._attribute_map(row):
                    if name not in seen:
                        seen.add(name)
                        names.append(name)
        return names

    def _title_option_name(self, candidates, native_names: list[str]) -> str:
        """Reuse an existing option when all child values equal the title suffix."""
        for option_name in native_names:
            matches = True
            for parent, children in candidates:
                _, title_value = self._split_title(parent["Name"])
                for index in range(len(children)):
                    child_value = self._attribute_map(children.iloc[index]).get(option_name, "")
                    if child_value.casefold() != title_value.casefold():
                        matches = False
                        break
                if not matches:
                    break
            if matches:
                return option_name
        return ""

    def _set_attributes(self, row: pd.Series, option_names: list[str], values: dict[str, str]):
        for index in range(1, self.max_attributes + 1):
            name_col = f"Attribute {index} name"
            value_col = f"Attribute {index} value(s)"
            visible_col = f"Attribute {index} visible"
            global_col = f"Attribute {index} global"
            if index <= len(option_names):
                option_name = option_names[index - 1]
                row[name_col] = option_name
                row[value_col] = values.get(option_name, "")
                row[visible_col] = 0
                row[global_col] = 1
            else:
                for column in (name_col, value_col, visible_col, global_col):
                    if column in row.index:
                        row[column] = ""

    def _merge_family(self, candidates, image_separator: str) -> list[pd.Series]:
        base_name, _ = self._split_title(candidates[0][0]["Name"])
        native_names = self._native_option_names(candidates)
        title_option_name = self._title_option_name(candidates, native_names)
        option_names = native_names if title_option_name else [self.fallback_option_name, *native_names]
        if len(option_names) > self.max_attributes:
            raise ValueError(f"{base_name!r} has more than {self.max_attributes} variant options")

        parent_sku = self._parent_sku(base_name)
        parent = candidates[0][0].copy()
        parent["Type"] = "variable"
        parent["SKU"] = parent_sku
        parent["Name"] = base_name
        parent["Parent"] = ""
        parent["Categories"] = self._merge_categories(
            item[0].get("Categories", "") for item in candidates
        )
        parent["Images"] = self._merge_images(
            [item[0].get("Images", "") for item in candidates]
            + [item[1].iloc[index].get("Images", "") for item in candidates for index in range(len(item[1]))],
            image_separator,
        )

        rows = []
        values_by_option = OrderedDict((name, []) for name in option_names)
        for source_parent, children in candidates:
            _, title_value = self._split_title(source_parent["Name"])
            for index in range(len(children)):
                variation = children.iloc[index].copy()
                values = dict(self._attribute_map(variation))
                if title_option_name:
                    values[title_option_name] = title_value
                else:
                    values[self.fallback_option_name] = title_value
                for option_name, value in values.items():
                    if option_name in values_by_option and value and value not in values_by_option[option_name]:
                        values_by_option[option_name].append(value)
                variation["Type"] = "variation"
                variation["Name"] = base_name
                variation["Parent"] = parent_sku
                variation["Categories"] = parent["Categories"]
                self._set_attributes(variation, option_names, values)
                rows.append(variation)

        self._set_attributes(
            parent,
            option_names,
            {name: ",".join(values) for name, values in values_by_option.items()},
        )
        return [parent, *rows]

    def run(self):
        data = pd.read_csv(self.input_file, dtype=str, keep_default_na=False)
        required = {"Type", "SKU", "Name", "Parent", "Categories", "Images"}
        missing = required.difference(data.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        data = self._dedupe_skus(data)
        families = self._families(data)
        split_groups = OrderedDict()
        for sku, (parent, children) in families.items():
            if self._is_split_link(parent, children):
                base_name, _ = self._split_title(parent["Name"])
                split_groups.setdefault(base_name, []).append(sku)
        merge_groups = {
            name: skus for name, skus in split_groups.items() if len(skus) > 1
        }
        merged_skus = {sku for skus in merge_groups.values() for sku in skus}
        image_separator = self.tool.config.images_split or ","

        output_rows = []
        consumed_skus = set()
        emitted_groups = set()
        for sku, (parent, children) in families.items():
            if sku in merged_skus:
                base_name, _ = self._split_title(parent["Name"])
                if base_name in emitted_groups:
                    continue
                candidates = [families[candidate_sku] for candidate_sku in merge_groups[base_name]]
                output_rows.extend(self._merge_family(candidates, image_separator))
                emitted_groups.add(base_name)
                for source_parent, source_children in candidates:
                    consumed_skus.add(self._text(source_parent["SKU"]))
                    consumed_skus.update(self._text(source_children.iloc[index]["SKU"]) for index in range(len(source_children)))
                continue
            output_rows.append(parent)
            consumed_skus.add(sku)
            for index in range(len(children)):
                output_rows.append(children.iloc[index])
                consumed_skus.add(self._text(children.iloc[index]["SKU"]))

        output_rows.extend(
            row for _, row in data.iterrows() if self._text(row["SKU"]) not in consumed_skus
        )
        output = pd.DataFrame(output_rows, columns=data.columns)
        self.tool.File.save_csv(output.to_dict("records"), self.output_file)

        merged_products = sum(len(skus) for skus in merge_groups.values())
        self.tool.print(
            f"SKU 去重后 {len(data)} 行；合并 {merged_products} 个拆分链接商品为 "
            f"{len(merge_groups)} 个变体家族。",
            color="green",
        )
        return output


__all__ = ["MergeLinkVariants"]
