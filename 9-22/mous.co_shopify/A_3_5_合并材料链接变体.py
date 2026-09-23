"""Merge only mutually declared Mous material PDP families."""

import hashlib
import json
from collections import OrderedDict

from config import Tool


class MousMaterialMerge:
    metadata_columns = (
        '__source_handle', '__linked_handles', '__linked_options',
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
            value = json.loads(cls.text(value))
        except (TypeError, ValueError):
            return expected()
        return value if isinstance(value, expected) else expected()

    @classmethod
    def join_unique(cls, values, separator):
        result = []
        for value in values:
            for item in cls.text(value).split(separator):
                item = item.strip()
                if item and item not in result:
                    result.append(item)
        return separator.join(result)

    def attributes(self, row):
        return OrderedDict(
            (self.text(row.get(f'Attribute {index} name')),
             self.text(row.get(f'Attribute {index} value(s)')))
            for index in range(1, self.max_attributes + 1)
            if self.text(row.get(f'Attribute {index} name'))
            and self.text(row.get(f'Attribute {index} name')).casefold() != 'title'
            and self.text(row.get(f'Attribute {index} value(s)'))
        )

    def set_attributes(self, row, names, values):
        for index in range(1, self.max_attributes + 1):
            fields = [f'Attribute {index} {suffix}' for suffix in ('name', 'value(s)', 'visible', 'global')]
            if index <= len(names):
                name = names[index - 1]
                row[fields[0]], row[fields[1]] = name, values.get(name, '')
                row[fields[2]], row[fields[3]] = '0', '1'
            else:
                for field in fields:
                    row[field] = ''

    def clean(self, row):
        return {key: value for key, value in row.items() if key not in self.metadata_columns}

    def run(self):
        data = self.tool.File.read_csv(path=self.input_file, dtype=str, keep_default_na=False).fillna('')
        missing = set(self.metadata_columns).difference(data.columns)
        if missing:
            raise ValueError(f'Missing material-link metadata: {sorted(missing)}')
        for index in range(1, self.max_attributes + 1):
            for suffix in ('name', 'value(s)', 'visible', 'global'):
                column = f'Attribute {index} {suffix}'
                if column not in data:
                    data[column] = ''

        children_by_parent = {}
        for _, row in data[data['Type'].str.casefold() == 'variation'].iterrows():
            children_by_parent.setdefault(self.text(row['Parent']), []).append(row.to_dict())

        families = OrderedDict()
        for _, row in data[data['Type'].str.casefold().isin({'variable', 'simple'})].iterrows():
            parent = row.to_dict()
            handle = self.text(parent.get('__source_handle'))
            if not handle:
                continue
            families[handle] = {
                'parent': parent,
                'children': children_by_parent.get(self.text(parent['SKU']), []),
                'links': self.decode(parent.get('__linked_handles'), list),
                'options': self.decode(parent.get('__linked_options'), dict),
            }

        root = {handle: handle for handle in families}

        def find(handle):
            while root[handle] != handle:
                root[handle] = root[root[handle]]
                handle = root[handle]
            return handle

        for handle, family in families.items():
            for linked in family['links']:
                if linked not in families or handle not in families[linked]['links']:
                    continue
                left, right = find(handle), find(linked)
                if left != right:
                    root[right] = left

        components = OrderedDict()
        for handle in families:
            components.setdefault(find(handle), []).append(handle)
        components = OrderedDict(
            (key, handles) for key, handles in components.items() if len(handles) > 1
        )
        component_for = {handle: key for key, handles in components.items() for handle in handles}

        output, emitted = [], set()
        for handle, family in families.items():
            component = component_for.get(handle)
            if component is None:
                output.append(self.clean(family['parent']))
                output.extend(self.clean(row) for row in family['children'])
                continue
            if component in emitted:
                continue
            emitted.add(component)
            members = [families[item] for item in components[component]]
            parent = members[0]['parent'].copy()
            parent_sku = 'linked-material-' + hashlib.sha1('|'.join(sorted(components[component])).encode()).hexdigest()[:12]
            categories = self.join_unique((member['parent']['Categories'] for member in members), ' | ')
            images = self.join_unique(
                (row['Images'] for member in members for row in [member['parent'], *member['children']]),
                self.tool.config.images_split or ',',
            )
            option_names = list(OrderedDict.fromkeys(
                name for member in members
                for name in [*member['options'], *self.attributes(member['parent']),
                             *(name for child in member['children'] for name in self.attributes(child))]
            ))
            if len(option_names) > self.max_attributes:
                raise ValueError(f'{parent["Name"]!r} has more than {self.max_attributes} options')
            parent.update({'Type': 'variable', 'SKU': parent_sku, 'Parent': '', 'Categories': categories, 'Images': images})

            variants, values = [], OrderedDict((name, []) for name in option_names)
            for member in members:
                source_options = {self.text(key): self.text(value) for key, value in member['options'].items()}
                source_rows = member['children'] or [member['parent']]
                for source in source_rows:
                    variant = source.copy()
                    attributes = {**source_options, **self.attributes(source)}
                    for name, value in attributes.items():
                        if name in values and value and value not in values[name]:
                            values[name].append(value)
                    variant.update({
                        'Type': 'variation', 'Name': parent['Name'], 'Parent': parent_sku,
                        'Categories': categories, 'Description': '',
                    })
                    if not self.text(variant.get('Images')):
                        variant['Images'] = member['parent']['Images']
                    self.set_attributes(variant, option_names, attributes)
                    variants.append(self.clean(variant))
            self.set_attributes(parent, option_names, {name: ','.join(value) for name, value in values.items()})
            output.append(self.clean(parent))
            output.extend(variants)

        columns = [column for column in data.columns if column not in self.metadata_columns]
        self.tool.File.save_csv(output, self.output_file, columns=columns)
        self.tool.print(f'合并 {len(components)} 个双方确认的材料变体家族。', color='green')


if __name__ == '__main__':
    MousMaterialMerge(
        Tool,
        Tool.File.path_add_site('res/result.csv'),
        Tool.File.path_add_site('fwq/merged_material_variants.csv'),
    ).run()
    Tool.close()
