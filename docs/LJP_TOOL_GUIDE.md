# `_ljp` Tool Quick Guide

## Read This First

This document is the primary reference for AI agents and contributors using or changing `_ljp`. Read it before inspecting implementation details. Only trace source code when this guide does not cover the case, when observed behavior conflicts with it, or when debugging an error. Update this guide when a confirmed public behavior changes.

## What `_ljp` Provides

`_ljp` is the shared toolkit for site crawlers and product-export pipelines. It owns:

- Site configuration and HTTP sessions
- File, URL, HTML, and product-row helpers
- Optional fingerprinted Playwright pages
- Reusable Step2, Step3, Step4, and post-processing templates

Create the shared tool once in a site-local `config.py`:

```python
from _ljp import Base_tool, Tool_config

config = Tool_config(
    base_url='https://example.com',
    site='example.com',
    zk=0.8,
)
Tool = Base_tool(config)
```

Pass that same `Tool` object to every Step.

`Base_tool` explicitly types the public `Tool` members (`File`, `URL`, `HTML`,
`Product`, `Browser`, `session`, and request/export helpers), so Python IDEs
can provide completion for `Tool.xxx`. The supplied external-template
`config.py` files also annotate their module-level `Tool` as `Base_tool`.

## `Tool` Surface

| Entry | Use it for |
| --- | --- |
| `Tool.get(url, ...)` | Default HTTP request path. Prefer this for normal static pages or APIs. |
| `Tool.post(url, ...)` | POST through the same retrying HTTP session. |
| `Tool.File` | JSON/CSV persistence and site-prefixed paths. |
| `Tool.URL` | Joining relative links and normalizing URL pieces. |
| `Tool.HTML` | Description cleanup and lightweight HTML helpers. |
| `Tool.Product` | Building standard product or variation dictionaries. |
| `Tool.browser` | Optional browser facade with Playwright or DrissionPage backends. `Tool.Browser` is a compatible alias. |
| `Tool.print(message, color=...)` | Project-standard status output. |
| `Tool.json_del_url(rows)` | Removes the internal `url` field before final CSV export. |
| `Tool.close()` | Closes the HTTP session and the current thread's browser resources. |

### Paths and Files

`Tool.File.path_add_site('data/ml.json')` prefixes the filename with the configured site and creates parent directories. `save_json` and `save_csv` apply the same prefix internally; `load_json` expects the path supplied by the caller (template code normally passes the result of `path_add_site`). `read_csv(path=...)` applies the prefix itself. Keep using these helpers instead of raw file I/O for pipeline files.

`Tool.HTML.save(html)` comments out script tags in a debug HTML snapshot. Use `Tool.HTML.save_raw(html)` only when a parser or diagnosis needs the original script contents preserved.

`Tool.HTML.clean_product_desc(tree)` is the rich-text sanitizer for an already
parsed lxml tree. It keeps only `p`, `br`, lists, and basic emphasis tags;
removes link attributes, raw `http(s)` URLs, scripts, forms, iframes, SVG, and
similar unsafe markup. `clean_product_desc_str(value)` is the matching string
wrapper. `HTML.is_text_field(name)` detects description-like metafields such
as `metafield`, `miaoshu`, `detail`, `feature`, `dimension`, `warranty`, and
`specification`.

For an already loaded pandas DataFrame, use
`Tool.HTML.clean_text_fields_df(df, columns=None, inplace=False)`. It performs
no file I/O and returns the cleaned DataFrame. With `columns=None`, it applies
the same description/metafield name and keyword detection as the standalone
script; provide a list/tuple or a comma-separated string for explicit columns.
Missing explicit columns are ignored. The default returns a copy, while
`inplace=True` mutates and returns the supplied DataFrame:

```python
cleaned_df = Tool.HTML.clean_text_fields_df(df)
Tool.HTML.clean_text_fields_df(
    df,
    columns=['Description', 'short description(product.metafields.c_f.short_description)'],
    inplace=True,
)
```

`Tool_config` copies supplied headers, cookies, browser options, and retry
settings. Modifying the source dictionaries after creating a Tool therefore
does not modify that Tool. `max_retry` must be a positive integer, `time_out`
must be positive, and `zk` must be within 0..1.

`File.save_json` and `File.save_csv` use an atomic replacement in the target
directory: a process interruption cannot leave a partially written cache or
CSV at the final path. They return the resolved site-prefixed `Path` and raise
`OSError` when writing fails. `load_json(path)` continues to return `{}` for a
missing or invalid file; use `load_json(path, default=..., strict=True)` when a
specific fallback or a parsing exception is required. `read_csv` accepts either
in-memory `data` (including an empty list) or a site-prefixed `path`.

