"""Merge MaryRuth linked-product swatches into WooCommerce variation families."""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict

import pandas as pd

from config import Tool


class MaryRuthLinkedVariantMerge:
    """Merge product URLs connected by the PDP's Flavor/Size swatches."""

    metadata_columns = (
        '__linked_handles',
        '__linked_options',
        '__linked_target_options',
    )
    max_attributes = 4

    def __init__(self, tool, input_file, output_file):
        self.tool = tool
        self.input_file = input_file
        self.output_file = output_file

    @staticmethod
    def text(value) -> str:
        if value is None:
            return ''
        return str(value).strip()

    @classmethod
    def merge_categories(cls, values) -> str:
        """Keep hierarchy commas intact; separate multiple category paths with `` | ``."""
        result = []
        seen = set()
        for value in values:
            for category in cls.text(value).split(' | '):
                category = category.strip()
                if category and category not in seen:
                    seen.add(category)
                    result.append(category)
        return ' | '.join(result)

    @classmethod
    def merge_images(cls, values, separator: str) -> str:
        result = []
        seen = set()
        for value in values:
            for image in cls.text(value).split(separator):
                image = image.strip()
                if image and image not in seen:
                    seen.add(image)
                    result.append(image)
        return separator.join(result)

    @classmethod
    def json_list(cls, value) -> list[str]:
        try:
            decoded = json.loads(cls.text(value))
        except (TypeError, ValueError):
            return []
        if not isinstance(decoded, list):
            return []
        return [cls.text(item) for item in decoded if cls.text(item)]

    @classmethod
    def json_dict(cls, value) -> OrderedDict[str, str]:
        try:
            decoded = json.loads(cls.text(value))
        except (TypeError, ValueError):
            return OrderedDict()
        if not isinstance(decoded, dict):
            return OrderedDict()
        return OrderedDict(
            (cls.text(name), cls.text(option_value))
            for name, option_value in decoded.items()
            if cls.text(name) and cls.text(option_value)
        )

    @classmethod
    def json_option_mapping(cls, value) -> dict[str, OrderedDict[str, str]]:
        try:
            decoded = json.loads(cls.text(value))
        except (TypeError, ValueError):
            return {}
        if not isinstance(decoded, dict):
            return {}
        return {
            cls.text(handle): cls.json_dict(json.dumps(options, ensure_ascii=False))
            for handle, options in decoded.items()
            if cls.text(handle) and isinstance(options, dict)
        }

    @staticmethod
    def is_type(row, expected: str) -> bool:
        return str(row.get('Type', '')).strip().casefold() == expected

    def ensure_attribute_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.copy()
        for index in range(1, self.max_attributes + 1):
            for suffix in ('name', 'value(s)', 'visible', 'global'):
                column = f'Attribute {index} {suffix}'
                if column not in data.columns:
                    data[column] = ''
        return data

    def attributes(self, row: pd.Series) -> OrderedDict[str, str]:
        values = OrderedDict()
        for index in range(1, self.max_attributes + 1):
            name = self.text(row.get(f'Attribute {index} name', ''))
            value = self.text(row.get(f'Attribute {index} value(s)', ''))
            if not name or not value or name.casefold() == 'title':
                continue
            values.setdefault(name, value)
        return values

    def set_attributes(self, row: pd.Series, option_names: list[str], values: dict[str, str]):
        for index in range(1, self.max_attributes + 1):
            name_column = f'Attribute {index} name'
            value_column = f'Attribute {index} value(s)'
            visible_column = f'Attribute {index} visible'
            global_column = f'Attribute {index} global'
            if index <= len(option_names):
                name = option_names[index - 1]
                row[name_column] = name
                row[value_column] = values.get(name, '')
                row[visible_column] = 0
                row[global_column] = 1
            else:
                row[name_column] = ''
                row[value_column] = ''
                row[visible_column] = ''
                row[global_column] = ''

    def source_families(self, data: pd.DataFrame):
        """Collapse category duplicates while retaining source-product family order."""
        families = OrderedDict()
        variations_by_parent = OrderedDict()

        for _, row in data.iterrows():
            if not self.is_type(row, 'variation'):
                continue
            parent_sku = self.text(row.get('Parent', ''))
            if parent_sku:
                variations_by_parent.setdefault(parent_sku, []).append(row.copy())

        for _, row in data.iterrows():
            if not self.is_type(row, 'variable'):
                continue
            sku = self.text(row.get('SKU', ''))
            if not sku:
                continue
            if sku not in families:
                families[sku] = {
                    'parent': row.copy(),
                    'categories': [row.get('Categories', '')],
                    'children': OrderedDict(),
                    'linked_handles': self.json_list(row.get('__linked_handles', '')),
                    'linked_options': self.json_dict(row.get('__linked_options', '')),
                    'linked_target_options': self.json_option_mapping(
                        row.get('__linked_target_options', '')
                    ),
                }
            else:
                families[sku]['categories'].append(row.get('Categories', ''))

        for sku, family in families.items():
            for child in variations_by_parent.get(sku, []):
                child_sku = self.text(child.get('SKU', ''))
                identity = child_sku or hashlib.sha1(
                    '|'.join(
                        self.text(child.get(column, ''))
                        for column in ('Name', 'Sale price', 'Images')
                    ).encode('utf-8')
                ).hexdigest()
                if identity not in family['children']:
                    family['children'][identity] = child.copy()
                family['categories'].append(child.get('Categories', ''))

            categories = self.merge_categories(family['categories'])
            family['parent']['Categories'] = categories
            for child in family['children'].values():
                child['Categories'] = categories
        return families

    @staticmethod
    def component_key(handles: list[str]) -> str:
        digest = hashlib.sha1('|'.join(sorted(handles)).encode('utf-8')).hexdigest()[:12]
        return f'linked-family-{digest}'

    def linked_components(self, families):
        parent = {sku: sku for sku in families}

        def find(value):
            while parent[value] != value:
                parent[value] = parent[parent[value]]
                value = parent[value]
            return value

        def union(left, right):
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parent[right_root] = left_root

        missing_links = {}
        for sku, family in families.items():
            for linked_sku in family['linked_handles']:
                if linked_sku in parent:
                    union(sku, linked_sku)
                else:
                    missing_links.setdefault(sku, set()).add(linked_sku)

        components = OrderedDict()
        for sku in families:
            components.setdefault(find(sku), []).append(sku)

        valid_components = OrderedDict()
        skipped_components = 0
        for root, skus in components.items():
            if len(skus) == 1:
                continue
            if any(missing_links.get(sku) for sku in skus):
                skipped_components += 1
                continue
            valid_components[root] = skus
        return valid_components, skipped_components

    def family_name(self, candidates) -> str:
        names = []
        option_values = []
        for family in candidates:
            names.append(self.text(family['parent'].get('Name', '')))
            option_values.extend(family['linked_options'].values())

        normalized = []
        for name in names:
            candidate = name
            for value in sorted(set(option_values), key=len, reverse=True):
                escaped = re.escape(value)
                candidate = re.sub(
                    rf'\s*\(\s*{escaped}\s*\)|\s*[-|:]\s*{escaped}$',
                    '',
                    candidate,
                    flags=re.IGNORECASE,
                ).strip()
            normalized.append(candidate or name)
        return max(OrderedDict.fromkeys(normalized), key=normalized.count)

    @staticmethod
    def parent_only_columns(columns) -> list[str]:
        fixed = {'Description', 'Tags'}
        return [
            column for column in columns
            if column in fixed or '(product.metafields.' in column
        ]

    @staticmethod
    def resolved_options(candidates) -> dict[str, OrderedDict[str, str]]:
        """Resolve each linked page's options from direct and target observations."""
        values_by_handle = {
            str(family['parent'].get('SKU', '')).strip(): OrderedDict(
                family['linked_options']
            )
            for family in candidates
        }
        observations = {
            handle: {} for handle in values_by_handle
        }
        for family in candidates:
            for target, option_values in family['linked_target_options'].items():
                if target not in observations:
                    continue
                for name, value in option_values.items():
                    if value:
                        observations[target].setdefault(name, set()).add(value)

        for handle, values in values_by_handle.items():
            for name, observed in observations[handle].items():
                if name not in values and len(observed) == 1:
                    values[name] = next(iter(observed))
        return values_by_handle

    def merge_component(self, candidates, columns) -> list[pd.Series]:
        component_skus = [self.text(family['parent'].get('SKU', '')) for family in candidates]
        parent_sku = self.component_key(component_skus)
        parent = candidates[0]['parent'].copy()
        option_names = []
        for family in candidates:
            for name in family['linked_options']:
                if name not in option_names:
                    option_names.append(name)
            for child in family['children'].values():
                for name in self.attributes(child):
                    if name not in option_names:
                        option_names.append(name)
        if len(option_names) > self.max_attributes:
            raise ValueError(
                f'{self.family_name(candidates)!r} has more than {self.max_attributes} options'
            )

        parent['Type'] = 'variable'
        parent['SKU'] = parent_sku
        parent['Name'] = self.family_name(candidates)
        parent['Parent'] = ''
        parent['Categories'] = self.merge_categories(
            family['parent'].get('Categories', '') for family in candidates
        )
        image_separator = self.tool.config.images_split or ','
        parent['Images'] = self.merge_images(
            [family['parent'].get('Images', '') for family in candidates]
            + [child.get('Images', '') for family in candidates for child in family['children'].values()],
            image_separator,
        )

        parent_values = OrderedDict((name, []) for name in option_names)
        linked_values_by_sku = self.resolved_options(candidates)
        rows = []
        for family in candidates:
            family_sku = self.text(family['parent'].get('SKU', ''))
            linked_values = dict(linked_values_by_sku[family_sku])
            for child in family['children'].values():
                values = dict(linked_values)
                values.update(self.attributes(child))
                for name, value in values.items():
                    if name in parent_values and value and value not in parent_values[name]:
                        parent_values[name].append(value)

                variation = child.copy()
                variation['Type'] = 'variation'
                variation['Name'] = parent['Name']
                variation['Parent'] = parent_sku
                variation['Categories'] = parent['Categories']
                if not self.text(variation.get('Images', '')):
                    variation['Images'] = family['parent'].get('Images', '')
                self.set_attributes(variation, option_names, values)
                for column in self.parent_only_columns(columns):
                    variation[column] = ''
                rows.append(variation)

        self.set_attributes(
            parent,
            option_names,
            {name: ','.join(values) for name, values in parent_values.items()},
        )
        return [parent, *rows]

    def without_metadata(self, row: pd.Series) -> pd.Series:
        row = row.copy()
        for column in self.metadata_columns:
            if column in row.index:
                row = row.drop(labels=column)
        return row

    def run(self):
        data = self.tool.File.read_csv(
            path=self.input_file,
            dtype=str,
            keep_default_na=False,
        ).fillna('')
        required = {'Type', 'SKU', 'Name', 'Parent', 'Categories', 'Images'}
        missing = required.difference(data.columns)
        if missing:
            raise ValueError(f'Missing required columns: {sorted(missing)}')
        if any(column not in data.columns for column in self.metadata_columns):
            raise ValueError(
                'A_3 output lacks linked-product metadata. Rerun A_3_获取产品数据.py '
                'with the linked-variants cache namespace before running A_3_5.'
            )

        data = self.ensure_attribute_columns(data)
        columns = list(data.columns)
        families = self.source_families(data)
        components, skipped_components = self.linked_components(families)
        component_by_sku = {
            sku: root for root, skus in components.items() for sku in skus
        }

        output_rows = []
        emitted_components = set()
        for sku, family in families.items():
            component = component_by_sku.get(sku)
            if component is None:
                output_rows.append(self.without_metadata(family['parent']))
                output_rows.extend(self.without_metadata(child) for child in family['children'].values())
                continue
            if component in emitted_components:
                continue
            candidates = [families[candidate_sku] for candidate_sku in components[component]]
            output_rows.extend(
                self.without_metadata(row) for row in self.merge_component(candidates, columns)
            )
            emitted_components.add(component)

        family_skus = set(families)
        orphan_rows = data[
            ~data['Type'].str.casefold().isin({'variable', 'variation'})
            | (
                data['Type'].str.casefold().eq('variation')
                & ~data['Parent'].map(self.text).isin(family_skus)
            )
        ]
        output_rows.extend(self.without_metadata(row) for _, row in orphan_rows.iterrows())

        output = pd.DataFrame(output_rows)
        output = output.reindex(columns=[column for column in columns if column not in self.metadata_columns])
        self.tool.File.save_csv(output.to_dict('records'), self.output_file)
        self.tool.print(
            f'合并 {len(components)} 个拆分链接变体家族；'
            f'因缺少关联链接跳过 {skipped_components} 个家族。',
            color='green',
        )
        return output


if __name__ == '__main__':
    MaryRuthLinkedVariantMerge(
        Tool,
        Tool.File.path_add_site('res/result.csv'),
        Tool.File.path_add_site('fwq/merged_link_variants.csv'),
    ).run()
