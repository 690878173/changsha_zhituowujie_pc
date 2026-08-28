import json
from copy import deepcopy
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
import pandas as pd

import aiohttp
import asyncio
from tqdm.asyncio import tqdm_asyncio
import time
from typing import Optional, Union, List, Tuple

_MISSING = object()


class WebPValidator:
    def __init__(
            self,
            file_path: Optional[str] = None,
            df: Optional[pd.DataFrame] = None,
            column_name: str = "Images",
            separator: str = ",",
            max_workers: int = 150,
            timeout: int = 20,
    ):

        if file_path is None and df is None:
            raise ValueError("必须提供 file_path 或 df 参数")
        if file_path is not None and df is not None:
            raise ValueError("file_path 和 df 只能二选一")

        self.column_name = column_name
        self.separator = separator
        self.max_workers = max_workers
        self.timeout = timeout

        if file_path:
            self._load_file(file_path)
        else:
            self.df = df.copy() if df is not None else pd.DataFrame()

        self.results = None  # 验证后存储结果

    def _load_file(self, file_path: str) -> None:

        self.df = pd.read_csv(file_path)

    @staticmethod
    async def _verify_single_url(session, url: str, timeout: int) -> Tuple[bool, str]:
        """验证单个 URL 是否为有效的 WebP（仅读文件头）"""
        try:
            headers = {"Range": "bytes=0-64"}
            async with session.get(url, timeout=timeout, headers=headers) as resp:
                if resp.status not in (200, 206):
                    return False, f"HTTP {resp.status}"

                chunk = await resp.content.read(64)
                if len(chunk) < 12:
                    return False, "文件过小/头部缺失"

                if chunk[0:4] == b'RIFF' and chunk[8:12] == b'WEBP':
                    return True, "OK"
                else:
                    return False, f"非 WebP (头: {chunk[:12]})"

        except asyncio.TimeoutError:
            return False, "超时"
        except aiohttp.ClientError as e:
            return False, f"请求错误: {str(e)[:30]}"
        except Exception as e:
            return False, f"异常: {str(e)[:30]}"

    async def _run_async_verify(self, tasks: List[Tuple[int, str]]) -> List[Tuple[int, str, bool, str]]:
        """异步并发执行验证"""
        connector = aiohttp.TCPConnector(limit=self.max_workers, limit_per_host=20)
        async with aiohttp.ClientSession(connector=connector) as session:
            semaphore = asyncio.Semaphore(self.max_workers)

            async def bounded_verify(row_idx, url):
                async with semaphore:
                    valid, msg = await self._verify_single_url(session, url, self.timeout)
                    return row_idx, url, valid, msg

            coros = [bounded_verify(idx, url) for idx, url in tasks]
            results = []
            for coro in tqdm_asyncio.as_completed(coros, total=len(tasks), desc="验证中"):
                results.append(await coro)
            return results

    def verify(self, verbose: bool = True) -> pd.DataFrame:
        """
        执行验证，返回带验证结果的 DataFrame。

        Args:
            verbose: 是否打印进度和失败摘要，默认 True

        Returns:
            包含原始数据 + '验证状态' + '失败详情' 列的 DataFrame
        """
        # 提取所有 URL 任务
        tasks = []
        for idx, row in self.df.iterrows():
            cell = row.get(self.column_name)
            if pd.isna(cell) or not cell:
                continue
            urls = [u.strip() for u in str(cell).split(self.separator) if u.strip()]
            for url in urls:
                tasks.append((idx, url))

        if verbose:
            print(f"总行数: {len(self.df)}，提取出 {len(tasks)} 个独立 URL")

        if not tasks:
            self.df["验证状态"] = "无URL"
            self.df["失败详情"] = ""
            return self.df

        # 执行异步验证
        start = time.time()
        raw_results = asyncio.run(self._run_async_verify(tasks))
        elapsed = time.time() - start
        if verbose:
            print(f"验证完成，耗时 {elapsed:.2f} 秒")

        # 组织结果
        self.df["验证状态"] = ""
        self.df["失败详情"] = ""
        temp_map = {idx: {} for idx in self.df.index}

        for row_idx, url, valid, msg in raw_results:
            temp_map[row_idx][url] = (valid, msg)

        for idx, url_results in temp_map.items():
            if not url_results:
                self.df.at[idx, "验证状态"] = "无URL"
                continue
            all_ok = all(v for v, _ in url_results.values())
            self.df.at[idx, "验证状态"] = "全部通过" if all_ok else "存在失败"
            fail_msgs = [f"{url}: {msg}" for url, (v, msg) in url_results.items() if not v]
            self.df.at[idx, "失败详情"] = " | ".join(fail_msgs) if fail_msgs else "全部成功"

        # 打印失败摘要
        if verbose:
            failed = self.df[self.df["验证状态"] == "存在失败"]
            if len(failed) > 0:
                print(f"\n❌ 发现 {len(failed)} 行存在失败 URL：")
                print(failed[[self.column_name, "验证状态", "失败详情"]])
            else:
                print("\n✅ 所有 URL 全部通过验证！")

        self.results = self.df
        return self.df

    def get_failed_urls(self) -> List[str]:
        """返回所有验证失败的 URL 列表"""
        if self.results is None:
            raise ValueError("请先调用 verify() 方法")
        failed_urls = []
        for idx, row in self.results.iterrows():
            if row["验证状态"] == "存在失败":
                # 从失败详情解析出 URL（格式："url: 原因 | url: 原因"）
                details = row["失败详情"]
                if details and details != "全部成功":
                    for part in details.split(" | "):
                        url = part.split(":", 1)[0].strip()
                        failed_urls.append(url)
        return failed_urls

    def run(self,verbose = True):
        return self.verify(verbose)