## HTTP Requests

`Tool.get` and `Tool.post` use a curl_cffi session per worker thread, so Step4
workers do not share a mutable HTTP session. The default retryable responses
are 429, 500, 502, 503, and 504. Customize them at Tool construction:

```python
config = Tool_config(
    base_url='https://example.com',
    site='example.com',
    zk=0.8,
    max_retry=4,
    retry_statuses=(429, 500, 502, 503, 504),
    retry_backoff={
        'base_seconds': 1.0,
        'max_seconds': 20.0,
        'jitter_seconds': 0.5,
    },
)
```

HTTP 404 responses return immediately. If every attempt ends in a transport
error, the result is `FailedResponse` with `status_code == 0`, empty text and
content, plus the original exception in `.error`. It is safe to branch on
`response.status_code` without handling a special sentinel class.

## Browser Automation

Browser automation is off by default. Configure its defaults when constructing `Tool_config`:

```python
config = Tool_config(
    base_url='https://example.com',
    site='example.com',
    zk=0.8,
    browser={
        'enabled': True,
        'backend': 'playwright',
        'headless': False,  # default: visible browser
        'context_count': 4,
        'block_images': True,
        'block_resource_types': ['font', 'media'],
        'fingerprint_options': {'seed': 42},
        'stable_wait_ms': 800,
    },
)
```

浏览器选项统一放在 `browser` 字典中；`BrowserConfig` 内部字段为
`enabled`、`headless`、`context_count` 等，无额外前缀。

The same settings may be changed before the first browser page is requested:

```python
Tool.browser.config.enabled = True
Tool.browser.config.context_count = 4
Tool.browser.config.context_options = {}
Tool.browser.config.launch_options = {}
```

`Tool.browser` is the browser entry point; `Tool.Browser` is a compatible
alias to the same object. Select a backend with `browser['backend']`;
`playwright` is the default and `drissionpage` is also built in. `engine` and
`driver` are accepted aliases during migration. A project may register another implementation with
`Browser.register_backend(name, BackendSubclass)`.

Browser config fields:

- `enabled`: 是否启用浏览器自动化。
- `backend`: `playwright`（默认）或 `drissionpage`。
- `headless`: 是否隐藏浏览器窗口，默认 `False`（有头）。
- `context_count`: 每个工作线程的页面池大小；Playwright 为独立 Context 数量，DrissionPage 为 Tab 数量。
- `block_images`: `True` 时阻止图片加载，默认 `False`。Playwright 精确拦截 `image` 资源；DrissionPage 使用 `ChromiumOptions.no_imgs(True)`。
- `block_resource_types`: 要阻止的 Playwright 资源类型，例如 `font`、`media`、`stylesheet` 和 `script`；DrissionPage 将已知类型转换为 URL 后缀规则。
- `blocked_url_patterns`: 要阻止的 URL 通配符列表；两种后端均在导航前安装规则。
- `extra_http_headers`: 在每个浏览器 Context/Tab 上附加的请求头。
- `user_agent`: 公共 User-Agent；Playwright 写入 Context，DrissionPage 写入 ChromiumOptions。也可保留后端专属设置。
- `init_scripts`: 仅 Playwright，在每个文档加载前执行的 JavaScript 字符串列表。
- `context_options`: 仅 Playwright，传给 `browser.new_context` 的参数。
- `launch_options`: 仅 Playwright，传给 `chromium.launch` 的参数。
- `fingerprint_enabled`: 仅 Playwright，默认 `True`；启用时需要 `fingerprint_toolkit`，设为 `False` 可使用普通 Playwright Context。
- `fingerprint_options`: 仅 Playwright，传给 `FingerprintKit` 的 `seed` 或 `profile`，每个 Context 创建独立指纹对象并在页面导航前注入。
- `context_create_delay_ms`: 仅 Playwright，创建 Context 之间的间隔，默认 1000ms。
- `drission_options`: 仅 DrissionPage。支持 `browser_path`、`address`、`local_port`、`user_data_path`、`cache_path`、`download_path`、`user_agent`、`proxy`、`no_imgs`、`auto_port`、`arguments`、`preferences`、`headers`、`cookies` 和 `blocked_urls`。未指定 `address`/`local_port` 时默认自动选择调试端口，适配 Step4 多线程。`no_imgs=True` 对应 DrissionPage 的 `ChromiumOptions.no_imgs(True)`。
- `wait_until`、`timeout`、`network_idle_timeout`、`stable_wait_ms`: 页面导航与稳定等待控制。

