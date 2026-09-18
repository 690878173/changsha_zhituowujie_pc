import subprocess
import sys
from pathlib import Path
from config import Tool
# 所有步骤脚本所在目录（与本脚本同目录）
BASE_DIR = Path(__file__).resolve().parent


STEPS = [
    "5.去重.py",
    "7.替换图片.py",
    "8.wp_to_shopify.py",
    "9.shopify打折.py",
    "10.生成分类.py",
]

Tool.run(BASE_DIR, STEPS)