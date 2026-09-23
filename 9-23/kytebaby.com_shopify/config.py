"""Site configuration loaded from the adjacent config.toml."""
from _ljp.toml_config import TomlSiteConfig


_settings = TomlSiteConfig.from_file(__file__)

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