Use it from a Step implementation:

```python
page = self.get_page(
    url,
    wait_for_selector='.product-card',
)
# Continue interacting with and parsing page here.
```

`get_page` rotates the current backend pool, creates a page, navigates when a
URL is given, waits for the requested selector, and then waits for the
configured stable interval. The Playwright backend additionally injects
`FingerprintKit` when enabled and attempts a network-idle wait. It returns the
live, *native* page object: Playwright returns a Playwright `Page`, while
DrissionPage returns a `ChromiumPage`/`ChromiumTab`. Parsing and subsequent
actions belong to the site-specific Step code.

### Browser-Context Fetch and Response Capture

With the Playwright backend, `Tool.browser.fetch()` executes native
`window.fetch()` in the selected page's JavaScript context. It uses that page's
browser session and visible cookies, and remains subject to normal CORS and
same-origin rules. It returns `BrowserFetchResponse` with `url`, `status`,
`headers`, binary `content`, visible `cookies`, and `error`; `text()` and
`json()` decode the response body. `body_bytes` accepts Python `bytes` and is
sent as a JavaScript `Uint8Array`.

```python
response = Tool.browser.fetch(
    'https://example.com/api/cart',
    page=page,
    options={
        'method': 'POST',
        'headers': {'content-type': 'application/octet-stream'},
        'body_bytes': b'\x01\x02',
    },
    timeout=15000,
)
if response.ok:
    payload = response.json()
```

For a request triggered by a click, navigation, or other page action, install
the expectation before triggering that action. `response_data()` reads the
intercepted native Playwright response body into the same `BrowserFetchResponse`
shape:

```python
with Tool.browser.expect_response(page, '**/api/products*', timeout=15000) as event:
    page.click('button.load-products')
response = Tool.browser.response_data(event.value)
```

These helpers are Playwright-only. A DrissionPage site continues to use its
native `page.run_js()` or `page.listen` APIs. Neither browser API exposes
`HttpOnly` cookies through `document.cookie` or `Set-Cookie` through ordinary
fetch response headers.

This is deliberately not a fake common page API. Existing code that calls
Playwright-specific methods such as `page.goto()` or `page.locator()` must stay
on `backend='playwright'`. A DrissionPage site uses DrissionPage methods such
as `page.get()` and `page.ele()` while still obtaining the page through
`Tool.browser.get_page()`.

Example DrissionPage configuration:

```python
config = Tool_config(
    base_url='https://example.com',
    site='example.com',
    zk=0.8,
    browser={
        'enabled': True,
        'backend': 'drissionpage',
        'headless': True,
        'context_count': 2,
        'timeout': 30000,
        'drission_options': {
            'arguments': ['--disable-blink-features=AutomationControlled'],
            'user_agent': 'Mozilla/5.0 ...',
        },
    },
)

page = Tool.browser.get_page('https://example.com', wait_for_selector='#app')
# DrissionPage native API:
title = page.ele('h1').text
```

When a site returns a verification or access-denied page, call
`Tool.browser.restart_context()` from the site Step. For Playwright it closes
the current thread's fingerprinted contexts and creates a fresh pool; pass
`relaunch_browser=True` to replace Chromium too. DrissionPage has no isolated
Context equivalent, so it always replaces the current thread's Chromium
instance. Do not pass a page object to another thread.

For Step4 workers, the synchronous browser pool is thread-local. Each request
worker owns its own pool and closes it when the worker exits.

## Step Templates

Import shared templates from `_ljp.mb.base`. Site packages such as `_ljp.mb.zj` preserve compatible thin subclasses.

### Step2: Category Pages to Detail URLs

Subclass `Step2` and implement:

```python
def fetch_page(self, page, params):
    return product_urls, next_url
```

- Return `list[str]` product URLs and a truthy next-page URL to continue.
- Set `page.status = 'end'` for a confirmed empty/end/invalid page. It is cached and skipped next time.
- Set `page.status = 'fail'` for a temporary request failure. It is not cached and will retry next run.
- Override `build_params(page)` when request parameters affect a page. The result participates in the cache key.
- Use `Tool.get` by default; use `self.get_page(...)` only when browser automation is needed.

Input: `{category_name: category_url}` JSON. Output: `{category_name: [detail_url, ...]}` JSON.

