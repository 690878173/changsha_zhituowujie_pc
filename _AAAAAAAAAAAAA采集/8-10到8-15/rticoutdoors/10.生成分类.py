import re
from pathlib import Path

import pandas as pd
from config import Tool

input_csv = Tool.File.dz_path()
output_csv = Tool.File.fl_path()


SMART_COLLECTION_COLUMNS = [
    "Handle",
    "Command",
    "Title",
    "Body HTML",
    "Sort Order",
    "Published",
    "Published Scope",
    "Row #",
    "Top Row",
    "Image Src",
    "Image Width",
    "Image Height",
    "Image Alt Text",
    "Must Match",
    "Rule: Product Column",
    "Rule: Relation",
    "Rule: Condition",
    "Published: Online Store",
    "Published: POS",
    "Published: Shop"
]


def make_handle(title):
    handle = title.strip().lower()
    handle = re.sub(r"[^a-z0-9]+", "-", handle)
    return handle.strip("-")


def get_unique_tags(input_csv):
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


def struct_smart_collection(input_csv, output_csv):
    rows = []

    for row_number, tag in enumerate(get_unique_tags(input_csv), start=1):
        rows.append(
            {
                "Handle": make_handle(tag),
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
            }
        )

    output_path = Path(output_csv)
    chunk_size = 99

    for index, start in enumerate(range(0, len(rows), chunk_size), start=1):
        chunk = rows[start : start + chunk_size]
        chunk_path = output_path
        if index > 1:
            chunk_path = output_path.with_name(
                f"{output_path.stem}_{index}{output_path.suffix}"
            )

        pd.DataFrame(chunk, columns=SMART_COLLECTION_COLUMNS).to_csv(
            chunk_path,
            mode="w",
            index=False,
            header=True,
            encoding="utf-8-sig",
        )
        print(f"Data successfully written to {chunk_path}")


def main():
    struct_smart_collection(input_csv, output_csv)


if __name__ == "__main__":
    main()
