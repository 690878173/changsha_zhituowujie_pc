import subprocess
import sys
from pathlib import Path

import config

# 所有步骤脚本所在目录（与本脚本同目录）
BASE_DIR = Path(__file__).resolve().parent

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
    steps = getattr(config, "pipeline_steps", list(range(1, 11)))
    scripts = []
    for number in steps:
        script = next(BASE_DIR.glob(f"{number}*.py"), None)
        if script is None:
            raise FileNotFoundError(f"未找到步骤 {number} 的脚本")
        scripts.append(script.name)

    print("开始一键运行，按顺序执行以下步骤：")
    for i, step in enumerate(scripts, 1):
        print(f"  {i}. {step}")
    print()

    for i, step in enumerate(scripts, 1):
        print(f"---- 步骤 {i}/{len(scripts)} ----")
        run_step(step)

    print("\n全部步骤执行完成。")


if __name__ == "__main__":
    main()
