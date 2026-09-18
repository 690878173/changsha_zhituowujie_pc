# 3. 获取产品数据

本阶段将详情任务解析为标准 WooCommerce 风格产品行，是字段定义和站点解析逻辑的唯一入口。使用 `Get_Product` 子类的 `fetch_product(url, category)`；普通/魔改 Shopify 只补充模板允许的 `zdy_zd(url, html_text)` 与 `storefront_settings()`，自建站在其 `fetch_product` 钩子内解析页面和变体。

自建站尽量保留_T的结构，方便观察和检验，同时方法名也知道是干什么的

为了避免长时间运行，请你只做小范围的抓取后停止，然后进入后续步骤,即合理设置ts_num
## 输出字段约束

使用 `Tool.Product.Simple(...).to_dic()` 或 `Tool.Product.Variation(...).to_dic()` 生成行。标准字段包括：

| 字段组 | 约束                                                                                              |
| --- |-------------------------------------------------------------------------------------------------|
| 标识 | `Type` 为 `simple` 或 `variation`；变体必须保留 `Parent`、`SKU` 及 Attribute 名称和值                          |
| 价格 | 使用 `Tool.clean_price`；不能以空值或零值混淆缺失价格与有效价格,必须抓取原价                                                |
| 内容 | `Description` 和文本型自定义字段用 `Tool.HTML.clean_product_desc`（lxml 节点）或 `clean_product_desc_str`（字符串）清洗 |
| 图片 | 传入图片 URL 列表，由 `Tool.Product` 转为相对 URL 已解析的 `Images`；必要时在配置中设置正确的 `images_split`，必须抓取多个图片链接，     |
| 库存 | 未知时传 `None` 使用默认库存；已知无货必须传 `stock=0`，零值不可丢失                                                     |
| 来源 | 内部 `url` 仅出现在测试输出，最终 `res/result.csv` 会移除它                                                      |

自定义钩子只返回逻辑字段字典或 `None`，例如 `{"Care": "...", "Materials": "..."}`。不要返回整行、手写 `product.metafields` 列名、调用 `build_custom_field_name`，或写入 `shopify_product[Tool.custom_key]`。框架负责命名；字段值缺失时返回空字符串，不能令整件商品失败。

禁止抓取不在上述表内的非自定义字段。

附加产品忽略，不作为变体字段，
## 缓存和错误约束
Step4 写缓存前按 `Type` 校验必要字段：`simple`（或未填 Type）要求
`SKU`、`Name`、`Description`、`Images` 及正数 `Sale price`、`Regular price`；
`variable` 要求前四个字段，不要求价格；`variation` 只要求 `SKU`、`Name`、
`Parent` 和正数 `Sale price`、`Regular price`。任一要求字段为空则失败，不写缓存；
通过的行统一写入 `Stock=1000`。不校验图片 URL 格式或描述来源。

返回单个产品行/对象或非空列表；对象必须支持 `to_dic()`。`None`、空列表或没有字典的列表均为解析失败，不缓存成功结果，交由 Step4 写入 `fail/`。同一 URL 在多个分类中只解析一次，框架再为各分类克隆行并覆盖 `Categories`；不可自行合并或手工写缓存。

HTTP 优先 `Tool.get`，浏览器只用于需要自动化的页面；Playwright 和 DrissionPage 原生 API 不可混用。遇到验证页用同一后端的 `Tool.browser.restart_context()`，页面和 session 不得跨线程传递。

## 字段分析和验收

先用少量任务运行并保存原始 HTML/JSON 与 `res/ts_res.csv`。调试快照文件名必须使用可反查的业务标识，例如 `<product-slug>_<parent-sku>_page.html` 与 `<product-slug>_<parent-sku>_<variant-sku>_variation.json`；禁止仅用哈希、序号或时间戳命名。通过 `scripts/analyze_fields.py <快照> --output analysis/fields.json` 盘点候选字段，手工确认字段语义、来源、空值策略和变体归属；HTML 报告只是候选，不可直接当字段定义。

至少用两个不同产品验证字段值。确认 `res/ts_res.csv` 含内部 `url` 用于排错，`res/result.csv` 已移除它；标准列、每个预期自定义列和 `fail/` 记录均正确。阶段 7 的 `EXTRA_META_COLUMNS` 只加入已验证且有值的最终自定义列。
