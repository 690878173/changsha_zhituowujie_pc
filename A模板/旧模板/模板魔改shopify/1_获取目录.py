"""
阶段1: 发现店铺 + 构建分类目录
运行: uv run python 1_获取目录.py
"""
import re
from typing import TYPE_CHECKING
from urllib.parse import unquote, urljoin

import html as html_lib
from lxml import html

from config import Tool, site_config, resume, run_mode, sample_limit, full_threshold
from storefront_engine import StorefrontEngine

# 引用 Tool.Shopify 上的工具
clean_text = Tool.Shopify.clean_text
slug = Tool.Shopify.slug
unique = Tool.Shopify.unique
cumulative_key = Tool.Shopify.cumulative_key
PAGE_SIZE = Tool.Shopify.PAGE_SIZE


# ═══ 阶段1: 发现站点配置 ═══

def discover(engine: StorefrontEngine, count_products: bool = True) -> dict:
    Tool.print("阶段1: 发现站点配置...", "cyan")
    src = engine.request_page(engine.site["home_url"]).text or ""
    engine.home_html = src
    engine.store_domain, engine.token, ts = engine._extract_config(src)
    if not engine.store_domain:
        raise RuntimeError("store_domain_not_found")
    if not engine.token:
        raise RuntimeError("storefront_token_not_found:在config.toml手动填写")

    version = clean_text(engine.site.get("api_version", "2026-04"))
    hosts = unique([
        h.rstrip("/") + f"/api/{version}/graphql.json"
        for h in [engine.site["base_url"], "https://" + engine.store_domain]
    ])
    for c in hosts:
        try:
            d = engine._gql_at(
                c,
                """query H @inContext(country: CO, language: LA) {
                  shop { name paymentSettings { currencyCode } }
                  products(first: 1) { nodes { handle } } }"""
                .replace("CO", "COUNTRY_CODE").replace("LA", "LANGUAGE_CODE"),
            )
            engine.api_url = c
            engine.shop_info = d.get("shop") or {}
            break
        except Exception:
            continue
    if not engine.api_url:
        raise RuntimeError("graphql_endpoint_not_found")

    pc = engine._count_products() if count_products else None
    cc = clean_text(((engine.shop_info.get("paymentSettings") or {}).get("currencyCode")))
    ec = clean_text(engine.site["currency"]).upper()
    if cc and cc != ec:
        raise RuntimeError(f"currency_mismatch:{ec}!={cc}")

    runtime = {
        "site_name": engine.site["site_name"],
        "base_url": engine.site["base_url"],
        "store_domain": engine.store_domain,
        "api_url": engine.api_url,
        "api_version": version,
        "token_source": ts,
        "currency": ec,
        "shop": engine.shop_info,
        "product_count": pc,
    }
    Tool.File.save_json(runtime, engine._data("json_data/storefront_runtime.json"))
    Tool.print(f"站点={engine.site['site_name']} 商品={pc} 币种={ec}", "green")
    return runtime


# ═══ 阶段1: 构建分类目录 ═══