### Step3: URL Deduplication

`Step3` reads the Step2 category mapping, globally deduplicates URLs while retaining first-seen order, and saves a JSON list. It normally needs no subclass logic.

### Step4: Product Details to CSV Rows

Subclass `Step4` and implement:

```python
def fetch_product(self, url, category):
    return [row_dict]
```

The return may contain dictionaries or objects exposing `to_dic()`. It must normalize to a non-empty list. `None` or an empty list is treated as a failed parse, is not cached, and retries on the next run. Step4 reuses successful product results for the same URL across categories, writes cache data, then exports the test CSV and the final CSV. The `Categories` field is replaced with the task category during final output.

Use `Tool.Product.Simple(...).to_dic()` or `Tool.Product.Variation(...).to_dic()` when the standard output schema fits. Keep HTTP/browser request and parser code inside `fetch_product`.

`stock=None` uses the standard fallback stock value. Pass `stock=0` for a known out-of-stock SKU; zero is preserved in the exported row.

Product helpers normalize relative image links against `base_url` before they
enter the `Images` field. Keep site-specific image extraction inside
`fetch_product`, then pass the raw image list to `Tool.Product.Simple` or
`Tool.Product.Variation`.

During `to_dic()` construction, the main description and description-like
custom fields passed through `**exc` are sanitized automatically through the
same tree-based cleaner. Other custom fields are preserved unchanged.

### Step6: Variation Parents

`Step6Variable` reads `res/quchong.csv`, inserts a `variable` parent row
before every non-empty variation family, and writes `fwq/variable.csv`.
It preserves simple products and original family ordering. Configure
`merge_fields` for values that belong on the parent (normally images and
attribute values) and `description_fields` for fields retained only on the
parent. Amazon and Target external templates invoke this step automatically.

### Direct Amazon and Target Modes

`_ljp.mb.amazon` and `_ljp.mb.target` are direct-collection modes. They do
not use the normal category-page `Step2` pagination template. Their collectors
persist the normal Step4 input shape, `{category: [detail_task, ...]}`, in
`data/detail_url.json`; that saved file is reused by default. Pass
`refresh=True` to collect it again. Detail results then use the normal
`DetailCatch`/`DetailIndex` cache and the same `Quchong`, `Step7`, `Step8`,
`Step9`, and `Step10` processing classes as ZJ.

Amazon retains the template's sequence: its `Step1` searches and brand-filters
ASINs into `data/amazon_asins.json`; `Step2` requests each product page and
expands its variation ASINs into `data/detail_url.json`; `Step4` initializes
the US ZIP delivery environment, then requests and parses the product and
price endpoints. The source request/parse flow, anti-bot checks, delays, and
fallbacks live in these classes; only task persistence and detail caching are
provided by `_ljp`. Amazon `Step4` defaults to one worker, matching the source
crawler. Configure a DrissionPage browser for `Step1`:

```python
from _ljp.mb.amazon import Step1, Step2, Step4, Quchong, Step7, Step8WpToShopify

Step1(Tool, keyword='dudewipe', brand='DUDE Wipes').run()
Step2(Tool).run()
Step4(Tool, max_threads=3).run()
Quchong(Tool).run()
```

Target `Step2` preserves the existing SLP API parameters, new-session
fingerprint rotation, retries, and backoff. It writes a standard mapping for
`Step4`; a legacy flat Target URL JSON file is also accepted by Target
`Step4`. Target detail parsing uses the template's native DrissionPage calls,
so configure `backend='drissionpage'` before running it:

```python
from _ljp.mb.target import Step2, Step4, Quchong, Replace_imgs, WpToShopify

Step2(Tool, keyword='zzzquil', max_pages=9).run()
Step4(Tool, max_threads=3).run()
Quchong(Tool).run()
```

The Target and Amazon request configuration is read from `Tool_config` headers
and cookies where applicable; replace expired site-specific credentials there,
not in the Step modules.

The ready-to-run external project templates are `新_模板亚马逊` and
`新_模板target`. Each follows the numbered external-template layout. Their
`config.py` contains only shared site settings (URL, site name, browser,
common headers/cookies, discount, image separator, and run order); each
numbered Step file owns its collector keywords, endpoint-specific headers and
cookies, parser options, parent-field policy, CDN prefix, and export columns.
`config.ini` is reserved for image-download concurrency, proxy, and WebP
settings. Run `一键.py` to execute the configured sequence. The default
pipelines perform direct collection, cached details, dedupe, parent generation,
image download, CDN URL replacement, Shopify conversion, discounting, and
collection generation. Both templates use `,` as their image separator.

