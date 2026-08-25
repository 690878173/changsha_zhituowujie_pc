"""
阶段3: 抓取商品详情 + 校验
运行: uv run python 3_获取详情页数据.py
依赖: 需先运行 1_获取目录.py 和 2_获取商品URL.py
"""
from __future__ import annotations
import csv, hashlib, json, re
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urljoin, urlparse, urlunparse
from lxml import html as lxml_html
from config import Tool, resume, run_mode, sample_limit, full_threshold
from storefront_engine import StorefrontEngine
from shopify_tool import (
    clean_text, money, slug, match_key, unique, stable_parent_key,
    clean_html_fragment, inner_html, portable_text_to_html,
    detail_record_key, upsert_detail_record, is_skippable_failure,
    STANDARD_FIELDS, VARIANT_PAGE_QUERY, IMAGE_PAGE_QUERY, PRODUCT_QUERY_TMPL,
    RemixSingleFetchDecoder,
)

DRK = detail_record_key; URD = upsert_detail_record; ISF = is_skippable_failure


# ═══ 产品字段处理 ═══

def _product_query(site: dict) -> str:
    ids = []; custom = site.get("custom_fields") or []
    for f in custom:
        mf = f.get("metafield") or {}
        ns, k = clean_text(mf.get("namespace")), clean_text(mf.get("key"))
        if ns and k and re.fullmatch(r"[A-Za-z0-9_.-]+", ns) and re.fullmatch(r"[A-Za-z0-9_.-]+", k):
            ids.append((ns, k))
    sel = ",".join(f'{{namespace: "{n}", key: "{k}"}}' for n, k in unique(ids)) if ids else ""
    mf_block = f"metafields(identifiers: [{sel}]) {{ namespace key type value }}" if sel else ""
    return PRODUCT_QUERY_TMPL.replace("METAFIELD_SELECTION", mf_block)


def _real_options(product: dict) -> list[str]:
    res = []
    for opt in product.get("options") or []:
        name = clean_text(opt.get("name"))
        vals = [clean_text(v) for v in opt.get("values") or [] if clean_text(v)]
        if name.casefold() == "title" and vals and all(v.casefold() == "default title" for v in vals): continue
        if name and vals: res.append(name)
    return res[:4]


def _selected_options(variant: dict, allowed: list[str]) -> list[tuple[str, str]]:
    m = {n.casefold(): n for n in allowed}; res = []
    for opt in variant.get("selectedOptions") or []:
        n, v = clean_text(opt.get("name")), clean_text(opt.get("value"))
        cn = m.get(n.casefold())
        if cn and v and not (cn.casefold() == "title" and v.casefold() == "default title"): res.append((cn, v))
    return res[:4]


def _product_images(product: dict) -> list[str]:
    return unique([clean_text(i.get("url")) for i in product.get("images") or [] if clean_text(i.get("url"))])


def _images_for_variant(product: dict, variant: dict, opts: list[tuple[str, str]], site: dict) -> list[str]:
    all_imgs = _product_images(product)
    primary = clean_text((variant.get("image") or {}).get("url"))
    res = [primary] if primary else []
    grps = {clean_text(n).casefold() for n in site.get("image_group_options", [])}
    gv = [match_key(v) for n, v in opts if n.casefold() in grps and match_key(v)]
    if gv:
        pgv = {match_key(o.get("value")) for item in product.get("variants") or []
               for o in item.get("selectedOptions") or [] if clean_text(o.get("name")).casefold() in grps and match_key(o.get("value"))}
        if len(pgv) == 1: res.extend(all_imgs)
        else:
            for item in product.get("images") or []:
                a, u = match_key(item.get("altText")), clean_text(item.get("url"))
                if u and any(v in a for v in gv): res.append(u)
    if not res and len(all_imgs) == 1: res = all_imgs
    return unique(res)


def _fieldnames(site: dict) -> list[str]:
    custom = [clean_text(f.get("name")) for f in site.get("custom_fields", []) if clean_text(f.get("name"))]
    return STANDARD_FIELDS + [n for n in unique(custom) if n not in STANDARD_FIELDS]


