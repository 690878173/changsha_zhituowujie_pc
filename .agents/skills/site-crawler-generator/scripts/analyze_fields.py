"""盘点 CSV、JSON 或 HTML 快照中的字段，输出可审阅的 JSON 报告。"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def json_keys(value: Any, prefix: str = "") -> Counter[str]:
    result: Counter[str] = Counter()
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result[path] += 1
            result.update(json_keys(child, path))
    elif isinstance(value, list):
        for child in value[:20]:
            result.update(json_keys(child, prefix + "[]"))
    return result


def analyze(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    report: dict[str, Any] = {"file": str(path), "type": suffix.lstrip("."), "fields": {}}
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        report["rows"] = len(rows)
        report["fields"] = {
            key: {"non_empty": sum(bool((row.get(key) or "").strip()) for row in rows)}
            for key in (reader.fieldnames or [])
        }
        return report
    text = path.read_text(encoding="utf-8", errors="replace")
    if suffix in {".json", ".jsonl"}:
        try:
            value = json.loads(text)
            report["fields"] = dict(json_keys(value))
            return report
        except json.JSONDecodeError:
            pass
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", text, flags=re.I | re.S)
    candidates = Counter(re.findall(r"(?:metafield|data-[\w-]+|product\.\w+|variant\w*)", text, flags=re.I))
    candidates.update(re.findall(r'"([A-Za-z][A-Za-z0-9_.:-]{2,})"\s*:', "\n".join(scripts)))
    report["script_blocks"] = len(scripts)
    report["fields"] = dict(candidates)
    report["notes"] = "HTML 结果是候选字段盘点，必须结合 DOM/JSON 语义人工确认。"
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.path)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(args.output)
    else:
        print(payload)


if __name__ == "__main__":
    main()