### Step8: WooCommerce to Shopify CSV

Step8 remains streaming, but keeps the final `variable` product family in a
chunk until the next family boundary or EOF. This preserves variations when a
CSV chunk boundary falls in the middle of a parent/child group. Source rows
must remain family ordered: `variable` followed by its `variation` rows.
Handle collision tracking spans every chunk in one run.

## Cache Rules

The shared cache models are `Catch` and `Index` in `_ljp/mb/model.py`
(`DetailCatch`/`DetailIndex` are legacy names used by older documentation).

- `Catch`: `category -> task_id -> {'url': url}`.
- `Index`: `url -> task_id -> cached_data`.
- Step2 index values are page metadata dictionaries containing `data`, `next_url`, and `end`.
- Step4 index values are normalized product-row lists.
- Step4 marks the cache as changed when it adds an index result or a new
  category-task mapping. The writer flushes after `catch_save_num` changes and
  also performs a final flush when the run ends, so a cache-only run may still
  rewrite the JSON files even though no new product was fetched.

Do not add a parallel cache dictionary or raw cache-file format in a site Step. Use the template cache APIs and let `run()` save them.

## Default Workflow for AI

1. Read this guide.
2. Use `Tool` helpers and the nearest shared Step template.
3. Put only site-specific request/parsing behavior in the subclass hook.
4. Use `Tool.get` first; enable `Tool.browser` only for pages that need automation.
5. Preserve the existing cache model and task/output contracts.
6. Inspect source only for an uncovered API, a bug, or a conflict with this guide. When source establishes a changed public contract, update this guide in the same change.

## Source Escalation Map

| Need | Read only when needed |
| --- | --- |
| Tool setup, session, lifecycle | `_ljp/config.py`, `_ljp/base_tool.py`, `_ljp/session.py` |
| Browser implementation failure | `_ljp/browser/browser.py`, `_ljp/browser/playwright.py`, `_ljp/browser/drission.py` |
| File naming or persistence issue | `_ljp/file_utils.py` |
| Product row shape issue | `_ljp/product.py` |
| Step2/detail pagination/cache behavior | `_ljp/mb/base/step_get_detail.py`, `_ljp/mb/model.py` |
| Step4/product threading/cache behavior | `_ljp/mb/base/step_get_product.py`, `_ljp/mb/model.py` |

## AI Contract: Decide Before Reading Source

Use this table to choose the smallest relevant surface. A site Step should
normally contain only request parameters, selectors/endpoints, and parsing.

| Task | Start here | Do not start with |
| --- | --- | --- |
| Add or repair a category crawler | `GetDetail.fetch_page` and `PageModel` | browser internals |
| Add or repair product parsing | `Get_Product.fetch_product` and `Product.Simple/Variation` | cache JSON files |
| Change retry behavior | `Tool_config` (`max_retry`, `retry_statuses`, `retry_backoff`) | Step worker threads |
| Change output columns | `fieldnames`, `Product.to_dic()`, `WpToShopify.EXTRA_META_COLUMNS` | CSV post-processing |
| Force a fresh crawl | Step `flush=True` | deleting cache files manually |
| Re-run only temporary failures | inspect `fail/*.json`, leave `flush=False` | clearing all caches |
| Change browser engine | `config.py` `browser.backend` | replacing page calls in shared code |
| Change image CDN naming | subclass `Replace_imgs.build_new_url_base` | editing hash logic |

Public import locations are the stable contract:

```python
from _ljp.mb.shopify import GetDetail, Get_Product, Replace_imgs, WpToShopify
from _ljp.mb.target import GetDetail, Get_Product, Quchong, Variable
from _ljp.mb.amazon import YMXStep1, YMXStep2, YMXStep3
```

`_ljp.mb.base.step_get_detail.GetDetail` is the category/detail URL base and
`_ljp.mb.base.step_get_product.Get_Product` is the product-detail base. Some
site packages expose these under local names such as `Step2` or `Step4`; the
hook signatures below are authoritative.

## Configuration And Lifecycle

The recommended site-local `config.py` has three layers:

```python
from _ljp import Base_tool, Tool_config

config = Tool_config(
    base_url='https://shop.example',
    site='shop.example',       # stored as the first label, e.g. ``shop``
    site_type='shopify',       # used by File.dz_path()/fl_path()
    zk=0.8,                    # sale price = compare-at price * zk
    headers={}, cookies={},
    browser={'enabled': False},
)
Tool: Base_tool = Base_tool(config)
```

