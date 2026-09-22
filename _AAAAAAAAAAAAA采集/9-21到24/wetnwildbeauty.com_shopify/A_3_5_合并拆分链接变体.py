"""Merge only the product families explicitly linked by King Linked Options."""

import hashlib
import json
from collections import OrderedDict

from config import Tool


class KingLinkedOptionsMerge:
    metadata = (
        '__source_handle',
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
        values = OrderedDict()
        for index in range(1, self.max_attributes + 1):
            name = self.text(row.get(f'Attribute {index} name'))
            value = self.text(row.get(f'Attribute {index} value(s)'))
            if name and value and name.casefold() != 'title':
                values.setdefault(name, value)
        return values

    def set_attributes(self, row, names, values):
        for index in range(1, self.max_attributes + 1):
            fields = [f'Attribute {index} {suffix}' for suffix in ('name', 'value(s)', 'visible', 'global')]
            if index <= len(names):
                row[fields[0]] = names[index - 1]
                row[fields[1]] = values.get(names[index - 1], '')
                row[fields[2]] = 0
                row[fields[3]] = 1
            else:
                for field in fields:
                    row[field] = ''

    def clean(self, row):
        return row.drop(labels=[column for column in self.metadata if column in row.index])

    def base_name(self, row, options):
        name = self.text(row.get('Name'))
        for value in options.values():
            suffix = f' | {value}'
            if name.endswith(suffix):
                return name[:-len(suffix)].strip()
        return name

    def run(self):
        data = self.tool.File.read_csv(
            path=self.input_file,
            dtype=str,
            keep_default_na=False,
        ).fillna('')
        missing = set(self.metadata).difference(data.columns)
        if missing:
            raise ValueError(f'Missing linked-options metadata: {sorted(missing)}')
        for index in range(1, self.max_attributes + 1):
            for suffix in ('name', 'value(s)', 'visible', 'global'):
                column = f'Attribute {index} {suffix}'
                if column not in data.columns:
                    data[column] = ''

        variations_by_parent = {}
        for _, row in data[data['Type'].str.casefold() == 'variation'].iterrows():
            variations_by_parent.setdefault(self.text(row.get('Parent')), []).append(row.copy())

        families = OrderedDict()
        parent_rows = data[data['Type'].str.casefold().isin({'variable', 'simple'})]
        for _, row in parent_rows.iterrows():
            handle = self.text(row.get('__source_handle'))
            if not handle:
                continue
            family = families.setdefault(handle, {
                'parent': row.copy(),
                'children': OrderedDict(),
                'links': [],
                'options': {},
                'targets': {},
                'categories': [],
            })
            family['categories'].append(row.get('Categories', ''))
            family['links'] = list(dict.fromkeys(
                family['links']
                + [self.text(value) for value in self.decode(row['__linked_handles'], list) if self.text(value)]
            ))
            family['options'].update({
                self.text(name): self.text(value)
                for name, value in self.decode(row['__linked_options'], dict).items()
                if self.text(name) and self.text(value)
            })
            family['targets'].update(self.decode(row['__linked_target_options'], dict))
            for child in variations_by_parent.get(self.text(row.get('SKU')), []):
                identity = self.text(child.get('SKU')) or hashlib.sha1(
                    repr(child.to_dict()).encode('utf-8')
                ).hexdigest()
                family['children'].setdefault(identity, child)

        parent_of = {handle: handle for handle in families}

        def find(handle):
            while parent_of[handle] != handle:
                parent_of[handle] = parent_of[parent_of[handle]]
                handle = parent_of[handle]
            return handle

        invalid = set()
        for handle, family in families.items():
            own_target = family['targets'].get(handle)
            if own_target and own_target != family['options']:
                invalid.add(handle)
            for linked in family['links']:
                if linked not in families:
                    invalid.add(handle)
                    continue
                left, right = find(handle), find(linked)
                if left != right:
                    parent_of[right] = left

        components = OrderedDict()
        for handle in families:
            components.setdefault(find(handle), []).append(handle)
        components = OrderedDict(
            (root, handles)
            for root, handles in components.items()
            if len(handles) > 1 and not any(handle in invalid for handle in handles)
        )
        component_for = {
            handle: root
            for root, handles in components.items()
            for handle in handles
        }

        output = []
        emitted = set()
        image_separator = self.tool.config.images_split or ','
        for handle, family in families.items():
            root = component_for.get(handle)
            if not root:
                output.append(self.clean(family['parent']))
                output.extend(self.clean(child) for child in family['children'].values())
                continue
            if root in emitted:
                continue

            emitted.add(root)
            members = [families[key] for key in components[root]]
            parent = members[0]['parent'].copy()
            parent_name = self.base_name(parent, members[0]['options'])
            parent_sku = 'king-linked-' + hashlib.sha1(
                '|'.join(sorted(components[root])).encode('utf-8')
            ).hexdigest()[:12]
            option_names = list(OrderedDict.fromkeys(
                name
                for member in members
                for name in [
                    *member['options'],
                    *(name for child in member['children'].values() for name in self.attributes(child)),
                ]
            ))
            if not option_names or len(option_names) > self.max_attributes:
                raise ValueError(f'{parent_name!r} has an invalid linked-option attribute set')

            parent['Type'] = 'variable'
            parent['SKU'] = parent_sku
            parent['Name'] = parent_name
            parent['Parent'] = ''
            parent['Categories'] = self.join_unique(
                (member['parent'].get('Categories', '') for member in members),
                ' | ',
            )
            parent['Images'] = self.join_unique(
                (
                    row.get('Images', '')
                    for member in members
                    for row in [member['parent'], *member['children'].values()]
                ),
                image_separator,
            )

            values_by_name = OrderedDict((name, []) for name in option_names)
            merged_children = []
            for member in members:
                for child in member['children'].values():
                    values = {**member['options'], **self.attributes(child)}
                    for name, value in values.items():
                        if name in values_by_name and value not in values_by_name[name]:
                            values_by_name[name].append(value)
                    child['Type'] = 'variation'
                    child['Name'] = parent_name
                    child['Parent'] = parent_sku
                    child['Categories'] = parent['Categories']
                    child['Description'] = ''
                    if not self.text(child.get('Images')):
                        child['Images'] = member['parent'].get('Images', '')
                    self.set_attributes(child, option_names, values)
                    merged_children.append(self.clean(child))

            self.set_attributes(
                parent,
                option_names,
                {name: ','.join(values) for name, values in values_by_name.items()},
            )
            output.append(self.clean(parent))
            output.extend(merged_children)

        columns = [column for column in data.columns if column not in self.metadata]
        self.tool.File.save_csv(
            [row.reindex(columns, fill_value='').to_dict() for row in output],
            self.output_file,
        )
        self.tool.print(
            f'合并 {len(components)} 个 King Linked Options 变体家族。',
            color='green',
        )


if __name__ == '__main__':
    KingLinkedOptionsMerge(
        Tool,
        Tool.File.path_add_site('res/result.csv'),
        Tool.File.path_add_site('fwq/merged_link_variants.csv'),
    ).run()
    Tool.close()
