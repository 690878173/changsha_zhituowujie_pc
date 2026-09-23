"""
Shopify Storefront GraphQL 核心引擎
仅包含：http/graphql、配置提取、URL规范化、分类产品抓取
"""
from __future__ import annotations

import json
import random
import re
import time
from urllib.parse import unquote, urljoin, urlparse

import html as html_lib
from curl_cffi import requests as curl_requests

from config import site_config, Tool

from shopify_tool import (
    clean_text, CHALLENGE_MARKERS, PAGE_SIZE,
)


class StorefrontEngine:
    """Shopify Storefront GraphQL 核心引擎 — 不含阶段逻辑"""

    def __init__(self):
        self.site = site_config
        self.token = clean_text(self.site.get("storefront_token"))
        self.store_domain = clean_text(self.site.get("store_domain"))
        self.api_url = ""
        self.shop_info = {}
        self.home_html = ""
        self.delay_range = tuple(self.site.get("request_delay_range", [0.15, 0.35]))
        self.gql_session = curl_requests.Session()

    def pause(self):
        time.sleep(random.uniform(*self.delay_range))

    # ── 文件路径 ──
    def _data(self, rel):
        return Tool.File.path_add_site(rel)

    # ── HTTP 请求 ──
    def request_page(self, url, **kw):
        """使用 Tool 的 session 请求页面，返回 curl_cffi Response"""
        res = Tool.get(url, **kw)
        if not res:
            raise RuntimeError(f"request_failed:{url}")
        body = res.text or ""
        if res.status_code in {403, 429} or any(m in body.lower() for m in CHALLENGE_MARKERS):
            raise RuntimeError(f"blocked:{res.status_code}:{url}")
        if res.status_code >= 400:
            raise RuntimeError(f"http_status:{res.status_code}:{url}")
        return res

    def _request(self, method, url, **kw):
        """通用 HTTP 请求（获取 HTML、Remix data 等）"""
        headers = {
            "accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
            ),
        }
        headers.update(kw.pop("headers", {}) or {})
        for attempt in range(3):
            try:
                resp = self.gql_session.request(method, url, headers=headers, timeout=30, **kw)
                body = resp.text or ""
                if resp.status_code in {403, 429} or any(m in body.lower() for m in CHALLENGE_MARKERS):
                    raise RuntimeError(f"blocked:{resp.status_code}:{url}")
                if resp.status_code >= 500:
                    if attempt < 2:
                        time.sleep(min(8.0, (attempt + 1) * 1.5))
                        continue
                    raise RuntimeError(f"http_status:{resp.status_code}:{url}")
                if resp.status_code >= 400:
                    raise RuntimeError(f"http_status:{resp.status_code}:{url}")
                return resp
            except RuntimeError:
                raise
            except Exception as e:
                if attempt == 2:
                    raise RuntimeError(f"request_failed:{url}:{e}")
                time.sleep(min(8.0, (attempt + 1) * 1.5))

    # ── GraphQL ──
    def graphql(self, query, variables=None):
        if not self.api_url:
            raise RuntimeError("api_url_not_set")
        for attempt in range(3):
            try:
                resp = self.gql_session.post(
                    self.api_url,
                    headers={
                        "content-type": "application/json",
                        "accept": "application/json",
                        "x-shopify-storefront-access-token": self.token,
                    },
                    json={"query": self._ctx(query), "variables": variables or {}},
                    timeout=30,
                )
                p = resp.json()
                if p.get("errors"):
                    raise RuntimeError("graphql_errors:" + json.dumps(p["errors"], ensure_ascii=False)[:1500])
                return p.get("data") or {}
            except RuntimeError:
                raise
            except Exception as e:
                if attempt >= 2:
                    raise RuntimeError(f"graphql_failed:{e}") from e
                time.sleep(min(4.0, attempt * 1.5))

    def _ctx(self, q):
        c = re.sub(r"[^A-Z]", "", clean_text(self.site["country"]).upper()) or "US"
        l = re.sub(r"[^A-Z]", "", clean_text(self.site["language"]).upper()) or "EN"
        return q.replace("COUNTRY_CODE", c).replace("LANGUAGE_CODE", l)

    def _gql_at(self, url, q, v=None):
        saved = self.api_url
        self.api_url = url
        try:
            return self.graphql(q, v)
        finally:
            self.api_url = saved

    # ── 配置提取 ──
    def _extract_config(self, src):
        d = html_lib.unescape(src or "")
        domain, token, ts = self.store_domain, self.token, "config" if self.token else ""
        if not domain:
            for p in [
                r"Shopify\.shop\s*=\s*['\"]([^'\"]+\.myshopify\.com)['\"]",
                r"([A-Za-z0-9][A-Za-z0-9-]*\.myshopify\.com)",
            ]:
                m = re.search(p, d, flags=re.I | re.S)
                if m:
                    domain = clean_text(m.group(1)).lower()
                    break
        if not token:
            for n, p in [
                ("STOREFRONT_ACCESS_TOKEN", r"(?:window\.)?STOREFRONT_ACCESS_TOKEN\s*=\s*['\"]([^'\"]+)"),
                ("PUBLIC_STOREFRONT_API_TOKEN", r"PUBLIC_STOREFRONT_API_TOKEN.{0,100}?([A-Za-z0-9_-]{16,})"),
                ("storefrontAccessToken", r"storefrontAccessToken.{0,120}?([A-Za-z0-9_-]{16,})"),
            ]:
                m = re.search(p, d, flags=re.I | re.S)
                if m:
                    token = clean_text(m.group(1)).replace("\\", "")
                    ts = n
                    break
        return domain, token, ts

    def _count_products(self):
        q = """query C($first: Int!, $after: String) @inContext(country: COUNTRY_CODE, language: LANGUAGE_CODE) {
          products(first: $first, after: $after) { nodes { handle } pageInfo { hasNextPage endCursor } } }"""
        cnt, after = 0, None
        while True:
            d = self.graphql(q, {"first": PAGE_SIZE, "after": after})
            conn = d.get("products") or {}
            cnt += len(conn.get("nodes") or [])
            pi = conn.get("pageInfo") or {}
            if not pi.get("hasNextPage"):
                return cnt
            after = pi.get("endCursor")
            if not after:
                raise RuntimeError("missing_product_count_cursor")
            self.pause()

    # ── URL 规范化 ──
    def _norm_col_url(self, v="", hv=""):
        raw = html_lib.unescape(str(v or "")).replace("\\/", "/").strip()
        if raw:
            parts = [unquote(p) for p in urlparse(urljoin(self.site["base_url"] + "/", raw)).path.split("/") if p]
            if len(parts) >= 2 and parts[0] == "collections":
                hv = parts[1]
        hv = clean_text(hv)
        return f"{self.site['base_url']}/collections/{hv}" if hv else ""

    def _norm_prod_url(self, v="", hv=""):
        raw = html_lib.unescape(str(v or "")).replace("\\/", "/").strip()
        if raw:
            parts = [unquote(p) for p in urlparse(urljoin(self.site["base_url"] + "/", raw)).path.split("/") if p]
            if len(parts) >= 2 and parts[0] == "products":
                hv = parts[1]
        hv = clean_text(hv)
        return f"{self.site['base_url']}/products/{hv}" if hv else ""

    def _col_handle(self, url):
        parts = [unquote(p) for p in urlparse(str(url or "")).path.split("/") if p]
        if len(parts) >= 2 and parts[0] == "collections":
            return parts[1]
        raise RuntimeError(f"not_collection_url:{url}")

    # ── 分类产品抓取（阶段2用）──
    def _fetch_coll_products(self, coll_url, limit=0, max_pages=10):
        hv = self._col_handle(coll_url)
        q = """query CP($handle: String!, $first: Int!, $after: String) @inContext(country: COUNTRY_CODE, language: LANGUAGE_CODE) {
          collection(handle: $handle) {
            title handle products(first: $first, after: $after) {
              nodes { handle onlineStoreUrl } pageInfo { hasNextPage endCursor } } } }"""
        result, seen, after = [], set(), None
        for _pt in range(1, max_pages + 1):
            ps = max(1, min(PAGE_SIZE, limit - len(result))) if limit else PAGE_SIZE
            d = self.graphql(q, {"handle": hv, "first": ps, "after": after})
            coll = d.get("collection")
            if not coll:
                raise RuntimeError(f"collection_not_found:{hv}")
            for prod in (coll.get("products") or {}).get("nodes") or []:
                url = self._norm_prod_url(prod.get("onlineStoreUrl"), prod.get("handle"))
                if url and url not in seen:
                    seen.add(url)
                    result.append(url)
                    if limit and len(result) >= limit:
                        return result
            pi = (coll.get("products") or {}).get("pageInfo") or {}
            if not pi.get("hasNextPage"):
                return result
            after = pi.get("endCursor")
            if not after:
                raise RuntimeError(f"missing_cursor:{hv}")
            self.pause()
        return result