`Tool_config` deep-copies mappings at construction. Later changes to the
original `headers`, `cookies`, or `browser` dictionaries do not affect the
Tool; mutate `Tool.config` (before the first browser request) if a run must
change settings. Validation rejects non-positive `max_retry`/`time_out`, a
`zk` outside `0..1`, invalid retry status codes, and invalid browser numeric
settings.

Every Step should use the same Tool instance and close it exactly once. The
context-manager form is safe for scripts:

```python
with Base_tool(config) as Tool:
    Pc(Tool, ...).run()
```

`Tool.close()` closes all thread-owned HTTP sessions and browser resources.
Do not pass a browser page or a mutable HTTP session between threads. The
facades are thread-local; each Step4 worker creates/uses its own resources.

## Public Helper Reference

### File

| Method | Contract |
| --- | --- |
| `path_add_site(path)` | Adds `<site>_` to the filename, creates parent directories, returns a `Path`. |
| `load_json(path, default=..., strict=False)` | Missing/invalid JSON returns `{}` (or a deep-copied `default`); `strict=True` re-raises parse/OS errors. |
| `save_json(data, path)` | Site-prefixes the path and atomically replaces the destination; returns the resolved `Path`. |
| `save_csv(data, path, columns=None)` | Builds a DataFrame, removes NUL bytes, writes UTF-8-SIG atomically, returns `Path`. |
| `read_csv(data=..., path=...)` | Exactly one of in-memory `data` or site-prefixed `path`; returns a DataFrame. |
| `json_ls_del(rows, target='url')` | Deep-copies row dictionaries and removes the internal field (normally `url`). |
| `dz_path()` / `fl_path()` | `res/<site_type>_<N>%off_ljp.csv` and `res/<site_type>_col_ljp.csv`, where `N=(1-zk)*100`. |

Do not mix raw paths and already-prefixed paths casually. The helpers are
designed to be called with logical paths such as `data/detail_url.json`.
Passing a `Path` returned by a helper back into another helper is supported
when its filename already starts with the site prefix, but logical paths are
clearer and avoid accidental double-prefixes.

### URL

`Tool.URL.add_site('/products/x')` joins against `base_url`; use
`URL.site_add(base, url)` for a one-off base. `get_base_domain(url)` returns
scheme plus host, `get_domain(url)` returns host, and `get_handle(url)` returns
the last path component without the trailing slash. `del_par(url)` removes
the query string while preserving the fragment. `get_params_str(params)` is a
simple query-string formatter and does not URL-encode values.

### Small `Tool` Utilities

| Method | Contract |
| --- | --- |
| `Tool.to_ml_data(tree)` | Flattens nested `{url, child}` menu data to `{path: url}`; input must be a dictionary. |
| `Tool.to_ml_json(tree, path)` | Removes the configured `custom_key`, flattens with `to_ml_data`, and saves JSON. |
| `Tool.clean_price(value)` | Stringifies and removes `$`, `/ea`, and `/EA`. |
| `Tool.sort_data(mapping)` | Returns a new dict sorted by integer-convertible keys. |
| `Tool.make_counter(n)` | Returns a closure for test limits; `None` means unlimited, exhaustion returns `0`. |
| `Tool.zs(...)` | Legacy decorator used by template scripts for lightweight status/debug output. |

`Tool.get()` and `Tool.post()` return the underlying curl response for an HTTP
response (with `.status_code`, `.text`, `.content`, `.headers`, `.json()`).
Only transport failures after all retries use `FailedResponse`; it has
`status_code == 0`, `.ok == False`, and the original exception in `.error`.

### HTML

`HTML.get_text(node)` extracts descendant text; `get_a_text_and_url(a)` returns
`(text, href)` and expects one lxml element, not a list. `extract_js_object()`
parses a balanced JavaScript object assigned to a variable (JSON first,
`json5` fallback). `script_text()` is a simpler regex extractor for an
`... = {...};` block.

For descriptions, use `clean_product_desc_str(value)` or
`clean_text_fields_df(df)`. The cleaner drops script/style/form/iframe/SVG
content, removes raw HTTP URLs and attributes, unwraps unsupported tags, and
keeps only `p`, `br`, lists, and basic emphasis tags. It is intentionally not
a general HTML sanitizer: parse site HTML first, then clean only fields that
will be exported as rich text.

