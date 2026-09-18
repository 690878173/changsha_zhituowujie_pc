"""从 A模板 复制一个站点目录并填写最小配置。"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


TYPE_ALIASES = {
    "shopify": ("新_模板shopify", "shopify", "shopify"),
    "mg_shopify": ("新_模板魔改shopify", "mg_shopify", "mg_shopify"),
    # 自建模板依赖空 site_type 生成历史兼容的输出文件名。
    "self_hosted": ("新_模板自建", "self_hosted", ""),
    "target": ("新_模板target", "target", "target"),
    "amazon": ("新_模板亚马逊", "amazon", "amazon"),
}


def normalize_type(value: str) -> str:
    value = value.strip().lower().replace("-", "_")
    aliases = {"mg": "mg_shopify", "magic_shopify": "mg_shopify", "custom": "self_hosted", "自建": "self_hosted", "魔改": "mg_shopify"}
    value = aliases.get(value, value)
    if value not in TYPE_ALIASES:
        raise ValueError(f"不支持的站点类型: {value}，可选 {', '.join(TYPE_ALIASES)}")
    return value


def update_config(path: Path, *, site: str, site_type: str, base_url: str) -> None:
    text = path.read_text(encoding="utf-8")
    replacements = {
        r'(?m)^base_url\s*=\s*".*?"$': f'base_url = "{base_url}"',
        r'(?m)^site\s*=\s*".*?"$': f'site = "{site}"',
        r'(?m)^site_type\s*=\s*".*?"$': f'site_type = "{site_type}"',
    }
    for pattern, replacement in replacements.items():
        text, count = re.subn(pattern, replacement, text, count=1)
        if count != 1:
            raise ValueError(f"无法更新配置项: {pattern}")
    path.write_text(text, encoding="utf-8")


def generate(site: str, site_type: str, base_url: str, output_root: Path, overwrite: bool = False) -> Path:
    site_type = normalize_type(site_type)
    template_name, suffix, config_type = TYPE_ALIASES[site_type]
    repo_root = Path(__file__).resolve().parents[4]
    template = repo_root / "A模板" / template_name
    if not template.is_dir():
        raise FileNotFoundError(template)
    safe_site = re.sub(r"[^A-Za-z0-9_.-]+", "-", site.strip()).strip("-")
    if not safe_site:
        raise ValueError("site 不能为空，且至少包含字母、数字、点、下划线或短横线")
    destination = output_root.resolve() / f"{safe_site}_{suffix}"
    if destination.exists():
        if not overwrite:
            raise FileExistsError(f"目标已存在: {destination}；如需覆盖请显式传 --overwrite")
        shutil.rmtree(destination)
    shutil.copytree(template, destination)
    update_config(destination / "config.toml", site=safe_site, site_type=config_type, base_url=base_url)
    for name in ("analysis", "data", "res", "hc", "fail", "fwq"):
        (destination / name).mkdir(exist_ok=True)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, help="站点标识，例如 example")
    parser.add_argument("--type", required=True, dest="site_type", help="shopify/mg_shopify/self_hosted/target/amazon")
    parser.add_argument("--base-url", default="", help="站点首页 URL")
    parser.add_argument("--output-root", default=".", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    print(generate(args.site, args.site_type, args.base_url, args.output_root, args.overwrite))


if __name__ == "__main__":
    main()