class File:
    """Site-scoped persistence service for crawler inputs, caches and exports."""

    def __init__(self, config):
        self.config = config
        self.base_site = config.site


        self.Web = WebPValidator



    @staticmethod
    def create_dir(file_path):
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    def path_add_site(self, file_path):
        p = Path(file_path)
        prefix = f'{self.base_site}_' if self.base_site else ''
        if prefix and not p.name.startswith(prefix):
            p = p.with_name(f"{self.base_site}_{p.name}")
        self.create_dir(p)
        return p

    @staticmethod
    def _empty_or_default(default):
        return {} if default is _MISSING else deepcopy(default)

    def load_json(self, file_path, default=_MISSING, *, strict=False):
        """Load site-scoped JSON; missing files retain the historical ``{}`` default."""
        fp = Path(file_path)
        self.create_dir(fp)
        if not fp.exists():
            print(f"[提示] 文件不存在，按空数据返回：{fp}")
            return self._empty_or_default(default)
        try:
            with fp.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[错误] 加载 JSON 失败：{fp}, {exc}")
            if strict:
                raise
            return self._empty_or_default(default)

    def save_json(self, data, path):
        fp = self.path_add_site(path)
        temp_path = None
        try:
            with NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=fp.parent,
                prefix=f'.{fp.name}.', suffix='.tmp', delete=False,
            ) as temp:
                temp_path = Path(temp.name)
                json.dump(data, temp, ensure_ascii=False, indent=4)
            os.replace(temp_path, fp)
            return fp
        except (OSError, TypeError, ValueError) as exc:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise OSError(f'Failed to save JSON: {fp}') from exc

    def save_csv(self, data, path, columns=None):
        fp = self.path_add_site(path)
        temp_path = None
        try:
            with NamedTemporaryFile(
                mode='w', encoding='utf-8-sig', newline='', dir=fp.parent,
                prefix=f'.{fp.name}.', suffix='.tmp', delete=False,
            ) as temp:
                temp_path = Path(temp.name)
                df = pd.DataFrame(data)
                df = df.replace('\x00', '', regex=True)
                df.to_csv(temp, index=False, columns=columns)
            os.replace(temp_path, fp)
            return fp
        except (OSError, ValueError, TypeError) as exc:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise OSError(f'Failed to save CSV: {fp}') from exc

    def read_csv(self, data=None, path=None, **kwargs):
        """Create a DataFrame from in-memory data or load a site-scoped CSV."""
        if data is not None and path is not None:
            raise ValueError('Provide either data or path, not both.')
        if data is not None:
            return pd.DataFrame(data)
        if path is None:
            raise ValueError('Missing data or path.')
        try:
            return pd.read_csv(self.path_add_site(path), encoding='utf-8-sig', **kwargs)
        except (OSError, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            raise OSError(f'Failed to read CSV: {path}') from exc

    def _res_prefix(self, name):
        st = self.config.site_type or ""
        prefix = f"{st}_" if st else ""
        return f"res/{prefix}{name}"

    def dz_path(self):
        n = int((1 - (self.config.zk or 0)) * 100)
        return self.path_add_site(self._res_prefix(f"{n}%off_ljp.csv"))

    def fl_path(self):
        return self.path_add_site(self._res_prefix("col_ljp.csv"))





    @staticmethod
    def json_ls_del(data:list[dict],targe='url'):

        df = deepcopy(data)
        for row in df:
            row.pop(targe,None)

        return df