def _nav_from_html(engine: StorefrontEngine, vbh: dict) -> tuple[list, list]:
    try:
        root = html.fromstring(engine.home_html)
    except Exception:
        return [], [{"reason": "homepage_parse_failed"}]
    xp = engine.site.get("navigation_xpath") or (
        "//header//nav//a[contains(@href, '/collections/')] | "
        "//*[@role='navigation']//a[contains(@href, '/collections/')]"
    )
    entries, rej, seen = [], [], set()
    for a in root.xpath(xp):
        href = a.get("href") or ""
        try:
            hv = engine._col_handle(urljoin(engine.site["base_url"] + "/", href))
        except RuntimeError:
            continue
        col = vbh.get(hv)
        if not col:
            rej.append({"url": href, "reason": "not_valid"})
            continue
        leaf = clean_text(" ".join(a.itertext())) or col["title"]
        if len(leaf) > 100 or re.search(r"\b(shop now|learn more)\b", leaf, flags=re.I):
            rej.append({"url": href, "title": leaf, "reason": "marketing"})
            continue
        parts = []
        sm = a.xpath(
            "ancestor::*[contains(concat(' ', normalize-space(@class), ' '), "
            "' header__sub-menu-item ')][1]"
        )
        if sm:
            rt = re.sub(r"\s+submenu\s*$", "", clean_text(sm[0].get("aria-label")), flags=re.I)
            if rt:
                parts.append(rt)
        sub = a.xpath("ancestor::*[starts-with(@id, 'submenu-')][1]")
        if sub and not parts:
            trig = root.xpath(f"//*[@aria-controls='{sub[0].get('id')}'][1]")
            if trig:
                rt = clean_text(" ".join(trig[0].itertext()))
                if rt:
                    parts.append(rt)
        nav = a.xpath("ancestor::nav[1]")
        if nav:
            lid = nav[0].get("aria-labelledby")
            if lid:
                lbl = root.xpath(f"//*[@id='{lid}'][1]")
                gt = clean_text(" ".join(lbl[0].itertext())) if lbl else ""
                if re.fullmatch(r"(?:main\s+)?(?:desktop\s+)?(?:menu|navigation)", gt, flags=re.I):
                    gt = ""
                if gt and (not parts or gt.casefold() != parts[-1].casefold()):
                    parts.append(gt)
        if not parts:
            parts.append(leaf)
        elif leaf.casefold() != parts[-1].casefold():
            parts.append(leaf)
        key = cumulative_key(parts)
        if key and (key, hv) not in seen:
            seen.add((key, hv))
            entries.append({
                "key": key, "title": leaf, "handle": hv,
                "url": col["url"], "source": "nav",
            })
    return entries, rej


def _menu_entries(engine: StorefrontEngine, hv: str, vbh: dict) -> tuple[list, dict]:
    q = """query M($handle: String!) { menu(handle: $handle) { title handle
      items { title type url resource { ... on Collection { title handle onlineStoreUrl } }
        items { title type url resource { ... on Collection { title handle onlineStoreUrl } }
          items { title type url resource { ... on Collection { title handle onlineStoreUrl } } } } } }"""
    try:
        menu = (engine.graphql(q, {"handle": hv}) or {}).get("menu")
    except Exception as e:
        return [], {"handle": hv, "accepted": False, "reason": str(e)}
    if not menu:
        return [], {"handle": hv, "accepted": False, "reason": "menu_not_found"}

    entries = []

    def walk(items, parents):
        for item in items or []:
            t = clean_text(item.get("title"))
            r = item.get("resource") or {}
            hf = clean_text(r.get("handle"))
            if not hf:
                try:
                    hf = engine._col_handle(item.get("url"))
                except RuntimeError:
                    hf = ""
            col = vbh.get(hf)
            cur = parents + ([t] if t else [])
            if col and t:
                entries.append({
                    "key": cumulative_key(cur), "title": t, "handle": hf,
                    "url": col["url"], "source": f"menu:{hv}",
                })
            walk(item.get("items") or [], cur)

    walk(menu.get("items") or [], [])
    entries = unique(entries)
    ok = len({e["handle"] for e in entries}) >= 2
    return (entries if ok else []), {"handle": hv, "accepted": ok, "reason": "accepted" if ok else "too_few"}


