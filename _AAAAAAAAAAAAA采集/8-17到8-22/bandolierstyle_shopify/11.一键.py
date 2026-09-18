import subprocess
import sys
from pathlib import Path

# 所有步骤脚本所在目录（与本脚本同目录）
BASE_DIR = Path(__file__).resolve().parent

# 按顺序运行的步骤脚本（脚本之间存在文件依赖，顺序不可更改）
STEPS = [
    # "5.去重.py",
    # "7.替换图片.py",
    "8.wp_to_shopify.py",
    "9.shopify打折.py",
    "10.生成分类.py",
]


def run_step(script_name: str) -> None:
    """运行单个步骤脚本，失败则中断后续流程。"""
    script_path = BASE_DIR / script_name
    print(f"\n{'=' * 60}")
    print(f"[运行] {script_name}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR),
    )

    if result.returncode != 0:
        print(f"\n[失败] {script_name} 退出码：{result.returncode}，流程中断。")
        raise SystemExit(result.returncode)

    print(f"\n[完成] {script_name}\n")


def main() -> None:
    print("开始一键运行，按顺序执行以下步骤：")
    for i, step in enumerate(STEPS, 1):
        print(f"  {i}. {step}")
    print()

    for i, step in enumerate(STEPS, 1):
        print(f"---- 步骤 {i}/{len(STEPS)} ----")
        run_step(step)

    print("\n全部步骤执行完成。")


if __name__ == "__main__":
    main()
