import json
from pathlib import Path
from typing import List, Any


class JsonDiffer:
    def __init__(self):
        self.diffs = []

    def add(self, loc: str, msg: str):
        self.diffs.append(f"[{loc}] {msg}")

    def compare(self, a: Any, b: Any, path="$"):
        if type(a) != type(b):
            self.add(path, f"类型不同：{type(a).__name__} vs {type(b).__name__}")
            return
        if isinstance(a, dict):
            ka = set(a.keys())
            kb = set(b.keys())
            for k in ka - kb:
                self.add(f"{path}.{k}", "仅左侧存在key")
            for k in kb - ka:
                self.add(f"{path}.{k}", "仅右侧存在key")
            for k in ka & kb:
                self.compare(a[k], b[k], f"{path}.{k}")
        elif isinstance(a, list):
            if len(a) != len(b):
                self.add(path, f"数组长度不一致 {len(a)} vs {len(b)}")
            maxlen = max(len(a), len(b))
            for idx in range(maxlen):
                va = a[idx] if idx < len(a) else None
                vb = b[idx] if idx < len(b) else None
                self.compare(va, vb, f"{path}[{idx}]")
        else:
            if a != b:
                self.add(path, f"值不等：{repr(a)} != {repr(b)}")


def diff_json(file_a: str, file_b: str) -> list[str]:
    try:
        with open(file_a, "r", encoding="utf-8") as f:
            data_a = json.load(f)
        with open(file_b, "r", encoding="utf-8") as f:
            data_b = json.load(f)
    except Exception as e:
        return [f"JSON读取失败: {str(e)}"]
    jd = JsonDiffer()
    jd.compare(data_a, data_b)
    return jd.diffs


def diff_text(file_a: str, file_b: str) -> list[str]:
    try:
        with open(file_a, "r", encoding="utf-8") as f:
            lines_a = [ln.rstrip("\n") for ln in f.readlines()]
        with open(file_b, "r", encoding="utf-8") as f:
            lines_b = [ln.rstrip("\n") for ln in f.readlines()]
    except Exception as e:
        return [f"文件读取失败: {str(e)}"]
    diffs = []
    max_row = max(len(lines_a), len(lines_b))
    for i in range(max_row):
        la = lines_a[i] if i < len(lines_a) else "[无此行]"
        lb = lines_b[i] if i < len(lines_b) else "[无此行]"
        if la != lb:
            diffs.append(f"【行{i+1}】A={repr(la)} | B={repr(lb)}")
    return diffs


def auto_compare(file1: str, file2: str, rel_path: str):
    suffix = Path(rel_path).suffix.lower()
    if suffix == ".json":
        return diff_json(file1, file2)
    else:
        return diff_text(file1, file2)


# =================配置================
BASE_DIRS = [
    r"J:\changsha\装修\data\原始模板",
        # r"J:\changsha\装修\data\导入模板",
        # r"J:\changsha\装修\data\导入模板2",
        r"J:\changsha\装修\data\导入模板2",
]
# 在这里填入目录扫描脚本输出的、有差异的文件相对路径
TARGET_REL_PATH = ["config/settings_data.json",
                   'templates/cart.json',
                   r'templates\index.json',
                   r'templates\product.json',
                   r'templates\search.json',
                   r'sections\footer-group.json']
# ====================================
def main():
    full_paths = [str(Path(d)) for d in BASE_DIRS]
    count = len(full_paths)
    print(f"对比文件：{TARGET_REL_PATH}\n")
    for idx, fp in enumerate(full_paths, 1):
        print(f"文件{idx}: {fp}")
    print("-" * 60)

    if count == 2:
        res = auto_compare(full_paths[0], full_paths[1], TARGET_REL_PATH)
        if not res:
            print("✅ 文件完全一致")
        else:
            for line in res:
                print(line)
    elif count == 3:
        pairs = [
            (0, 1, "目录1 VS 目录2"),
            (0, 2, "目录1 VS 目录3"),
            (1, 2, "目录2 VS 目录3")
        ]
        for i, j, title in pairs:
            print(f"\n==== {title} ====")
            for path in TARGET_REL_PATH:
                res = auto_compare(full_paths[i], full_paths[j], path)
                if not res:
                    print("✅ 一致")
                else:
                    for line in res:
                        print(line)


if __name__ == "__main__":
    main()
