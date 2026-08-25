"""
阶段2: 获取每个分类下的商品URL
运行: uv run python 2_获取商品URL.py

可手动修改 run_mode / sample_limit / full_threshold 控制scope
"""
from config import Tool, resume, run_mode, sample_limit, full_threshold, max_url_pages
from storefront_engine import StorefrontEngine
from shopify_tool import unique, clean_text

PAGE_SIZE = Tool.Shopify.PAGE_SIZE


# ═══ 阶段2: 构建商品URL ═══

def build_urls(
    engine: StorefrontEngine,
    *,
    limit_products: int = 0,
    max_pages: int = 10,
    resume: bool = True,
) -> dict:
    catalog = Tool.File.load_json(engine._data("json_data/data.json"))
    if not isinstance(catalog, dict) or not catalog:
        raise RuntimeError("catalog_missing")

    is_sample = bool(limit_products)
    sfx = "_sample" if is_sample else ""
    out = engine._data(f"json_data/data_url{sfx}.json")
    prog = engine._data(f"json_data/data_url{sfx}_progress.json")
    fail = engine._data(f"json_data/data_url{sfx}_fail.json")
    mp = max_pages or 10

    result = Tool.File.load_json(out) if resume else {}
    progress = Tool.File.load_json(prog) if resume else {}
    completed = set(progress.get("completed_categories") or [])
    failures = Tool.File.load_json(fail, {"failed": []}) if resume else {"failed": []}
    fr = failures.get("failed") or []
    uniq = {url for urls in result.values() if isinstance(urls, list) for url in urls}
    items = list(catalog.items())

    for idx, (cat, curl) in enumerate(items, 1):
        if limit_products and len(uniq) >= limit_products:
            break
        if cat in completed and isinstance(result.get(cat), list):
            continue
        rem = max(0, limit_products - len(uniq)) if limit_products else 0
        cl = min(1, rem) if limit_products else 0
        try:
            links = engine._fetch_coll_products(str(curl), cl, mp)
            result[cat] = unique(links)
            uniq.update(result[cat])
            completed.add(cat)
            fr = [r for r in fr if r.get("category") != cat]
            Tool.print(f"[URL] {idx}/{len(items)} {cat}: {len(links)}个", "green")
        except Exception as e:
            result.setdefault(cat, [])
            fr.append({"category": cat, "url": curl, "reason": str(e)})
            Tool.print(f"[URL FAIL] {cat}: {e}")
        Tool.File.save_json(result, out)
        Tool.File.save_json({"failed": fr}, fail)
        Tool.File.save_json(
            {"stage": "running", "completed_categories": sorted(completed),
             "unique_urls": len(uniq), "failure_count": len(fr)},
            prog,
        )
    Tool.File.save_json(result, out)
    Tool.print(f"商品URL={len(uniq)} 分类={len(result)} 失败={len(fr)}", "green")
    return result


# ═══ main ═══

def main():
    engine = StorefrontEngine()
    runtime = engine._count_products()  # 仅计数，不需要完整 discover
    inventory = int(runtime or 0)

    if run_mode == "sample":
        limit = sample_limit
    elif run_mode == "full":
        limit = 0
    else:  # auto
        limit = sample_limit if inventory > full_threshold else 0

    scope = f"sample({limit})" if limit else "full"
    Tool.print(f"run_mode={run_mode} scope={scope} inventory={inventory}")

    build_urls(engine, limit_products=limit, max_pages=max_url_pages, resume=resume)
    Tool.print("阶段2完成 next=3_获取详情页数据.py", "green")


if __name__ == "__main__":
    main()