def build_catalog(engine: StorefrontEngine) -> dict:
    """构建分类目录，输出 data.json"""
    if not engine.home_html:
        discover(engine, count_products=False)

    # 获取所有非空集合
    q = """query Cols($first: Int!, $after: String) @inContext(country: COUNTRY_CODE, language: LANGUAGE_CODE) {
      collections(first: $first, after: $after) {
        nodes { title handle onlineStoreUrl products(first: 1) { nodes { handle } } }
        pageInfo { hasNextPage endCursor } } }"""
    raw, after = [], None
    while True:
        d = engine.graphql(q, {"first": PAGE_SIZE, "after": after})
        conn = d.get("collections") or {}
        raw.extend(conn.get("nodes") or [])
        pi = conn.get("pageInfo") or {}
        if not pi.get("hasNextPage"):
            break
        after = pi.get("endCursor")
        if not after:
            raise RuntimeError("missing_collection_cursor")
        engine.pause()

    excludes = [re.compile(p, re.I) for p in engine.site.get("exclude_collection_patterns") or []]
    valid, skipped, seen = [], [], set()
    for node in raw:
        title = clean_text(node.get("title"))
        hv = clean_text(node.get("handle"))
        has_prod = bool(((node.get("products") or {}).get("nodes") or []))
        reason = ""
        if not title:
            reason = "missing_title"
        elif not hv or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", hv):
            reason = "invalid_handle"
        elif hv in seen:
            reason = "duplicate_handle"
        elif not has_prod:
            reason = "empty_collection"
        elif any(p.search(title) or p.search(hv) for p in excludes):
            reason = "excluded"
        url = engine._norm_col_url(node.get("onlineStoreUrl"), hv)
        if not reason and not url:
            reason = "missing_url"
        item = {"title": title, "handle": hv, "url": url}
        if reason:
            item["reason"] = reason
            skipped.append(item)
        else:
            seen.add(hv)
            valid.append(item)

    if not valid:
        raise RuntimeError("no_valid_nonempty_collections")
    vbh = {it["handle"]: it for it in valid}

    # 导航分析
    nav_entries, nav_rej = _nav_from_html(engine, vbh)
    menu_entries, menu_reports = [], []
    for mh in engine.site.get("menu_handles") or []:
        ent, rep = _menu_entries(engine, clean_text(mh), vbh)
        menu_entries.extend(ent)
        menu_reports.append(rep)

    # 合并目录
    catalog, used, rej = {}, set(), []
    for entry in nav_entries + menu_entries:
        if entry["handle"] in used:
            continue
        if entry["key"] in catalog and catalog[entry["key"]] != entry["url"]:
            rej.append({**entry, "reason": "dup_key"})
            continue
        catalog[entry["key"]] = entry["url"]
        used.add(entry["handle"])
    tk = {clean_text(k.split(",")[-1]).casefold() for k in catalog}
    for col in valid:
        if col["handle"] in used:
            continue
        k = col["title"]
        if k.casefold() in tk or k in catalog:
            continue
        catalog[k] = col["url"]
        tk.add(k.casefold())
        used.add(col["handle"])

    Tool.File.save_json(catalog, engine._data("json_data/data.json"))
    Tool.File.save_json(
        {"nav": nav_entries, "menu_reports": menu_reports,
         "valid": valid, "skipped": skipped, "rejected": rej},
        engine._data("json_data/catalog_candidates.json"),
    )
    Tool.print(f"目录={len(catalog)} 导航={len(nav_entries)} 集合={len(valid)}", "green")
    return catalog


# ═══ main ═══

def main():
    engine = StorefrontEngine()
    runtime = discover(engine, count_products=True)
    inventory = int(runtime.get("product_count") or 0)
    # 判断 scope
    if run_mode == "sample":
        sample = True
        limit = sample_limit
    elif run_mode == "full":
        sample = False
        limit = 0
    else:  # auto
        sample = inventory > full_threshold
        limit = sample_limit if sample else 0
    scope = f"sample({limit})" if sample else "full"
    Tool.print(f"run_mode={run_mode} scope={scope} inventory={inventory}")

    catalog = build_catalog(engine)
    Tool.print(
        f"阶段1完成 catalog={len(catalog)} inventory={inventory} "
        f"next=2_获取商品URL.py scope={scope}",
        "green",
    )


if __name__ == "__main__":
    main()
