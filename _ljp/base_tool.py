import subprocess
import sys
from typing import Any, Callable

from .config import Tool_config
from .file_utils import File
from .url_utils import URL
from .html_utils import HTML
from .product import Product
from .session import Session
from .simtool import SimTool
from .browser import Browser


class Base_tool:
    """Typed public facade exposed as the site-local ``Tool`` instance."""

    config: Tool_config
    base_url: str
    site: str
    max_retry: int
    time_out: float
    headers: dict[str, Any]
    cookies: dict[str, Any]
    site_type: str | None
    custom_key: str | None
    zk: float

    _File: File
    _URL: URL
    _HTML: HTML
    _Product: Product
    _session: Session
    _browser: Browser
    Browser: Browser
    zs: Callable[..., Any]

    def __init__(self, config: Tool_config):
        self.config = config
        self.base_url = config.base_url
        self.site = config.site
        self.max_retry = config.max_retry
        self.time_out = config.time_out
        self.headers = config.headers
        self.cookies = config.cookies
        self.site_type = config.site_type
        self.custom_key = config.custom_key
        self.zk = config.zk
        self.File = File(self.config)
        self.URL = URL(self.config)
        self.HTML = HTML(self.config)
        self.Product = Product(self.config)
        self.session = Session(self.config)
        self.browser = Browser(self.config.browser)
        # Legacy site Steps use both spellings; they share one thread-local facade.
        self.Browser = self.browser

        self.zs = SimTool.zs

    def get(self, url, headers=None, cookies=None, params=None, **kwargs):
        return self.session.get(url, headers=headers, cookies=cookies, params=params, **kwargs)

    def post(self, url, **kwargs):
        """Send a POST request through the shared retrying HTTP client."""
        return self.session.post(url, **kwargs)

    def make_counter(self, ts_num):
        if ts_num is None:
            def counter():
                return None  # 表示无限
        else:
            self.print(f'启动测试模式,当前测试数量:{ts_num}')
            count = ts_num

            def counter():
                nonlocal count
                if count == 0:
                    return 0  # 表示已耗尽
                count -= 1
                return count
        return counter

    @staticmethod
    def to_ml_data(data: dict) -> dict:
        if not isinstance(data, dict):
            raise TypeError('ml data must be a dictionary.')
        res = {}

        def walk(path, node):
            if isinstance(node, str):
                res[path] = node
                return
            if not isinstance(node, dict):
                raise TypeError(f'Invalid ml node at {path!r}: {type(node).__name__}.')
            _url = node.get('url')
            if _url:
                res[path] = _url
            for ck, cv in (node.get("child") or {}).items():
                walk(f"{path},{path.split(',')[-1]} {ck}", cv)

        for k, v in data.items():
            walk(k, v)
        return res

    def to_ml_json(self, data, file_path):
        if not isinstance(data, dict):
            raise TypeError('ml data must be a dictionary.')
        filtered = {key: value for key, value in data.items() if key != self.custom_key}
        return self.File.save_json(self.to_ml_data(filtered), file_path)

    @staticmethod
    def clean_price(price):
        return str(price).replace("$", "").replace("/ea", "").replace("/EA", "")

    @staticmethod
    def sort_data(data):
        return {k: data[k] for k in sorted(data.keys(), key=int)}

    def json_del_url(self, data:list,targe='url'):
        return self.File.json_ls_del(data,targe)

    @staticmethod
    def print(msg, color="red"):
        SimTool.print(msg, color)

    def last_print(self):
        self.config.print()

    def close(self):
        if getattr(self, "session", None) is not None:
            self.session.close()
        if getattr(self, "browser", None) is not None:
            self.browser.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
        return False


    def run(self,BASE_DIR ,STEPS):
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
        print("开始一键运行，按顺序执行以下步骤：")
        for i, step in enumerate(STEPS, 1):
            print(f"  {i}. {step}")
        print()

        for i, step in enumerate(STEPS, 1):
            print(f"---- 步骤 {i}/{len(STEPS)} ----")
            run_step(step)

        print("\n全部步骤执行完成。")


    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
