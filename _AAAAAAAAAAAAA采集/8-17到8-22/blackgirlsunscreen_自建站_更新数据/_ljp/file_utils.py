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

    def verify(self, verbose=True):
        # 构建 URL 到行索引列表的映射
        url_to_rows = {}
        for idx, row in self.df.iterrows():
            cell = row.get(self.column_name)
            if pd.isna(cell) or not cell:
                continue
            urls = [u.strip() for u in str(cell).split(self.separator) if u.strip()]
            for url in urls:
                if url not in url_to_rows:
                    url_to_rows[url] = []
                url_to_rows[url].append(idx)

        # 生成唯一 URL 列表
        unique_urls = list(url_to_rows.keys())
        if verbose:
            print(f"原始 URL 数: {sum(len(v) for v in url_to_rows.values())}，去重后: {len(unique_urls)}")

        # 构建任务（仅对唯一 URL 进行验证）
        tasks = [(0, url) for url in unique_urls]  # 行索引占位，实际用不到

        # 执行异步验证，返回结果列表 [(0, url, valid, msg), ...]
        raw_results = asyncio.run(self._run_async_verify(tasks))

        # 将结果映射到每个 URL
        url_result = {url: (valid, msg) for _, url, valid, msg in raw_results}

        # 回写到 DataFrame
        self.df["验证状态"] = ""
        self.df["失败详情"] = ""
        for idx, row in self.df.iterrows():
            # 获取该行的 URL 列表
            urls = [u.strip() for u in str(row.get(self.column_name)).split(self.separator) if u.strip()]
            if not urls:
                self.df.at[idx, "验证状态"] = "无URL"
                continue
            all_ok = True
            fail_msgs = []
            for url in urls:
                if url and str(url) != 'nan' and not pd.isna(url):
                    valid, msg = url_result.get(url, (False, "未验证"))
                    if not valid:
                        all_ok = False
                        fail_msgs.append(f"{url}: {msg}")
            self.df.at[idx, "验证状态"] = "全部通过" if all_ok else "存在失败"
            self.df.at[idx, "失败详情"] = " | ".join(fail_msgs) if fail_msgs else "全部成功"

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

    def run(self,save_path,verbose = True, only_failed: bool = True):
        df_all = self.verify(verbose)
        if only_failed:
            df_failed = df_all[df_all["验证状态"] == "存在失败"]

        else:
            df_failed = df_all
        if len(df_failed) > 0:
            print(f'存在失败链接,数量:{len(df_failed)}')
            with pd.option_context('display.max_rows', None,  # 显示所有行
                                   'display.max_columns', None,
                                   'display.max_colwidth', None):  # 显示所有列
                print(df_failed[['SKU', '失败详情']])
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            df_failed.to_csv(save_path, index=False)
        else:
            print(f'全部url通过验证')




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