### Product

`Tool.Product.Simple(...)` creates a `ProductSimple`; `Variation(...)` creates
a `ProductVariation`. Both return dictionaries through `to_dic()` with the
WooCommerce-style columns below:

| Field group | Keys / behavior |
| --- | --- |
| identity | `Type` (`simple`/`variation`), `SKU`, `Name`, `Parent`, `Categories`, `Tags` |
| pricing | `Sale price`, `Regular price` (price strings lose `$` and `/ea`) |
| content | `Description`, `Images` (absolute URLs joined by `config.images_split`) |
| inventory | `Stock` (defaults to `1000.0`; explicit `0` is preserved), `is_upload` |
| source | internal `url` (removed by `json_del_url` before final CSV) |
| custom | `**exc`, renamed to `name(product.metafields.c_f.name)` and cleaned when the field is text-like |

Variation attributes are written as `Attribute 1 name`,
`Attribute 1 value(s)`, etc. If `sku=None`, a deterministic suffix based on
attribute values is appended to the variation name. `imgs` must be a list (a
string is accepted and converted to a one-item list); relative image links
are resolved against `base_url`. If an original URL contains a comma, set a
different `images_split` before creating products.

## Step Data Contracts

### Detail URL collection (`GetDetail`)

Input JSON is a mapping of category name to one URL or a list of URLs:

```json
{"Shoes": ["https://shop/collections/shoes"], "Sale": ["https://shop/sale"]}
```

Implement `fetch_page(page, params) -> (product_urls, next_url)`. `page` is a
mutable `PageModel` with `url`, `next_url`, `page` (1-based), `extra`,
`status`, and `is_next`. Use `page.set_end()` for a confirmed empty/terminal
page and `page.set_fail()` for a temporary failure. A failure is deliberately
not cached. `build_params(page)` must return only values that affect the
response; its result is included in the MD5 page-cache key. `before_request`
is the place to compute stable per-category values such as an API base URL.
The template does not convert arbitrary exceptions from `fetch_page` into a
retry state; catch expected request/parser errors in the hook, log them, call
`page.set_fail()`, and return an empty page result. Let programming errors
surface during development.

Output is again `{category: [detail_url, ...]}`. URLs are deduplicated per
page and again while aggregating categories. The final aggregation follows
category/page traversal order; do not rely on the exact order within a single
page because the low-level page cache currently uses set-based deduplication.
`skip_input_url_ls` skips source category URLs; `skip_output_url_ls` removes
detail URLs from both page output and final aggregation. `ts_num` limits the
number of input categories, not the number of products.

The two caches are JSON dictionaries:

```text
catch_path: {category: {page_id: {"url": page_url}}}
index_path: {page_url: {page_id: {"data": [...], "next_url": ..., "end": bool}}}
```

### Product collection (`Get_Product`)

Input is the same category mapping. `fetch_product(url, category)` may return
one dictionary/object or a list; objects must expose `to_dic()`. `None`, an
empty list, or a list containing no dictionaries is a failed parse and is not
cached. Exceptions are caught by the worker and written to `fail_file` as
`{category: [url, ...]}`.

Step4 writes two CSVs:

| File | Contents |
| --- | --- |
| `output_ts_file` | Test/raw output including internal `url`, useful for diagnosis |
| `output_file` | Final output with `url` removed; `Categories` overwritten with the task category |

One URL has one shared product parse in `index_path`, even when it appears in
multiple categories. Each category receives a cloned row with its own
`Categories` value. `max_threads` controls request workers; URL locks prevent
the same URL from being fetched concurrently. `catch_save_num` controls how
many cache changes are buffered before a disk flush; the writer also flushes
once at normal completion, including for a cache-only run.

The Step4 index shape is `url -> task_id -> [normalized product-row dicts]`.
The current worker generates the shared product-cache ID from the URL (the
model also accepts an optional category argument for compatibility). Category
membership is stored separately in `catch`. Treat task IDs as opaque and use
`catch`/`index` APIs rather than constructing IDs manually.

## Standard Post-processing Steps

These classes are pure file transforms; they do not issue site requests.

