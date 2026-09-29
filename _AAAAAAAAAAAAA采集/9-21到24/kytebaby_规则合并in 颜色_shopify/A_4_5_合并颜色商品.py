"""Merge Kyte Baby's color-split Shopify product families without refetching."""

from __future__ import annotations

import hashlib
from collections import OrderedDict, defaultdict

import pandas as pd

from config import Tool


class ColorFamilyMerger:
    max_attributes = 3

    def __init__(self, tool, input_path, output_path):
        self.tool = tool
        self.input_path = input_path
        self.output_path = output_path

    @staticmethod
    def text(value) -> str:
        return str(value or '').strip()

    @staticmethod
    def parent_sku(name: str) -> str:
        digest = hashlib.sha1(name.casefold().encode('utf-8')).hexdigest()[:12]
        return f'color-family-{digest}'

    def attributes(self, row) -> OrderedDict[str, str]:
        result = OrderedDict()
        for index in range(1, self.max_attributes + 1):
            name = self.text(row.get(f'Attribute {index} name', ''))
            value = self.text(row.get(f'Attribute {index} value(s)', ''))
            key = name.casefold()
            if name and key not in result:
                result[name] = value
        return result

    @staticmethod
    def append_unique(target: list[str], value: str):
        value = str(value or '').strip()
        if value and value not in target:
            target.append(value)

    def merge_categories(self, rows) -> str:
        values = []
        for row in rows:
            for category in self.text(row.get('Categories', '')).split(','):
                self.append_unique(values, category)
        return ','.join(values)

    def merge_images(self, rows) -> str:
        separator = self.tool.config.images_split or ','
        values = []
        for row in rows:
            for image in self.text(row.get('Images', '')).split(separator):
                self.append_unique(values, image)
        return separator.join(values)

    def color_base_name(self, row) -> tuple[str, str] | None:
        attributes = self.attributes(row)
        color_name = next((name for name in attributes if name.casefold() == 'color'), '')
        color = attributes.get(color_name, '')
        title = self.text(row.get('Name', ''))
        if not color or ',' in color:
            return None
        marker = f' in {color}'
        position = title.casefold().find(marker.casefold())
        if position < 1:
            return None
        base_name = (title[:position] + title[position + len(marker):]).strip()
        return (base_name, color) if base_name else None

    def valid_color_family(self, parent, children) -> tuple[str, str] | None:
        title_data = self.color_base_name(parent)
        if not title_data or not children:
            return None
        base_name, color = title_data
        for child in children:
            attributes = self.attributes(child)
            child_color = next(
                (value for name, value in attributes.items() if name.casefold() == 'color'), ''
            )
            if child_color.casefold() != color.casefold():
                return None
        return base_name, color

    def option_names(self, candidates) -> list[str]:
        names = []
        seen = set()
        for parent, children, _ in candidates:
            for row in [parent, *children]:
                for name in self.attributes(row):
                    key = name.casefold()
                    if key not in seen:
                        seen.add(key)
                        names.append(name)
        color_index = next((index for index, name in enumerate(names) if name.casefold() == 'color'), None)
        if color_index is None:
            raise ValueError('Merged family is missing its Color attribute')
        names.insert(0, names.pop(color_index))
        if len(names) > self.max_attributes:
            raise ValueError(f'Merged family has more than {self.max_attributes} attributes: {names}')
        return names

    def set_attributes(self, row, names: list[str], values: dict[str, str]):
        lookup = {name.casefold(): value for name, value in values.items()}
        for index in range(1, self.max_attributes + 1):
            columns = (
                f'Attribute {index} name',
                f'Attribute {index} value(s)',
                f'Attribute {index} visible',
                f'Attribute {index} global',
            )
            if index <= len(names):
                name = names[index - 1]
                row[columns[0]] = name
                row[columns[1]] = lookup.get(name.casefold(), '')
                row[columns[2]] = '0'
                row[columns[3]] = '1'
            else:
                for column in columns:
                    if column in row.index:
                        row[column] = ''

    def merge_family(self, candidates) -> list[pd.Series]:
        base_name = candidates[0][2][0]
        names = self.option_names(candidates)
        parent = candidates[0][0].copy()
        parent_sku = self.parent_sku(base_name)
        all_rows = [row for source_parent, children, _ in candidates for row in [source_parent, *children]]

        parent['Type'] = 'variable'
        parent['SKU'] = parent_sku
        parent['Name'] = base_name
        parent['Parent'] = ''
        parent['Categories'] = self.merge_categories(all_rows)
        parent['Images'] = self.merge_images(all_rows)

        attribute_values = OrderedDict((name, []) for name in names)
        variations = []
        for source_parent, children, (_, color) in candidates:
            for child in children:
                variation = child.copy()
                values = self.attributes(variation)
                values[next(name for name in names if name.casefold() == 'color')] = color
                for name, value in values.items():
                    target_name = next((item for item in names if item.casefold() == name.casefold()), '')
                    if target_name:
                        self.append_unique(attribute_values[target_name], value)
                variation['Type'] = 'variation'
                variation['Name'] = base_name
                variation['Parent'] = parent_sku
                variation['Categories'] = parent['Categories']
                self.set_attributes(variation, names, values)
                variations.append(variation)

        self.set_attributes(
            parent,
            names,
            {name: ','.join(values) for name, values in attribute_values.items()},
        )
        return [parent, *variations]

    def run(self):
        data = pd.read_csv(self.input_path, dtype=str, keep_default_na=False)
        required = {'Type', 'SKU', 'Name', 'Parent', 'Categories', 'Images'}
        missing = required.difference(data.columns)
        if missing:
            raise ValueError(f'Missing required columns: {sorted(missing)}')

        rows = [row.copy() for _, row in data.iterrows()]
        parents = OrderedDict(
            (self.text(row['SKU']), row)
            for row in rows
            if self.text(row.get('Type', '')).casefold() == 'variable'
        )
        children_by_parent = defaultdict(list)
        for row in rows:
            if self.text(row.get('Type', '')).casefold() == 'variation':
                children_by_parent[self.text(row.get('Parent', ''))].append(row)

        families = OrderedDict()
        for sku, parent in parents.items():
            children = children_by_parent.get(sku, [])
            family_data = self.valid_color_family(parent, children)
            if family_data:
                families[sku] = (parent, children, family_data)

        groups = OrderedDict()
        for sku, (_, _, (base_name, _)) in families.items():
            groups.setdefault(base_name, []).append(sku)
        merge_groups = {name: skus for name, skus in groups.items() if len(skus) > 1}
        merged_parent_skus = {sku for skus in merge_groups.values() for sku in skus}

        output_rows = []
        consumed_skus = set()
        emitted_groups = set()
        for row in rows:
            product_type = self.text(row.get('Type', '')).casefold()
            sku = self.text(row.get('SKU', ''))
            if product_type == 'variable' and sku in merged_parent_skus:
                base_name = families[sku][2][0]
                if base_name not in emitted_groups:
                    candidates = [families[item] for item in merge_groups[base_name]]
                    output_rows.extend(self.merge_family(candidates))
                    emitted_groups.add(base_name)
                    for source_parent, children, _ in candidates:
                        consumed_skus.add(self.text(source_parent['SKU']))
                        consumed_skus.update(self.text(child['SKU']) for child in children)
                continue
            if sku in consumed_skus:
                continue
            output_rows.append(row)

        output = pd.DataFrame(output_rows, columns=data.columns)
        self.tool.File.save_csv(output.to_dict('records'), self.output_path)
        self.tool.print(
            f'合并 {sum(len(skus) for skus in merge_groups.values())} 个颜色商品为 '
            f'{len(merge_groups)} 个变体家族，保存至 {self.output_path}',
            color='green',
        )
        return output


if __name__ == '__main__':
    ColorFamilyMerger(
        Tool,
        Tool.File.path_add_site('fwq/quchong.csv'),
        Tool.File.path_add_site('fwq/merged_color_variants.csv'),
    ).run()
