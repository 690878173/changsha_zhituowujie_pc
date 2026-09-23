"""
Shopify Storefront 通用工具类
挂载到 Tool.Shopify 上使用: Tool.Shopify.clean_text(...) 等
"""
from __future__ import annotations

import hashlib
import html as html_lib
import json
import re
from urllib.parse import parse_qsl, unquote, urljoin, urlparse, urlunparse

from lxml import etree, html

# ═══ 常量 ═══
PAGE_SIZE = 250

STANDARD_FIELDS = [
    "Type", "SKU", "Name", "Description", "Sale price", "Regular price",
    "Categories", "Tags", "Images", "Parent",
    "Attribute 1 name", "Attribute 1 value(s)", "Attribute 2 name", "Attribute 2 value(s)",
    "Attribute 3 name", "Attribute 3 value(s)", "Attribute 4 name", "Attribute 4 value(s)",
    "brand", "Stock", "is_upload",
]

CHALLENGE_MARKERS = (
    "cf-chl-", "cloudflare ray id", "verify you are human",
    "attention required", "/cdn-cgi/challenge-platform/",
    "challenges.cloudflare.com", "<title>just a moment",
)

# ═══ GraphQL 模板 ═══
VARIANT_PAGE_QUERY = """
query V($handle: String!, $after: String) @inContext(country: COUNTRY_CODE, language: LANGUAGE_CODE) {
  product(handle: $handle) {
    variants(first: 250, after: $after) {
      nodes { id sku title availableForSale selectedOptions { name value }
        price { amount currencyCode } compareAtPrice { amount currencyCode }
        image { url altText } }
      pageInfo { hasNextPage endCursor } } } }
"""

IMAGE_PAGE_QUERY = """
query I($handle: String!, $after: String) @inContext(country: COUNTRY_CODE, language: LANGUAGE_CODE) {
  product(handle: $handle) {
    images(first: 250, after: $after) {
      nodes { url altText } pageInfo { hasNextPage endCursor } } } }
"""

PRODUCT_QUERY_TMPL = """
query P($handle: String!) @inContext(country: COUNTRY_CODE, language: LANGUAGE_CODE) {
  product(handle: $handle) {
    id title handle vendor descriptionHtml productType tags onlineStoreUrl
    options { name values } seo { title description }
    METAFIELD_SELECTION
    images(first: 250) { nodes { url altText } pageInfo { hasNextPage endCursor } }
    variants(first: 250) {
      nodes { id sku title availableForSale selectedOptions { name value }
        price { amount currencyCode } compareAtPrice { amount currencyCode }
        image { url altText } }
      pageInfo { hasNextPage endCursor } } } }"""


# ═══ 工具函数 ═══

def clean_text(v):
    t = html_lib.unescape(str(v or ""))
    return re.sub(r"\s+", " ", t.replace("\u200b", "").replace("\ufeff", "")).strip()


def money(v):
    t = clean_text(v).replace(",", "")
    if not t:
        return ""
    try:
        return f"{float(t):.2f}"
    except ValueError:
        return ""


def slug(v):
    t = re.sub(r"[^a-z0-9]+", "-", clean_text(v).lower()).strip("-")
    return t or "item"


def match_key(v):
    t = clean_text(v).casefold().replace("\u00ae", "").replace("\u2122", "").replace("\u00a9", "")
    return re.sub(r"[^a-z0-9]+", "", t)


def unique(xs):
    r, s = [], set()
    for x in xs:
        m = json.dumps(x, sort_keys=True, ensure_ascii=False) if isinstance(x, (dict, list)) else str(x)
        if m not in s:
            s.add(m)
            r.append(x)
    return r


def stable_parent_key(handle_val, reserved=()):
    ht = clean_text(handle_val)
    base = f"parent--{slug(ht)}"
    rs = {clean_text(v) for v in reserved if clean_text(v)}
    if base not in rs:
        return base
    d = hashlib.sha256(ht.encode()).hexdigest()
    for n in range(8, len(d) + 1, 4):
        c = f"{base}--{d[:n]}"
        if c not in rs:
            return c
    raise RuntimeError(f"parent_key_collision:{ht}")


