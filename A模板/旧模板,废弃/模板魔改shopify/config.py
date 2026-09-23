"""
站点配置文件 — 从 config.toml 读取所有配置，初始化 Tool 实例

用法：复制整个模板目录到站点目录，修改 config.toml，然后运行脚本
"""
from __future__ import annotations

from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # pip install tomli

from _ljp import Base_tool, Tool_config
from shopify_tool import ShopifyCommon

# ── 加载 TOML 配置 ──────────────────────────────────
_CONFIG_PATH = Path(__file__).with_name("config.toml")
with _CONFIG_PATH.open("rb") as _f:
    _cfg = tomllib.load(_f)

# ── 提取配置变量 ──────────────────────────────────
base_url: str = _cfg["base_url"].rstrip("/")
home_url: str = _cfg.get("home_url", base_url + "/")
site: str = _cfg["site"]
site_name: str = _cfg["site_name"]
brand: str = _cfg.get("brand", site_name)

# Shopify Storefront 专用
store_domain: str = _cfg.get("store_domain", "")
storefront_token: str = _cfg.get("storefront_token", "")
api_version: str = _cfg.get("api_version", "2026-04")
country: str = _cfg.get("country", "US")
language: str = _cfg.get("language", "EN")
currency: str = _cfg.get("currency", "USD")

# 导航/目录
menu_handles: list[str] = _cfg.get("menu_handles", ["main-menu"])
exclude_collection_patterns: list[str] = _cfg.get("exclude_collection_patterns", [])
navigation_xpath: str | None = _cfg.get("navigation_xpath")

# 图片/变体
image_group_options: list[str] = _cfg.get("image_group_options", ["Color", "Colour", "Style"])

# 自定义字段
custom_fields: list[dict] = _cfg.get("custom_fields", [])
remix_data: dict = _cfg.get("remix_data", {})
sample_products: list[dict] = _cfg.get("sample_products", [])

# 运行时参数
run_mode: str = _cfg.get("run_mode", "auto")
sample_limit: int = _cfg.get("sample_limit", 10)
full_threshold: int = _cfg.get("full_threshold", 500)
max_url_pages: int = _cfg.get("max_url_pages", 10)
resume: bool = _cfg.get("resume", True)

# 折扣
zk: float = _cfg.get("zk", 0)

# 请求头 / Cookie（None = 使用 _ljp 默认值）
headers = _cfg.get("headers")
cookies = _cfg.get("cookies")
custom_key = _cfg.get("custom_key")
images_split = _cfg.get("images_split")

# 引擎延迟（秒）
request_delay_range: tuple = tuple(_cfg.get("request_delay_range", [0.15, 0.35]))

# ── 构建站点配置 dict（传给 storefront_engine） ──────
site_config: dict = {
    "site_name": site_name,
    "base_url": base_url,
    "home_url": home_url,
    "brand": brand,
    "store_domain": store_domain,
    "storefront_token": storefront_token,
    "api_version": api_version,
    "country": country,
    "language": language,
    "currency": currency,
    "menu_handles": menu_handles,
    "exclude_collection_patterns": exclude_collection_patterns,
    "image_group_options": image_group_options,
    "custom_fields": custom_fields,
    "remix_data": remix_data,
    "sample_products": sample_products,
    "navigation_xpath": navigation_xpath,
    "request_delay_range": list(request_delay_range),
    "project_dir": str(_CONFIG_PATH.parent.resolve()),
}

# ── 初始化 Tool ────────────────────────────────────
config = Tool_config(
    base_url=base_url,
    site=site,
    zk=zk,
    site_type="shopify",
    headers=headers,
    cookies=cookies,
    custom_key=custom_key,
    images_split=images_split,
)

Tool = Base_tool(config)
# 挂载 Shopify 通用工具
Tool.Shopify = ShopifyCommon(Tool)