def _base_row(product: dict, categories: list[str], site: dict) -> dict:
    row = {f: "" for f in _fieldnames(site)}
    row.update(Name=clean_text(product.get("title")),
        Description=clean_html_fragment(product.get("descriptionHtml")),
        Categories=",".join(unique([clean_text(v) for v in categories if clean_text(v)])),
        Tags=",".join(unique([clean_text(v) for v in product.get("tags") or [] if clean_text(v)])),
        brand=clean_text(product.get("vendor")) or clean_text(site.get("brand")), Stock="1000", is_upload="0")
    row.update(product.get("custom_fields") or {}); return row


def _rows_for_product(product: dict, categories: list[str], site: dict) -> list[dict]:
    variants = product.get("variants") or []
    if not variants: raise RuntimeError(f"product_without_variants:{product.get('handle')}")
    opts = _real_options(product); base = _base_row(product, categories, site)
    if not opts:
        v = variants[0]; p = money((v.get("price") or {}).get("amount"))
        c = money((v.get("compareAtPrice") or {}).get("amount")) or p
        sku = clean_text(v.get("sku")) or clean_text(product.get("handle"))
        return [dict(base, Type="simple", SKU=sku, **{"Sale price": p}, **{"Regular price": c},
                       Parent="", Images=",".join(_product_images(product)))]
    parent = stable_parent_key(product.get("handle"), (v.get("sku") for v in variants))
    res, seen = [], set()
    for v in variants:
        sel = _selected_options(v, opts)
        if not sel: raise RuntimeError(f"variant_missing_real_options:{product.get('handle')}:{v.get('id')}")
        gen = "--".join([clean_text(product.get("handle"))] + [slug(val) for _, val in sel])
        sku = clean_text(v.get("sku")) or gen
        if sku in seen: sfx = slug(str(v.get("id") or "").split("/")[-1]); sku = f"{sku}--{sfx}"
        seen.add(sku); p = money((v.get("price") or {}).get("amount"))
        c = money((v.get("compareAtPrice") or {}).get("amount")) or p
        row = dict(base, Type="variation", SKU=sku, **{"Sale price": p}, **{"Regular price": c},
                    Parent=parent, Images=",".join(_images_for_variant(product, v, sel, site)))
        for i, (name, val) in enumerate(sel, 1): row[f"Attribute {i} name"] = name; row[f"Attribute {i} value(s)"] = val
        res.append(row)
    return res


def _cache_path(engine: StorefrontEngine, handle: str) -> Path:
    d = hashlib.sha256(handle.encode()).hexdigest()[:16]
    return engine._data(f"json_data/detail_cache/{slug(handle)[:80]}-{d}.json")