def cumulative_key(parts):
    cl = [clean_text(p) for p in parts if clean_text(p)]
    if len(cl) > 3:
        cl = [cl[0], cl[1], " ".join(cl[2:])]
    cur, res = [], []
    for p in cl[:3]:
        cur.append(p)
        res.append(" ".join(cur))
    return ",".join(res)


def clean_html_fragment(v):
    src = html_lib.unescape(str(v or "")).strip()
    if not src:
        return ""
    try:
        root = html.fragment_fromstring(src, create_parent="div")
    except (etree.ParserError, ValueError):
        return clean_text(re.sub(r"https?://\S+", "", re.sub(r"<[^>]+>", " ", src)))
    for n in root.xpath(".//script|.//style|.//select|.//option|.//button|.//form|.//iframe|.//svg|.//img|.//noscript"):
        n.drop_tree()
    for n in root.xpath(".//a"):
        n.drop_tag()
    for n in root.iter():
        for a in list(n.attrib):
            if a.lower() in {"href", "src", "style"} or a.lower().startswith("on"):
                del n.attrib[a]
    s = "".join(etree.tostring(c, encoding="unicode", method="html") for c in root)
    return re.sub(r"\s+", " ", re.sub(r"https?://[^\s\"'<>]+", "", s, flags=re.I)).strip()


def inner_html(node):
    return (node.text or "") + "".join(etree.tostring(c, encoding="unicode", method="html") for c in node)


def portable_text_to_html(v):
    if isinstance(v, dict) and isinstance(v.get("content"), list):
        v = v["content"]
    if isinstance(v, str):
        return clean_html_fragment(v)
    if not isinstance(v, list):
        return ""
    frags, al = [], ""
    for b in v:
        if not isinstance(b, dict):
            continue
        parts = []
        for child in b.get("children") or []:
            if not isinstance(child, dict):
                continue
            t = clean_text(child.get("text"))
            if not t:
                continue
            esc = html_lib.escape(t, quote=False)
            marks = {clean_text(m).lower() for m in child.get("marks") or []}
            if marks & {"strong", "bold"}:
                esc = f"<strong>{esc}</strong>"
            if marks & {"em", "emphasis", "italic"}:
                esc = f"<em>{esc}</em>"
            parts.append(esc)
        cnt = "".join(parts)
        if not cnt:
            continue
        li = clean_text(b.get("listItem")).lower()
        if li:
            tag = "ol" if li in {"number", "numbered", "ordered"} else "ul"
            if al != tag:
                if al:
                    frags.append(f"</{al}>")
                frags.append(f"<{tag}>")
                al = tag
            frags.append(f"<li>{cnt}</li>")
            continue
        if al:
            frags.append(f"</{al}>")
            al = ""
        sty = clean_text(b.get("style")).lower()
        tag = sty if re.fullmatch(r"h[1-6]", sty) else "blockquote" if sty == "blockquote" else "p"
        frags.append(f"<{tag}>{cnt}</{tag}>")
    if al:
        frags.append(f"</{al}>")
    return clean_html_fragment("".join(frags))


def detail_record_key(row):
    return clean_text(row.get("handle")) or clean_text(row.get("url"))


def upsert_detail_record(rows, row):
    m = detail_record_key(row)
    r = [it for it in rows if isinstance(it, dict) and detail_record_key(it) != m]
    r.append(dict(row))
    return r


def is_skippable_failure(v):
    reason = clean_text(v.get("reason")) if isinstance(v, dict) else clean_text(v)
    lowered = reason.casefold()
    return "http_status:404" in lowered or "product_not_found:" in lowered


# ═══ Remix 解码器 ═══