| Class | Input -> output | Important behavior |
| --- | --- | --- |
| `Detail_QuChong` | category mapping -> URL list JSON | global first-seen URL dedupe |
| `Quchong` | `result.csv` -> `quchong.csv` | group by `SKU`, merge `Categories`, preserve original row order; warns on other field conflicts (blank SKUs form one group) |
| `Variable` | variation rows -> `variable.csv` | inserts one `variable` parent before each family; parent SKU is child `Parent`; when present, `Categories` participates in grouping; configurable `merge_fields`/`description_fields` |
| `Replace_imgs` | CSV -> CSV | MD5 URL basename + `.webp`; skips failed URLs and already-converted CDN URLs; removes parent families with no image |
| `WpToShopify` | WooCommerce CSV -> Shopify CSV | streaming conversion; source families must be ordered `variable` then its `variation` rows |
| `Shopify_dz` | Shopify CSV -> discount CSV | removes every handle whose compare-at price is numeric zero, then computes `Variant Price = Variant Compare At Price * Tool.zk`, rounded to 2 decimals |
| `Collection` | discount CSV -> collection CSV(s) | reads `Tags`, case-insensitive dedupe, writes at most 99 smart-collection rows per file |
| `IMG_download_ljp` | CSV `Images` -> local WebP files | reads `[PATHS]`, `[PROXY]`, `[REQUEST]` from `config.ini`; failed URLs go to `failed_log` |

`Replace_imgs` hashes the complete original URL, so query-string changes create
different filenames. Override only `build_new_url_base()` or
`load_failed_images()` for site policy. `WpToShopify` keeps the final variable
family across pandas chunk boundaries; do not sort or independently split its
input by arbitrary rows.

## Ready-made Template Pipelines

The maintained templates live under `A模板/`:

| Template | Sequence | Typical artifacts |
| --- | --- | --- |
| `新_模板shopify` | A_1 catalog -> A_2 detail URLs -> A_3 products -> A_4 SKU dedupe -> A_5 images -> A_6 Shopify -> A_7 discount -> A_8 collections | `data/ml.json`, `data/detail_url.json`, `res/result.csv`, `fwq/quchong.csv`, `res/picture.csv` |
| `新_模板自建` | A_1 -> A_2 -> A_3 -> A_4 -> A_5 variable -> A_6 images -> A_7 Shopify -> A_8 discount -> A_9 collections | same, with `fwq/variable.csv` |
| `新_模板target` | detail -> products -> dedupe -> parent -> download -> replace -> Shopify -> discount -> collections | browser backend must be `drissionpage` |
| `新_模板亚马逊` | ASIN search -> variation expansion -> products -> dedupe -> parent -> replace -> Shopify -> discount -> collections | `data/amazon_asins.json`, `data/detail_url.json` |

Run scripts from the directory that contains the script, using the project
virtual-environment interpreter (per repository instructions):

```powershell
Set-Location 'J:\changsha\A模板\新_模板shopify'
& 'J:\changsha\.venv\Scripts\python.exe' 'A_1_获取目录.py'
```

For a configured one-click runner, `Base_tool.run(BASE_DIR, STEPS)` executes
each script with `cwd=BASE_DIR`, stops on the first non-zero exit code, and
uses the current interpreter. Browser-enabled templates require the relevant
browser dependency and a working Chromium/DrissionPage installation.

## Failure And Debugging Playbook

1. Confirm the logical input path and its site prefix. A missing JSON file is
   treated as empty data by default, so inspect the printed path before
   assuming a crawler returned zero records.
2. Check HTTP `status_code`. `404` is returned immediately. A transport-only
   failure is `FailedResponse(status_code=0, error=...)`; do not call
   `.json()` on it.
3. For an empty Step4 result, inspect `fail/*.json`, the test CSV, and the
   parser return value. Returning `[]` means retry next run; it is not a valid
   “no product” cache entry.
4. For repeated Step2 pages, verify `build_params()` changes with the page
   and that `next_url` eventually becomes `None`. A truthy self-link will
   intentionally continue until the template warning threshold.
5. For missing custom columns, check `fieldnames=None` and
   `WpToShopify.EXTRA_META_COLUMNS`; product dictionaries can contain fields
   that a downstream explicit column list drops.
6. For image failures, inspect the downloader's `failed_log` and use
   `Replace_imgs.load_failed_images()` to prevent exporting known-bad URLs.
7. For access-denied pages, call `Tool.browser.restart_context()` in the Step,
   then retry with the same native backend API. Do not pass a Playwright page
   to DrissionPage code or vice versa.

When source inspection is unavoidable, read the narrow module from the map
above, then update this guide if the confirmed public contract changed. Keep
site-specific credentials, endpoint headers, and selectors in the site Step or
`config.py`; never add them to shared `_ljp` defaults.
