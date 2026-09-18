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
from .分割csv import split_shopify_csv_large


Tool = Base_tool(config=Tool_config(base_url='',site='',site_type='',zk=1))


__all__ = [
    "Tool_config", "SimTool", "Session", "FailedResponse", "HTML", "URL", "File",
    "Product", "ProductSimple", "ProductVariation", "Base_tool",
    "Browser", "BrowserBackend", "BrowserConfig", "BrowserFetchResponse",
    "DrissionPageBackend", "PlaywrightBackend",
    "_DEFAULT_HEADERS", "_DEFAULT_COOKIES",
    "_CUSTOM_KEY", "_IMAGE_SPLIT", "_MAX_RETRY", "_TIMEOUT", "_IMPERSONATE_TARGET",
    'split_shopify_csv_large',"Tool"
]
