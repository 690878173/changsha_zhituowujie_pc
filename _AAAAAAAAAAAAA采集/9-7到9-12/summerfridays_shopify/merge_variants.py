"""合并 summerfridays 以独立链接发布的变体。

该站把同一个可售选项拆成多个独立产品链接：标题形如
``Lip Butter Balm Pink Sugar``，尾部的 ``Pink Sugar`` 正是该产品自身的
``Shade`` 选项值，而不是共享类默认的 ``Name | Variant`` 写法。因此这里在读取
CSV 后按自身选项值建立「标题 -> (基础名, 后缀)」映射，其余家族合并逻辑沿用
``MergeLinkVariants``：合并 SKU 与分类、生成 ``variable`` 父行与 ``variation``
子行，已有原生选项时保留该选项（例如 ``Shade``），否则写入 ``Variant`` 选项。
"""

from __future__ import annotations

import hashlib

import pandas as pd

from _ljp.mb.mg_shopify import MergeLinkVariants


class SummerFridaysMergeVariants(MergeLinkVariants):
    """把独立产品链接合并成变体家族，并保留每个变体的原始图片。"""

    def __init__(self, tool, input_file, output_file):
        super().__init__(tool, input_file, output_file)
        self._split_titles: dict[str, tuple[str, str]] = {}

    def run(self):
        data = pd.read_csv(self.input_file, dtype=str, keep_default_na=False)
        self._split_titles = {}
        for _, row in data.iterrows():
            if self._text(row.get('Type', '')).casefold() != 'variable':
                continue
            name = self._text(row.get('Name', ''))
            value = self._text(row.get('Attribute 1 value(s)', ''))
            option = self._text(row.get('Attribute 1 name', ''))
            if not name or not value or not option or option.casefold() == 'title':
                continue
            if not name.casefold().endswith(value.casefold()):
                continue
            base = name[: len(name) - len(value)].strip()
            if base:
                self._split_titles[name] = (base, value)
        return super().run()

    def _split_title(self, title: str) -> tuple[str, str]:
        text = self._text(title)
        if text in self._split_titles:
            return self._split_titles[text]
        return super()._split_title(text)

    def _dedupe_skus(self, data: pd.DataFrame) -> pd.DataFrame:
        """Deduplicate rows without discarding image URLs from later copies.

        Step4 can emit the same SKU once per category.  The shared merger keeps
        only the first row in that case, but Summer Fridays commonly has the
        useful image URLs on a later copy (or on a different source row).  Fold
        those URLs into the first row before applying the shared SKU logic.
        """
        data = data.copy()
        image_separator = self.tool.config.images_split or ","

        # Mirror the shared fallback-SKU rule so grouping below uses the same
        # identity as the parent implementation.
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
            row["Images"] = self._merge_images(group["Images"], image_separator)
            rows.append(row)
        return pd.DataFrame(rows, columns=data.columns)

    def _merge_family(self, candidates, image_separator: str) -> list[pd.Series]:
        rows = super()._merge_family(candidates, image_separator)

        # A split product's parent row carries the product/shade gallery while
        # its native Shopify variation often has no image field.  Keep an
        # explicitly supplied variation gallery, otherwise inherit that source
        # parent's gallery so every emitted variation retains its original
        # image links.
        output_index = 1
        for source_parent, children in candidates:
            parent_images = self._text(source_parent.get("Images", ""))
            for index in range(len(children)):
                variation = rows[output_index]
                if not self._text(variation.get("Images", "")) and parent_images:
                    variation["Images"] = parent_images
                output_index += 1
        return rows

    def _is_split_link(self, parent, children) -> bool:
        return (
            self._text(parent.get('Name', '')) in self._split_titles
            and not children.empty
        )


__all__ = ['SummerFridaysMergeVariants']
