"""步骤10：生成 Shopify 智能分类（Collection）模板

通用流程：读取打折后 CSV 的 Tags 列 -> 去重 -> 生成 smart collection 行 -> 按 99 条分块写出。

"""
import re
from pathlib import Path

import pandas as pd


class Step10Collection:
    """生成分类基类"""

    SMART_COLLECTION_COLUMNS = [
        "Handle", "Command", "Title", "Body HTML", "Sort Order", "Published",
        "Published Scope", "Row #", "Top Row", "Image Src", "Image Width",
        "Image Height", "Image Alt Text", "Must Match", "Rule: Product Column",
        "Rule: Relation", "Rule: Condition", "Published: Online Store",
        "Published: POS", "Published: Shop",
    ]

    CHUNK_SIZE = 99

    def __init__(self, tool, input_csv, output_csv):
        self.tool = tool
        self.Tool = tool
        self.input_csv = input_csv
        self.output_csv = output_csv

    @staticmethod
    def make_handle(title):
        handle = title.strip().lower()
        handle = re.sub(r"[^a-z0-9]+", "-", handle)
        return handle.strip("-")

    def get_unique_tags(self, input_csv):
        df = pd.read_csv(input_csv)
        if "Tags" not in df.columns:
            raise ValueError('Input CSV must contain a "Tags" column.')

        unique_tags = []
        seen = set()
        for tags in df["Tags"].dropna():
            for tag in str(tags).split(","):
                tag = tag.strip()
                if not tag:
                    continue
                key = tag.casefold()
                if key in seen:
                    continue
                seen.add(key)
                unique_tags.append(tag)
        return unique_tags

    def struct_smart_collection(self, input_csv, output_csv):
        rows = []
        for row_number, tag in enumerate(self.get_unique_tags(input_csv), start=1):
            rows.append({
                "Handle": self.make_handle(tag),
                "Command": "MERGE",
                "Title": tag,
                "Body HTML": "",
                "Sort Order": "Best Selling",
                "Published": "TRUE",
                "Published Scope": "global",
                "Row #": row_number,
                "Top Row": "TRUE",
                "Image Src": "",
                "Image Width": "",
                "Image Height": "",
                "Image Alt Text": "",
                "Must Match": "all conditions",
                "Rule: Product Column": "Tag",
                "Rule: Relation": "Equals",
                "Rule: Condition": tag,
                "Published: Online Store": "TRUE",
                "Published: POS": "TRUE",
                "Published: Shop": "TRUE",
            })

        output_path = Path(output_csv)
        for index, start in enumerate(range(0, len(rows), self.CHUNK_SIZE), start=1):
            chunk = rows[start:start + self.CHUNK_SIZE]
            chunk_path = output_path
            if index > 1:
                chunk_path = output_path.with_name(f"{output_path.stem}_{index}{output_path.suffix}")

            pd.DataFrame(chunk, columns=self.SMART_COLLECTION_COLUMNS).to_csv(
                chunk_path, mode="w", index=False, header=True, encoding="utf-8-sig",
            )
            print(f"成功写入，路径: {chunk_path}")

    def run(self):
        self.struct_smart_collection(self.input_csv, self.output_csv)
        return self.output_csv