def _config_fingerprint(site: dict) -> str:
    s = {"base_url": site["base_url"], "api_version": site.get("api_version"),
         "country": site.get("country"), "language": site.get("language"),
         "currency": site.get("currency"), "custom_fields": site.get("custom_fields", []), "cache_version": 2}
    return hashlib.sha256(json.dumps(s, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _detail_tasks(engine: StorefrontEngine, url_data: dict, limit: int = 0) -> list[dict]:
    cb, ub = defaultdict(list), {}
    for cat, urls in (url_data or {}).items():
        for u in urls or []:
            parts = [unquote(p) for p in urlparse(str(u)).path.split("/") if p]
            if len(parts) < 2 or parts[0] != "products": continue
            h = parts[1]; cb[h].append(cat); ub.setdefault(h, engine._norm_prod_url(handle_value=h))
    tasks = [{"handle": h, "url": ub[h], "categories": unique(cats)} for h, cats in cb.items()]
    return tasks[:limit] if limit else tasks


def _fetch_product(engine: StorefrontEngine, site: dict, handle: str, product_query: str) -> dict:
    data = engine.graphql(product_query, {"handle": handle})
    prod = data.get("product")
    if not prod: raise RuntimeError(f"product_not_found:{handle}")
    vs = (prod.get("variants") or {}).get("nodes") or []
    pi = (prod.get("variants") or {}).get("pageInfo") or {}
    after = pi.get("endCursor") if pi.get("hasNextPage") else None
    while after:
        extra = engine.graphql(VARIANT_PAGE_QUERY, {"handle": handle, "after": after})
        conn = ((extra.get("product") or {}).get("variants") or {})
        vs.extend(conn.get("nodes") or []); info = conn.get("pageInfo") or {}
        after = info.get("endCursor") if info.get("hasNextPage") else None; engine.pause()
    imgs = (prod.get("images") or {}).get("nodes") or []
    pi = (prod.get("images") or {}).get("pageInfo") or {}
    after = pi.get("endCursor") if pi.get("hasNextPage") else None
    while after:
        extra = engine.graphql(IMAGE_PAGE_QUERY, {"handle": handle, "after": after})
        conn = ((extra.get("product") or {}).get("images") or {})
        imgs.extend(conn.get("nodes") or []); info = conn.get("pageInfo") or {}
        after = info.get("endCursor") if info.get("hasNextPage") else None; engine.pause()
    prod["variants"] = unique(vs); prod["images"] = unique(imgs)
    ec = clean_text(site.get("currency", "USD")).upper()
    for v in vs:
        for pk in ("price", "compareAtPrice"):
            pc = clean_text((v.get(pk) or {}).get("currencyCode")).upper()
            if pc and pc != ec: raise RuntimeError(f"currency_mismatch:{handle}:{pk}:{ec}:{pc}")
    prod["custom_fields"] = _fetch_custom_fields(engine, site, handle, prod)
    return prod


def _fetch_custom_fields(engine: StorefrontEngine, site: dict, handle: str, prod: dict) -> dict[str, str]:
    fields = site.get("custom_fields") or []; res = {}
    html_fs = [f for f in fields if clean_text(f.get("source")).lower() == "html"]
    remix_fs = [f for f in fields if clean_text(f.get("source")).lower() == "remix_data"]
    root, page_resp = None, None
    if html_fs or remix_fs:
        purl = engine._norm_prod_url(handle_value=handle)
        page_resp = engine._request("GET", purl, headers={"accept": "text/html,application/xhtml+xml"})
    if html_fs and page_resp is not None:
        try: root = lxml_html.fromstring(page_resp.text or "")
        except Exception as e: raise RuntimeError(f"product_html_parse:{handle}:{e}")
    rv = _fetch_remix_fields(engine, site, page_resp, prod, remix_fs) if remix_fs else {}
    mf = {(clean_text(i.get("namespace")), clean_text(i.get("key"))): i.get("value")
          for i in prod.get("metafields") or [] if i}
    for f in fields:
        name = clean_text(f.get("name"))
        if not name: continue
        src = clean_text(f.get("source")).lower()
        if src == "html" and root is not None:
            xp = clean_text(f.get("xpath")); nodes = root.xpath(xp) if xp else []
            res[name] = clean_html_fragment(" ".join(n if isinstance(n, str) else inner_html(n) for n in nodes))
        elif src == "metafield":
            m = f.get("metafield") or {}
            res[name] = clean_html_fragment(mf.get((clean_text(m.get("namespace")), clean_text(m.get("key"))), ""))
        elif src == "remix_data": res[name] = rv.get(clean_text(f.get("field")) or name, "")
    return res


def _fetch_remix_fields(engine, site, page_resp, prod, fields) -> dict[str, str]:
    if page_resp is None: raise RuntimeError("remix_data_page_missing")
    cfg = site.get("remix_data") or {}; rurl = str(page_resp.url); parsed = urlparse(rurl)
    sfx = clean_text(cfg.get("suffix")) or ".data"; dp = parsed.path.rstrip("/")
    if not dp.endswith(sfx): dp += sfx
    durl = urlunparse((parsed.scheme, parsed.netloc, dp, "", "", ""))
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    vp = clean_text(cfg.get("variant_parameter")) or "v"
    if vp not in params:
        v = next((i for i in prod.get("variants") or [] if clean_text(i.get("id"))), None)
        vid = clean_text((v or {}).get("id")).rsplit("/", 1)[-1]
        if vid: params[vp] = vid
    routes = cfg.get("routes") or []
    if isinstance(routes, list): routes = ",".join(clean_text(r) for r in routes if clean_text(r))
    routes = clean_text(routes)
    if not routes: raise RuntimeError("remix_routes_missing")
    params[clean_text(cfg.get("routes_parameter")) or "_routes"] = routes
    resp = engine._request("GET", durl, params=params, headers={"accept": "text/x-script"})
    ct = clean_text(resp.headers.get("content-type")).lower()
    if "text/x-script" not in ct and not (resp.text or "").lstrip().startswith("["):
        raise RuntimeError(f"remix_bad_ct:{ct}:{durl}")
    decoder = RemixSingleFetchDecoder(resp.text or ""); res = {}
    for f in fields:
        sn = clean_text(f.get("field")) or clean_text(f.get("name"))
        if sn: res[sn] = portable_text_to_html(decoder.find_field(sn))
    return res


# ═══ SKU / Parent 标准化 ═══

def _normalize_output_identifiers(groups: list) -> tuple[list, dict]:
    groups = [(h, [dict(r) for r in rows]) for h, rows in groups]
    sku_map = defaultdict(list)
    for gi, (hv, rows) in enumerate(groups):
        for ri, row in enumerate(rows):
            s = clean_text(row.get("SKU"))
            if s: sku_map[s].append((gi, ri, hv))
    dups = {k: v for k, v in sku_map.items() if len(v) > 1}
    used = {k for k, v in sku_map.items() if len(v) == 1}
    final = {}
    for sku, es in sorted(dups.items()):
        hc = defaultdict(int)
        for _, _, hv in es: hc[hv] += 1
        for gi, ri, hv in sorted(es, key=lambda x: (x[2], x[0], x[1])):
            cand = f"{sku}--{slug(hv)}"
            if hc[hv] > 1: cand = f"{cand}--{ri + 1}"
            if cand in used:
                d = hashlib.sha256(f"{sku}\0{hv}\0{gi}\0{ri}".encode()).hexdigest()[:8]
                cand = f"{cand}--{d}"
            if cand in used: raise RuntimeError(f"duplicate_sku:{cand}")
            used.add(cand); final[(gi, ri)] = cand
    for gi, (_, rows) in enumerate(groups):
        orig = [clean_text(r.get("SKU")) for r in rows]
        for ri, row in enumerate(rows): row["SKU"] = final.get((gi, ri), orig[ri])
    all_s = [clean_text(r.get("SKU")) for _, rows in groups for r in rows if clean_text(r.get("SKU"))]
    if len(all_s) != len(set(all_s)): raise RuntimeError("duplicate_sku_after_normalization")
    rew, up, rv = 0, set(), set(all_s)
    for hv, rows in groups:
        pr = [r for r in rows if clean_text(r.get("Type")).lower() == "variation"]
        if not pr: continue
        op = {clean_text(r.get("Parent")) for r in pr if clean_text(r.get("Parent"))}
        np = stable_parent_key(hv, rv | up)
        if op != {np}: rew += 1
        for r in pr: r["Parent"] = np
        up.add(np)
    return groups, {"source_duplicate_sku_groups": len(dups),
                    "rewritten_sku_rows": sum(len(e) for e in dups.values()),
                    "rewritten_parent_products": rew}


# ═══ build_details ═══

def build_details(engine: StorefrontEngine, *, limit: int = 0, resume: bool = True) -> list:
    site = engine.site
    url_data = Tool.File.load_json(engine._data("json_data/data_url.json"))
    if not isinstance(url_data, dict) or not url_data: raise RuntimeError("url_json_missing_or_empty")
    tasks = _detail_tasks(engine, url_data, limit=limit)
    if not tasks: raise RuntimeError("no_valid_product_tasks")
    fp = _config_fingerprint(site); is_sample = bool(limit); sfx = "_sample" if is_sample else ""
    out = (engine._data(f"pd/data/{slug(site['site_name'])}_detail_sample_{limit}.csv")
           if is_sample else engine._data("pd/data/output.csv"))
    prog_p = engine._data(f"json_data/detail{sfx}_progress.json")
    fail_p = engine._data(f"json_data/detail{sfx}_fail.json")
    fs = Tool.File.load_json(fail_p, {"failed": [], "skipped": []}) if resume else {"failed": [], "skipped": []}
    lf = fs.get("failed") or []; ls = fs.get("skipped") or []
    failed, skipped = [], []
    for item in ls:
        if isinstance(item, dict) and DRK(item): skipped = URD(skipped, item)
    for item in lf:
        if isinstance(item, dict) and DRK(item):
            if ISF(item): skipped = URD(skipped, {**item, "status": "skipped_not_public"})
            else: failed = URD(failed, item)
    product_query = _product_query(site); completed, products = [], {}
    for idx, task in enumerate(tasks, 1):
        h = task["handle"]; cp = _cache_path(engine, h)
        cache = Tool.File.load_json(cp, {}) if resume else {}
        if cache.get("fingerprint") == fp and isinstance(cache.get("product"), dict):
            product = cache["product"]
            failed = [r for r in failed if DRK(r) != h]
            skipped = [r for r in skipped if DRK(r) != h]
            Tool.print(f"[DETAIL CACHE] {idx}/{len(tasks)} {h}")
        elif resume and any(DRK(r) == h for r in skipped):
            Tool.print(f"[DETAIL SKIPPED CACHE] {idx}/{len(tasks)} {h}")
            Tool.File.save_json({"failed": failed, "skipped": skipped}, fail_p); continue
        else:
            try:
                product = _fetch_product(engine, site, h, product_query)
                Tool.File.save_json(cp, {"fingerprint": fp, "handle": h, "source_url": task["url"], "product": product})
                failed = [r for r in failed if DRK(r) != h]; skipped = [r for r in skipped if DRK(r) != h]
                Tool.print(f"[DETAIL OK] {idx}/{len(tasks)} {h} variants={len(product.get('variants') or [])} images={len(product.get('images') or [])}")
            except Exception as e:
                rec = {"handle": h, "url": task["url"], "reason": str(e)}
                if ISF(e):
                    failed = [r for r in failed if DRK(r) != h]; skipped = URD(skipped, {**rec, "status": "skipped_not_public"})
                    Tool.print(f"[DETAIL SKIPPED] {idx}/{len(tasks)} {h}: {e}")
                else:
                    skipped = [r for r in skipped if DRK(r) != h]; failed = URD(failed, rec)
                    Tool.print(f"[DETAIL FAILED] {idx}/{len(tasks)} {h}: {e}")
                Tool.File.save_json({"failed": failed, "skipped": skipped}, fail_p); continue
            engine.pause()
        products[h] = product; completed.append(h)
        Tool.File.save_json({"failed": failed, "skipped": skipped}, fail_p)
        Tool.File.save_json({"stage": "running", "sample": is_sample, "task_count": len(tasks),
            "completed_handles": completed, "completed_count": len(completed),
            "failure_count": len(failed), "skipped_count": len(skipped)}, prog_p)
    groups = []
    for task in tasks:
        prod = products.get(task["handle"])
        if not prod: continue
        try: groups.append((task["handle"], _rows_for_product(prod, task["categories"], site)))
        except Exception as e: failed = URD(failed, {"handle": task["handle"], "url": task["url"], "reason": f"row_build:{e}"})
    groups, id_stats = _normalize_output_identifiers(groups)
    rows = [r for _, pr in groups for r in pr]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fns = _fieldnames(site)
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fns, extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in fns})
    Tool.File.save_json({"failed": failed, "skipped": skipped}, fail_p)
    stage = "finished_with_failures" if failed else "finished_with_skips" if skipped else "finished"
    Tool.File.save_json({"stage": stage, "sample": is_sample, "sample_limit": limit, "task_count": len(tasks),
        "completed_handles": completed, "completed_count": len(completed), "row_count": len(rows),
        "simple_rows": sum(r.get("Type") == "simple" for r in rows),
        "variation_rows": sum(r.get("Type") == "variation" for r in rows),
        "failure_count": len(failed), "skipped_count": len(skipped), "identifier_normalization": id_stats}, prog_p)
    Tool.print(f"详情={out} 商品={len(completed)} 行={len(rows)} 失败={len(failed)} 跳过={len(skipped)} SKU重写={id_stats['rewritten_sku_rows']}", "green")
    return rows


