"""站点输入配置：读取同目录 config.toml。"""
import sys
from pathlib import Path

# Allow this generated site package to run directly from its own directory.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from _ljp.toml_config import TomlSiteConfig


_settings = TomlSiteConfig.from_file(__file__)

# 保留模板原有公共变量，Step 文件无需改动。
base_url = _settings.base_url
site = _settings.site
site_type = _settings.site_type
zk = _settings.zk
headers = _settings.headers
cookies = _settings.cookies
max_retry = _settings.max_retry
time_out = _settings.time_out
images_split = _settings.images_split
custom_key = _settings.custom_key
browser = _settings.browser

config, Tool = _settings.build_tool()
