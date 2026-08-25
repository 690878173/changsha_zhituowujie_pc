"""_ljp 工具包 — 爬虫/数据处理基础框架"""

from .config import (
    _DEFAULT_HEADERS, _DEFAULT_COOKIES,
    _CUSTOM_KEY, _IMAGE_SPLIT, _MAX_RETRY, _TIMEOUT, _IMPERSONATE_TARGET,
    Tool_config,
)
from .simtool import SimTool
from .session import FailedResponse, Session
from .html_utils import HTML

from .url_utils import URL
from .file_utils import File
from .product import Product, ProductSimple, ProductVariation
from .base_tool import Base_tool
from .browser import (
    Browser, BrowserBackend, BrowserConfig, BrowserFetchResponse,
    DrissionPageBackend, PlaywrightBackend,
)


# 为了兼容旧代码，保持 _Simple / _Variation 作为别名
_Simple = ProductSimple
_Variation = ProductVariation

# Fc 是 File 的缩写别名（部分老项目使用）
Fc = File

# zs 装饰器快捷引用
zs = SimTool.zs

__all__ = [
    "Tool_config", "SimTool", "Session", "FailedResponse", "HTML", "URL", "File",
    "Product", "ProductSimple", "ProductVariation", "Base_tool",
    "Browser", "BrowserBackend", "BrowserConfig", "BrowserFetchResponse",
    "DrissionPageBackend", "PlaywrightBackend", "zs",
    "_Simple", "_Variation", "Fc",
    "_DEFAULT_HEADERS", "_DEFAULT_COOKIES",
    "_CUSTOM_KEY", "_IMAGE_SPLIT", "_MAX_RETRY", "_TIMEOUT", "_IMPERSONATE_TARGET",
]
