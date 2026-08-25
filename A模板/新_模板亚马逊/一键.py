"""Run numbered Amazon template steps in the configured order."""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def main():
    import config

    try:
        for number in config.pipeline_steps:
            script = next(ROOT.glob(f"{number}.*.py"), None)
            if script is None:
                raise FileNotFoundError(f"未找到步骤 {number} 的脚本")
            print(f"\n{'=' * 60}\n[运行] {script.name}\n{'=' * 60}")
            result = subprocess.run([sys.executable, str(script)], cwd=ROOT)
            if result.returncode:
                raise SystemExit(result.returncode)
    finally:
        config.Tool.close()


if __name__ == "__main__":
    main()
