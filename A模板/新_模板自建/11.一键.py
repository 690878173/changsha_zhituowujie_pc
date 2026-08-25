"""Run the self-hosted template pipeline in the configured order."""

import subprocess
import sys
from pathlib import Path

import config


BASE_DIR = Path(__file__).resolve().parent


def main():
    steps = getattr(config, "pipeline_steps", list(range(1, 11)))
    for number in steps:
        script = next(BASE_DIR.glob(f"{number}*.py"), None)
        if script is None:
            raise FileNotFoundError(f"未找到步骤 {number} 的脚本")
        print(f"\n{'=' * 60}\n[运行] {script.name}\n{'=' * 60}")
        result = subprocess.run([sys.executable, str(script)], cwd=BASE_DIR)
        if result.returncode:
            raise SystemExit(result.returncode)
    print("\n全部步骤执行完成。")


if __name__ == "__main__":
    main()