class RemixSingleFetchDecoder:
    def __init__(self, source):
        lines = [l for l in (source or "").splitlines() if l.strip()]
        if not lines:
            raise RuntimeError("remix_data_empty")
        try:
            init = json.loads(lines[0])
        except json.JSONDecodeError as e:
            raise RuntimeError(f"remix_initial_invalid:{e}") from e
        if not isinstance(init, list):
            raise RuntimeError("remix_payload_not_list")
        self.table = list(init)
        self.n0 = len(self.table)
        self.pt, self.memo, self.active = {}, {}, set()
        for line in lines[1:]:
            m = re.match(r"^P(\d+):(.*)$", line, flags=re.S)
            if not m:
                continue
            try:
                p = json.loads(m.group(2))
            except json.JSONDecodeError as e:
                raise RuntimeError(f"remix_promise_invalid:{m.group(1)}:{e}") from e
            if isinstance(p, list):
                self.pt[int(m.group(1))] = len(self.table)
                self.table.extend(p)
            else:
                self.pt[int(m.group(1))] = p

    def decode_ref(self, ref):
        if ref < 0:
            return None
        if ref >= len(self.table):
            raise RuntimeError(f"remix_ref_oob:{ref}")
        if ref in self.memo:
            return self.memo[ref]
        if ref in self.active:
            return None
        self.active.add(ref)
        val = self.decode_value(self.table[ref])
        self.active.remove(ref)
        self.memo[ref] = val
        return val

    def decode_value(self, val):
        if isinstance(val, dict):
            r = {}
            for ek, ev in val.items():
                k = self.decode_ref(int(ek[1:])) if ek.startswith("_") and ek[1:].isdigit() else ek
                r[str(k)] = self.decode_ref(ev) if isinstance(ev, int) else self.decode_value(ev)
            return r
        if isinstance(val, list):
            if len(val) == 2 and val[0] == "P" and isinstance(val[1], int):
                t = self.pt.get(val[1])
                return self.decode_ref(t) if isinstance(t, int) and t >= 0 else None
            return [self.decode_ref(i) if isinstance(i, int) else self.decode_value(i) for i in val]
        return val

    def find_field(self, name):
        for item in self.table[:self.n0]:
            if not isinstance(item, dict):
                continue
            for ek, ev in item.items():
                k = self.decode_ref(int(ek[1:])) if ek.startswith("_") and ek[1:].isdigit() else ek
                if k == name:
                    return self.decode_ref(ev) if isinstance(ev, int) else self.decode_value(ev)
        return None


# ═══ 挂在 Tool 上的聚合类 ═══

class ShopifyCommon:
    """Shopify 通用工具，挂载为 Tool.Shopify"""

    def __init__(self, tool):
        self.tool = tool

    # ── 文本/价格 ──
    clean_text = staticmethod(clean_text)
    money = staticmethod(money)
    slug = staticmethod(slug)
    match_key = staticmethod(match_key)

    # ── 集合/去重 ──
    unique = staticmethod(unique)
    stable_parent_key = staticmethod(stable_parent_key)
    cumulative_key = staticmethod(cumulative_key)

    # ── HTML 清洗 ──
    clean_html_fragment = staticmethod(clean_html_fragment)
    inner_html = staticmethod(inner_html)
    portable_text_to_html = staticmethod(portable_text_to_html)

    # ── 记录/失败 ──
    detail_record_key = staticmethod(detail_record_key)
    upsert_detail_record = staticmethod(upsert_detail_record)
    is_skippable_failure = staticmethod(is_skippable_failure)

    # ── 常量 ──
    PAGE_SIZE = PAGE_SIZE
    STANDARD_FIELDS = STANDARD_FIELDS
    CHALLENGE_MARKERS = CHALLENGE_MARKERS

    # ── GraphQL ──
    VARIANT_PAGE_QUERY = VARIANT_PAGE_QUERY
    IMAGE_PAGE_QUERY = IMAGE_PAGE_QUERY
    PRODUCT_QUERY_TMPL = PRODUCT_QUERY_TMPL

    # ── Remix ──
    RemixSingleFetchDecoder = RemixSingleFetchDecoder
