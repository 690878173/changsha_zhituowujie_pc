"""站点输入层 TOML 加载器。

该模块只负责读取模板目录中的 ``config.toml``，底层 Tool 和 Step API 不变。
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


def _optional(section: Mapping[str, Any], key: str) -> Any:
    value = section.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return value


@dataclass(frozen=True)
class TomlSiteConfig:
    """模板输入层的通用站点配置。"""

    source_path: Path
    base_url: Any
    site: Any
    site_type: Any
    zk: Any
    headers: Any
    cookies: Any
    max_retry: Any
    time_out: Any
    images_split: Any
    custom_key: Any
    browser: Any

    @classmethod
    def from_file(cls, path: str | Path) -> "TomlSiteConfig":
        config_path = Path(path)
        if config_path.suffix.lower() != ".toml":
            config_path = config_path.with_name("config.toml")
        config_path = config_path.resolve()
        with config_path.open("rb") as stream:
            data = tomllib.load(stream)
        if not isinstance(data, Mapping):
            raise TypeError("TOML root must be a table.")

        site = data.get("site") or {}
        request = data.get("request") or {}
        if not isinstance(site, Mapping):
            raise TypeError("config.site must be a TOML table.")
        if not isinstance(request, Mapping):
            raise TypeError("config.request must be a TOML table.")

        return cls(
            source_path=config_path,
            base_url=site.get("base_url", ""),
            site=site.get("site", ""),
            site_type=_optional(site, "site_type"),
            zk=site.get("zk"),
            headers=_optional(request, "headers"),
            cookies=_optional(request, "cookies"),
            max_retry=request.get("max_retry"),
            time_out=request.get("time_out"),
            images_split=_optional(request, "images_split"),
            custom_key=_optional(request, "custom_key"),
            browser=request.get("browser"),
        )

    def build_tool(self):
        """使用现有底层 Tool_config 创建 Tool"""
        from .base_tool import Base_tool
        from .config import Tool_config

        config = Tool_config(
            base_url=self.base_url,
            site=self.site,
            zk=self.zk,
            site_type=self.site_type,
            max_retry=self.max_retry,
            time_out=self.time_out,
            headers=self.headers,
            cookies=self.cookies,
            custom_key=self.custom_key,
            images_split=self.images_split,
            browser=self.browser,
        )
        return config, Base_tool(config)


__all__ = ["TomlSiteConfig"]
