"""在 SKU 去重后，按实际子类属性修正 Shopify 父类。"""

import re

import pandas as pd

from config import Tool


input_file = Tool.File.path_add_site('fwq/quchong.csv')
output_file = Tool.File.path_add_site('fwq/variable.csv')


class ParentAttributeNormalizer:
    """保留既有父子行，只用子类实际值重建父类属性。"""

    MAX_SHOPIFY_OPTIONS = 3
    ATTRIBUTE_PATTERN = re.compile(r'^Attribute (\d+) (?:name|value\(s\)|visible|global)$')

    def __init__(self, tool, input_path, output_path):
        self.tool = tool
        self.input_path = input_path
        self.output_path = output_path

    @staticmethod
    def _text(value):
        if pd.isna(value):
            return ''
        return str(value).strip()

    @classmethod
    def _attribute_numbers(cls, columns):
        return sorted({
            int(match.group(1))
            for column in columns
            if (match := cls.ATTRIBUTE_PATTERN.match(column))
        })

    @staticmethod
    def _ordered_values(values):
        collected = []
        for value in values:
            if value and value not in collected:
                collected.append(value)
        return collected

    def _family_attributes(self, parent, children, attribute_numbers):
        attributes = []
        for source_index in attribute_numbers:
            name_key = f'Attribute {source_index} name'
            value_key = f'Attribute {source_index} value(s)'
            name = self._text(parent.get(name_key, ''))
            if not name:
                name = next((
                    self._text(child.get(name_key, ''))
                    for child in children
                    if self._text(child.get(name_key, ''))
                ), '')
            if not name:
                continue
            values = self._ordered_values(
                self._text(child.get(value_key, ''))
                for child in children
            )
            attributes.append({
                'source_index': source_index,
                'name': name,
                'values': values,
            })
        return attributes

    @staticmethod
    def _write_attribute(row, index, name, value):
        row[f'Attribute {index} name'] = name
        row[f'Attribute {index} value(s)'] = value
        row[f'Attribute {index} visible'] = 0
        row[f'Attribute {index} global'] = 1

    @staticmethod
    def _clear_attributes(row, attribute_numbers):
        for index in attribute_numbers:
            for suffix in ('name', 'value(s)', 'visible', 'global'):
                key = f'Attribute {index} {suffix}'
                if key in row:
                    row[key] = ''

    def _rebuild_parent_values(self, parent, attributes):
        for attribute in attributes:
            self._write_attribute(
                parent,
                attribute['source_index'],
                attribute['name'],
                ','.join(attribute['values']),
            )

    def _reduce_single_value_options(self, parent, children, attributes, attribute_numbers):
        """超过三个属性时，将单值属性移入名称并同步父子行。"""
        remaining = list(attributes)
        folded = []
        while len(remaining) > self.MAX_SHOPIFY_OPTIONS:
            singleton_index = next(
                (index for index, attribute in enumerate(remaining)
                 if len(attribute['values']) == 1),
                None,
            )
            if singleton_index is None:
                break
            folded.append(remaining.pop(singleton_index))

        if folded:
            child_values = [
                {
                    attribute['source_index']: self._text(
                        child.get(f"Attribute {attribute['source_index']} value(s)", '')
                    )
                    for attribute in attributes
                }
                for child in children
            ]
            suffix = ' - '.join(attribute['values'][0] for attribute in folded)
            base_name = self._text(parent.get('Name', ''))
            name = f'{base_name} - {suffix}' if base_name else suffix
            parent['Name'] = name
            for child in children:
                child['Name'] = name

            self._clear_attributes(parent, attribute_numbers)
            for child in children:
                self._clear_attributes(child, attribute_numbers)

            for target_index, attribute in enumerate(remaining, start=1):
                self._write_attribute(
                    parent,
                    target_index,
                    attribute['name'],
                    ','.join(attribute['values']),
                )
                for child, values in zip(children, child_values):
                    self._write_attribute(
                        child,
                        target_index,
                        attribute['name'],
                        values[attribute['source_index']],
                    )

        if len(remaining) > self.MAX_SHOPIFY_OPTIONS:
            names = ', '.join(attribute['name'] for attribute in remaining)
            self.tool.print(
                '[WARN] Shopify 父类属性仍超过 3，未自动拆分产品：'
                f"{parent.get('Name', '')}（{len(remaining)} 个：{names}）",
                color='yellow',
            )
        return bool(folded)

    def run(self):
        frame = self.tool.File.read_csv(path=self.input_path).fillna('')
        required_columns = {'Type', 'SKU', 'Parent', 'Name'}
        missing = required_columns.difference(frame.columns)
        if missing:
            raise KeyError(f'生成父类缺少字段：{sorted(missing)}')

        rows = frame.to_dict(orient='records')
        attribute_numbers = self._attribute_numbers(frame.columns)
        children_by_parent = {}
        for row in rows:
            if self._text(row.get('Type', '')).lower() != 'variation':
                continue
            parent_sku = self._text(row.get('Parent', ''))
            if parent_sku:
                children_by_parent.setdefault(parent_sku, []).append(row)

        processed = 0
        folded = 0
        for parent in rows:
            if self._text(parent.get('Type', '')).lower() != 'variable':
                continue
            children = children_by_parent.get(self._text(parent.get('SKU', '')), [])
            if not children:
                continue

            attributes = self._family_attributes(parent, children, attribute_numbers)
            self._rebuild_parent_values(parent, attributes)
            processed += 1
            if len(attributes) > self.MAX_SHOPIFY_OPTIONS:
                folded += self._reduce_single_value_options(
                    parent,
                    children,
                    attributes,
                    attribute_numbers,
                )

        columns = list(frame.columns)
        for row in rows:
            for column in row:
                if column not in columns:
                    columns.append(column)
        self.tool.File.save_csv(rows, self.output_path, columns=columns)
        self.tool.print(
            f'父类属性处理完成：{processed} 个父类，折叠 {folded} 个超限父类，保存至 {self.output_path}',
            color='green',
        )
        return rows


if __name__ == '__main__':
    ParentAttributeNormalizer(Tool, input_file, output_file).run()