# ═══ validate ═══

def validate(engine: StorefrontEngine, *, sample: bool = False, inventory_count: int = None) -> dict:
    site = engine.site; sfx = "_sample" if sample else ""
    url_data = Tool.File.load_json(engine._data(f"json_data/data_url{sfx}.json"), {})
    csv_p = (engine._data(f"pd/data/{slug(site['site_name'])}_detail_sample_{site.get('sample_limit', 10)}.csv")
             if sample else engine._data("pd/data/output.csv"))
    dfail_p = engine._data(f"json_data/detail{sfx}_fail.json")
    ufail_p = engine._data(f"json_data/data_url{sfx}_fail.json")
    rpt_p = engine._data(f"validation_report{sfx}.json")
    ds_state = Tool.File.load_json(dfail_p, {"failed": [], "skipped": []})
    url_f = Tool.File.load_json(ufail_p, {"failed": []})
    df, ds = [], []
    for item in ds_state.get("skipped") or []:
        if isinstance(item, dict) and DRK(item): ds = URD(ds, item)
    for item in ds_state.get("failed") or []:
        if isinstance(item, dict) and DRK(item):
            if ISF(item): ds = URD(ds, {**item, "status": "skipped_not_public"})
            else: df = URD(df, item)
    sh = {DRK(r) for r in ds if DRK(r)}
    exp_f = _fieldnames(site); rows, af = [], []
    if Path(csv_p).exists():
        with open(csv_p, "r", encoding="utf-8-sig", newline="") as f:
            rdr = csv.DictReader(f); af = rdr.fieldnames or []; rows = list(rdr)
    iss = {k: 0 for k in ["header_mismatch","invalid_type_rows","stock_not_1000_rows","missing_sku_rows",
        "duplicate_sku_rows","missing_name_rows","missing_price_rows","missing_images_rows",
        "simple_with_parent_rows","simple_with_attributes_rows","variation_missing_parent_rows",
        "variation_missing_attributes_rows","variation_parent_equals_sku_rows",
        "parent_collides_with_variant_sku_groups","attribute_pair_mismatch_rows","categories_pipe_rows",
        "dirty_description_rows","invalid_catalog_entries","invalid_url_entries",
        "source_cache_missing_products","source_variant_count_mismatch_products","source_missing_variant_rows",
        "source_unexpected_rows","source_type_mismatch_rows","source_price_mismatch_rows",
        "source_option_mismatch_rows","source_parent_mismatch_rows","source_image_mismatch_rows",
        "source_category_mismatch_rows","source_custom_field_mismatch_rows","source_name_mismatch_rows",
        "required_custom_fields_empty"]}
    iss["header_mismatch"] = int(af != exp_f)
    seen_sku = set(); dirty_re = re.compile(r"<a\b|href\s*=|https?://|<button\b|<form\b|<script\b|<style\b|<svg\b|<img\b", re.I)
    desc_f = ["Description"] + [clean_text(f.get("name")) for f in site.get("custom_fields", []) if clean_text(f.get("name"))]
    for row in rows:
        rt = clean_text(row.get("Type")).lower()
        if rt not in {"simple","variation"}: iss["invalid_type_rows"] += 1
        if clean_text(row.get("Stock")) != "1000": iss["stock_not_1000_rows"] += 1
        sku = clean_text(row.get("SKU"))
        if not sku: iss["missing_sku_rows"] += 1
        elif sku in seen_sku: iss["duplicate_sku_rows"] += 1
        seen_sku.add(sku)
        if not clean_text(row.get("Name")): iss["missing_name_rows"] += 1
        if not clean_text(row.get("Sale price")) and not clean_text(row.get("Regular price")): iss["missing_price_rows"] += 1
        if not clean_text(row.get("Images")): iss["missing_images_rows"] += 1
        pairs, mis = [], False
        for i in range(1, 5):
            n = clean_text(row.get(f"Attribute {i} name")); v = clean_text(row.get(f"Attribute {i} value(s)"))
            if bool(n) != bool(v): mis = True
            if n and v: pairs.append((n, v))
        if mis: iss["attribute_pair_mismatch_rows"] += 1
        if rt == "simple":
            if clean_text(row.get("Parent")): iss["simple_with_parent_rows"] += 1
            if pairs: iss["simple_with_attributes_rows"] += 1
        if rt == "variation":
            if not clean_text(row.get("Parent")): iss["variation_missing_parent_rows"] += 1
            if not pairs: iss["variation_missing_attributes_rows"] += 1
        if "|" in str(row.get("Categories") or ""): iss["categories_pipe_rows"] += 1
        if any(dirty_re.search(str(row.get(f) or "")) for f in desc_f): iss["dirty_description_rows"] += 1
    vr = [r for r in rows if clean_text(r.get("Type")).lower() == "variation"]
    vs = {clean_text(r.get("SKU")) for r in vr if clean_text(r.get("SKU"))}
    iss["variation_parent_equals_sku_rows"] = sum(bool(clean_text(r.get("Parent"))) and clean_text(r.get("Parent")) == clean_text(r.get("SKU")) for r in vr)
    iss["parent_collides_with_variant_sku_groups"] = len({clean_text(r.get("Parent")) for r in vr if clean_text(r.get("Parent")) in vs})
    ab = {clean_text(r.get("SKU")): r for r in rows if clean_text(r.get("SKU"))}
    cn = exp_f[len(STANDARD_FIELDS):]; spc, epg = 0, []
    for task in _detail_tasks(engine, url_data):
        h = task["handle"]
        cache = Tool.File.load_json(_cache_path(engine, h), {})
        prod = cache.get("product") if cache.get("fingerprint") == _config_fingerprint(site) else None
        if not isinstance(prod, dict):
            if h not in sh: iss["source_cache_missing_products"] += 1
            continue
        spc += 1
        try: epg.append((h, _rows_for_product(prod, task["categories"], site)))
        except Exception: iss["source_variant_count_mismatch_products"] += 1
    epg, id_stats = _normalize_output_identifiers(epg)
    e_all = {clean_text(r.get("SKU")) for _, er in epg for r in er if clean_text(r.get("SKU"))}
    for _, er in epg:
        apr = 0
        for e in er:
            sku = clean_text(e.get("SKU")); row = ab.get(sku)
            if row is None: iss["source_missing_variant_rows"] += 1; continue
            apr += 1
            if clean_text(row.get("Type")).lower() != clean_text(e.get("Type")).lower(): iss["source_type_mismatch_rows"] += 1
            if (clean_text(row.get("Sale price")) != clean_text(e.get("Sale price")) or
                clean_text(row.get("Regular price")) != clean_text(e.get("Regular price"))): iss["source_price_mismatch_rows"] += 1
            ao = [(clean_text(row.get(f"Attribute {i} name")), clean_text(row.get(f"Attribute {i} value(s)")))
                  for i in range(1, 5) if clean_text(row.get(f"Attribute {i} name")) or clean_text(row.get(f"Attribute {i} value(s)"))]
            eo = [(clean_text(e.get(f"Attribute {i} name")), clean_text(e.get(f"Attribute {i} value(s)")))
                  for i in range(1, 5) if clean_text(e.get(f"Attribute {i} name")) or clean_text(e.get(f"Attribute {i} value(s)"))]
            if ao != eo: iss["source_option_mismatch_rows"] += 1
            if clean_text(row.get("Parent")) != clean_text(e.get("Parent")): iss["source_parent_mismatch_rows"] += 1
            ai = {clean_text(v) for v in str(row.get("Images") or "").split(",") if clean_text(v)}
            ei = {clean_text(v) for v in str(e.get("Images") or "").split(",") if clean_text(v)}
            if ai != ei: iss["source_image_mismatch_rows"] += 1
            if clean_text(row.get("Categories")) != clean_text(e.get("Categories")): iss["source_category_mismatch_rows"] += 1
            if clean_text(row.get("Name")) != clean_text(e.get("Name")): iss["source_name_mismatch_rows"] += 1
            if any(clean_text(row.get(fn)) != clean_text(e.get(fn)) for fn in cn): iss["source_custom_field_mismatch_rows"] += 1
        if apr != len(er): iss["source_variant_count_mismatch_products"] += 1
    iss["source_unexpected_rows"] = len(set(ab) - e_all)
    catalog = Tool.File.load_json(engine._data("json_data/data.json"), {})
    for k, v in (catalog or {}).items():
        if not clean_text(k) or not engine._norm_col_url(v): iss["invalid_catalog_entries"] += 1
    for cat, urls in (url_data or {}).items():
        if not clean_text(cat) or not isinstance(urls, list) or len(urls) != len(set(urls)): iss["invalid_url_entries"] += 1; continue
        for u in urls:
            if not engine._norm_prod_url(u): iss["invalid_url_entries"] += 1
    cfn_rows = {f: sum(bool(clean_text(row.get(f))) for row in rows) for f in cn}
    req_cf = {clean_text(f.get("name")) for f in site.get("custom_fields", []) if f.get("validation_required") and clean_text(f.get("name"))}
    missing_req = sorted(f for f in req_cf if not cfn_rows.get(f))
    iss["required_custom_fields_empty"] = len(missing_req)
    fc = {"url_failures": len(url_f.get("failed") or []), "detail_failures": len(df)}
    passed = bool(rows) and not any(iss.values()) and not any(fc.values())
    report = {"site_name": site["site_name"], "mode": "sample" if sample else "full",
        "inventory_product_count": inventory_count,
        "catalog_categories": len(catalog) if isinstance(catalog, dict) else 0,
        "url_categories": len(url_data) if isinstance(url_data, dict) else 0,
        "csv_rows": len(rows), "simple_rows": sum(clean_text(r.get("Type")).lower()=="simple" for r in rows),
        "variation_rows": sum(clean_text(r.get("Type")).lower()=="variation" for r in rows),
        "custom_fields": cn, "custom_field_nonempty_rows": cfn_rows, "missing_required_custom_fields": missing_req,
        "source_products_cross_checked": spc, "identifier_normalization": id_stats,
        "issues": iss, "failures": fc, "skips": {"detail_skipped": len(ds), "handles": sorted(sh)},
        "passed": passed, "limits": {"sample": sample}}
    Tool.File.save_json(report, rpt_p)
    Tool.print(f"校验通过={passed} 行={len(rows)} simple={report['simple_rows']} variation={report['variation_rows']} 问题={sum(iss.values())} 失败={sum(fc.values())}", "green")
    return report


# ═══ main ═══

def main():
    engine = StorefrontEngine()
    runtime = engine._count_products()
    inventory = int(runtime or 0)
    if run_mode == "sample": sample, limit = True, sample_limit
    elif run_mode == "full": sample, limit = False, 0
    else: sample = inventory > full_threshold; limit = sample_limit if sample else 0
    scope = f"sample({limit})" if sample else "full"
    Tool.print(f"run_mode={run_mode} scope={scope} inventory={inventory}")
    build_details(engine, limit=limit, resume=resume)
    report = validate(engine, sample=sample, inventory_count=inventory)
    report["selection"] = {"run_mode": run_mode, "full_threshold": full_threshold,
        "inventory_product_count": inventory, "selected_mode": "sample" if sample else "full", "sample_limit": limit}
    Tool.File.save_json(report, engine._data(f"validation_report{'_sample' if sample else ''}.json"))
    Tool.print(f"阶段3完成 校验通过={report['passed']}", "green")


if __name__ == "__main__":
    main()
