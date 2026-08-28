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

`Tool.File.path_add_site('data/ml.json')` prefixes the filename with the configured site and creates parent directories. `load_json`, `save_json`, and `save_csv` also apply this site-prefix rule. Keep using these helpers instead of raw file I/O for pipeline files.

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
from _ljp.mb.target import Step2, Step4, Quchong, Step7, Step8WpToShopify

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

The shared cache models are `DetailCatch` and `DetailIndex` in `mb/modal.py`.

- `DetailCatch`: `category -> task_id -> {'url': url}`.
- `DetailIndex`: `url -> task_id -> cached_data`.
- Step2 index values are page metadata dictionaries containing `data`, `next_url`, and `end`.
- Step4 index values are normalized product-row lists.
- Step4 writes its cache only after an index result or category-task mapping changes. A
  run served entirely by existing cache entries does not rewrite the cache files.

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
| Browser implementation failure | `_ljp/browser.py` |
| File naming or persistence issue | `_ljp/file_utils.py` |
| Product row shape issue | `_ljp/product.py` |
| Step2 pagination/cache behavior | `_ljp/mb/base/step2.py`, `_ljp/mb/modal.py` |
| Step4 threading/product cache behavior | `_ljp/mb/base/step4.py`, `_ljp/mb/modal.py` |
