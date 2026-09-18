# 2. 获取详细链接

本阶段把分类页、平台搜索结果或已知产品任务转换为产品详情 URL 映射。普通/魔改 Shopify 和自建站使用 `GetDetail`；Target 和 Amazon 使用各自的直接采集器，但输出契约相同。

为了避免长时间运行，请你只做小范围的抓取后停止，然后进入后续步骤,即合理设置ts_num
## 输入、输出和缓存

- 输入 `data/ml.json` 的形状为 `{category: category_url 或 [category_url, ...]}`；直接模式输出的任务也必须归属到一个 `category`。
- 输出 `data/detail_url.json` 的形状为 `{category: [detail_url, ...]}`。每页和最终聚合均去重，类别和页面的遍历顺序保留，但不要依赖单页内的 URL 顺序。
- 使用模板提供的 `catch_path` 与 `index_path`。不要新增原始 JSON 缓存、手工构造 task ID 或将暂时失败写入成功缓存。

## 实现边界

- 在 `GetDetail` 子类实现 `fetch_page(page, params) -> (product_urls, next_url)`。仅当响应变化依赖参数时覆写 `build_params(page)`；返回值只包含影响响应的稳定参数，因为它参与页面缓存键。
- 已确认空页、终页或无效页调用 `page.set_end()`；临时请求/可预期解析错误记录后调用 `page.set_fail()`，返回空结果。不要把编程错误转换成失败状态。
- `before_request` 用于稳定的分类级预计算。只在必要时用浏览器 `self.get_page(...)`，普通 HTTP/API 优先 `Tool.get`。不要在模块级创建请求循环。
- 魔改 Shopify 只通过 `storefront_settings()` 提供公开解析到的 Storefront domain、token、版本及区域配置。无法验证 endpoint、domain 或 token 时停止本阶段并要求补充信息，不可改用 sitemap 或另写集合抓取流程。

## 流程和验收

先以 `ts_num=2` 验证两个输入分类与分页：下一页必须前进，终页必须被标记为 end，临时失败在下次运行可重试。检查 `data/detail_url.json`、`hc/2` 和失败记录，再恢复 `ts_num=None`。

最终抽查每个类别的 URL 是真实产品详情页，分类归属保留且跨类别重复产品不会造成重复请求。Amazon 先完成 ASIN 搜索与变体扩展；Target 使用其模板的关键词 collector，并在需要时处理可见浏览器人工验证。
