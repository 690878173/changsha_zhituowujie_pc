"""Merge only PDP families connected by Quip's custom-swatch product links."""

import hashlib
import json
from collections import OrderedDict

import pandas as pd

from config import Tool


class QuipLinkedSwatchMerge:
    metadata = ('__source_handle', '__linked_handles', '__linked_options', '__linked_target_options')
    max_attributes = 4

    def __init__(self, tool, input_file, output_file):
        self.tool, self.input_file, self.output_file = tool, input_file, output_file

    @staticmethod
    def text(value):
        return '' if value is None else str(value).strip()

    @classmethod
    def decode(cls, value, expected):
        try:
            parsed = json.loads(cls.text(value))
        except (TypeError, ValueError):
            return expected()
        return parsed if isinstance(parsed, expected) else expected()

    @classmethod
    def join_unique(cls, values, separator):
        result = []
        for value in values:
            for part in cls.text(value).split(separator):
                part = part.strip()
                if part and part not in result:
                    result.append(part)
        return separator.join(result)

    def attributes(self, row):
        return OrderedDict(
            (self.text(row.get(f'Attribute {index} name')),
             self.text(row.get(f'Attribute {index} value(s)')))
            for index in range(1, self.max_attributes + 1)
            if self.text(row.get(f'Attribute {index} name')).casefold() != 'title'
            and self.text(row.get(f'Attribute {index} name'))
            and self.text(row.get(f'Attribute {index} value(s)'))
        )

    def set_attributes(self, row, names, values):
        for index in range(1, self.max_attributes + 1):
            fields = [f'Attribute {index} {suffix}' for suffix in ('name', 'value(s)', 'visible', 'global')]
            if index <= len(names):
                row[fields[0]], row[fields[1]], row[fields[2]], row[fields[3]] = names[index - 1], values.get(names[index - 1], ''), 0, 1
            else:
                for field in fields:
                    row[field] = ''

    def clean(self, row):
        return row.drop(labels=[column for column in self.metadata if column in row.index])

    def run(self):
        data = self.tool.File.read_csv(path=self.input_file, dtype=str, keep_default_na=False).fillna('')
        missing = set(self.metadata).difference(data.columns)
        if missing:
            raise ValueError(f'Missing linked-swatch metadata: {sorted(missing)}')
        for index in range(1, self.max_attributes + 1):
            for suffix in ('name', 'value(s)', 'visible', 'global'):
                column = f'Attribute {index} {suffix}'
                if column not in data:
                    data[column] = ''
        variation_rows = {}
        for _, row in data[data['Type'].str.casefold() == 'variation'].iterrows():
            variation_rows.setdefault(self.text(row['Parent']), []).append(row.copy())
        families = OrderedDict()
        for _, row in data[data['Type'].str.casefold().isin({'variable', 'simple'})].iterrows():
            handle = self.text(row.get('__source_handle'))
            if not handle:
                continue
            family = families.setdefault(handle, {'parent': row.copy(), 'children': [], 'links': [], 'options': {}, 'categories': []})
            family['categories'].append(row['Categories'])
            family['links'] = list(dict.fromkeys(family['links'] + [self.text(x) for x in self.decode(row['__linked_handles'], list) if self.text(x)]))
            family['options'].update({self.text(k): self.text(v) for k, v in self.decode(row['__linked_options'], dict).items() if self.text(k) and self.text(v)})
            family['children'].extend(variation_rows.get(self.text(row['SKU']), []))
        for family in families.values():
            children = OrderedDict()
            for child in family['children']:
                identity = self.text(child.get('SKU')) or hashlib.sha1(repr(child.to_dict()).encode()).hexdigest()
                children.setdefault(identity, child)
            family['children'] = list(children.values())
        parent_of = {handle: handle for handle in families}
        def find(handle):
            while parent_of[handle] != handle:
                parent_of[handle] = parent_of[parent_of[handle]]; handle = parent_of[handle]
            return handle
        invalid = set()
        for handle, family in families.items():
            for linked in family['links']:
                if linked not in families: invalid.add(handle); continue
                left, right = find(handle), find(linked)
                if left != right: parent_of[right] = left
        components = OrderedDict()
        for handle in families: components.setdefault(find(handle), []).append(handle)
        components = OrderedDict((root, handles) for root, handles in components.items() if len(handles) > 1 and not any(handle in invalid for handle in handles))
        component_for = {handle: root for root, handles in components.items() for handle in handles}
        output, emitted = [], set()
        for handle, family in families.items():
            root = component_for.get(handle)
            if not root:
                output.append(self.clean(family['parent'])); output.extend(self.clean(row) for row in family['children']); continue
            if root in emitted: continue
            emitted.add(root); members = [families[key] for key in components[root]]; parent = members[0]['parent'].copy()
            parent_sku = 'linked-swatch-' + hashlib.sha1('|'.join(sorted(components[root])).encode()).hexdigest()[:12]
            names = list(OrderedDict.fromkeys(name for member in members for name in [*member['options'], *(key for child in member['children'] for key in self.attributes(child))]))
            if len(names) > self.max_attributes: raise ValueError(f'{parent["Name"]!r} has more than {self.max_attributes} options')
            parent['Type'], parent['SKU'], parent['Parent'] = 'variable', parent_sku, ''
            parent['Categories'] = self.join_unique((member['parent']['Categories'] for member in members), ' | ')
            sep = self.tool.config.images_split or ','
            parent['Images'] = self.join_unique((row['Images'] for member in members for row in [member['parent'], *member['children']]), sep)
            values_by_name = OrderedDict((name, []) for name in names)
            output.append(self.clean(parent))
            for member in members:
                for child in member['children']:
                    values = {**member['options'], **self.attributes(child)}
                    for name, value in values.items():
                        if name in values_by_name and value not in values_by_name[name]: values_by_name[name].append(value)
                    child['Type'], child['Name'], child['Parent'], child['Categories'], child['Description'] = 'variation', parent['Name'], parent_sku, parent['Categories'], ''
                    if not self.text(child['Images']): child['Images'] = member['parent']['Images']
                    self.set_attributes(child, names, values); output.append(self.clean(child))
            self.set_attributes(parent, names, {name: ','.join(values) for name, values in values_by_name.items()})
            output[-len([row for member in members for row in member['children']]) - 1] = self.clean(parent)
        columns = [column for column in data.columns if column not in self.metadata]
        self.tool.File.save_csv([row.reindex(columns, fill_value='').to_dict() for row in output], self.output_file)
        self.tool.print(f'合并 {len(components)} 个 data-product 色板变体家族。', color='green')


if __name__ == '__main__':
    QuipLinkedSwatchMerge(Tool, Tool.File.path_add_site('res/result.csv'), Tool.File.path_add_site('fwq/merged_link_variants.csv')).run()
    Tool.close()
