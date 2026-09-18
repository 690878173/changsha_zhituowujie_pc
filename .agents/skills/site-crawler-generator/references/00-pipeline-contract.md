# 流程总契约

先完整阅读 `docs/LJP_TOOL_GUIDE.md`，再复制最接近的 `A模板` 模板。使用 `scripts/generate_site_template.py` 创建 `<site>_<type>` 目录；它默认不覆盖现有目录。站点 URL、请求头、Cookie、Storefront token 和浏览器设置只能存于站点 `config.toml` 或允许的站点 Step，不能写进 `_ljp` 默认配置或 Skill 文件。

## 类型与阶段选择

| 类型 | 使用模板 | 必要或常用阶段 | 允许省略的阶段 |
| --- | --- | --- | --- |
| `shopify` | `新_模板shopify` | 1, 2, 3, 4, 6, 7, 8, 9 | 5|
| `mg_shopify` | `新_模板魔改shopify` | 1, 2, 3, 4, 6, 7, 8, 9 | 5 |
| `self_hosted` | `新_模板自建` | 1 至 9 | 5 仅在没有 variation 家族时可省略|
| `target` | `新_模板target` | 2, 3, 4, 5, 6, 7, 8, 9 | 1；6 前必须先下载图片 |
| `amazon` | `新_模板亚马逊` | 搜索 ASIN、展开变体、3, 4, 5, 6, 7, 8, 9 | 1、通用 2 |

魔改 Shopify 若产品以独立 URL 形式发布选项，先在阶段 4 前运行 `MergeLinkVariants`；它生成的父/变体家族替代阶段 5。Target 和 Amazon 是直接采集模式，详情任务仍必须保存为标准的 `{category: [detail_task, ...]}` 形状。

## 跨阶段约束

- 不增加模块级抓取循环、平行缓存字典、原始文件读写或平行 CSV 导出。请求、缓存和持久化均通过模板与 `Tool` 公开 API 完成。
- 所有 Step 传入同一个 `Tool`。Step4 的浏览器、HTTP session 和页面均为线程本地资源，不得跨线程传递；在脚本或一键运行器结束时只关闭一次。
- 使用逻辑路径，例如 `data/detail_url.json`；通过 `Tool.File` 处理 site 前缀与原子保存。需要重新抓取时使用 Step 的 `flush=True`，不删除用户缓存。
- 从低成本样本开始：目录和详情阶段先限制类别，产品阶段先限制少量任务；通过后恢复全量。每一阶段完成后检查其输入、输出、失败文件和缓存，再执行下一阶段。
- 站点专用请求参数、选择器和解析代码只能位于模板公开的站点类/钩子。普通 Shopify 与魔改 Shopify 优先使用现有 Step；自建站只在其 `GetDetail`/`Get_Product` 子类的钩子中实现页面逻辑。
- 每次处理前保持行序，除非所属阶段明确允许改变它。特别是 variable 父行必须排在其 variation 子行之前，直到 Shopify 转换完成。
- 中间生成的调试产物统一存放在 站点目录下的 ts文件夹下的阶段文件夹下，不要平铺到目录下
- 所有实现方法都需要在钩子内实现，以及钩子所依附的类内实现，禁止在外部实现
## 通用验收

交付前，从脚本所在目录用 `J:\changsha\.venv\Scripts\python.exe` 按已选阶段顺序运行。每个输出应存在、非空且可被下一阶段读取；失败任务必须保留为待重试状态，不能伪装成成功缓存。联网或浏览器依赖不可用时，至少使用已保存的 HTML/JSON 和最小 CSV 样本验证解析及转换。

不遗留 `TODO`、示例 XPath、`NotImplementedError` 或占位站点配置。不要输出 Token、Cookie 或其他凭证。
