# 1. 获取目录

本阶段将站点公开导航转换为产品分类任务的来源。仅在需要目录驱动采集的 Shopify、魔改 Shopify 和自建站模板中使用；Target 与 Amazon 的直接采集流程跳过此阶段。

## 实现边界

- 使用 `_ljp.mb.base.get_ml.CatalogParser` 和对应站点公开导出的 `CatCol`。解析器必须直接继承 `CatalogParser`，实现 `matches(html)` 与 `parse(html, collector)`；可复用的页面结构应加入对应 `_ljp.mb.*.catalog` 的内置 `CatCol.parser_types` 和公共导出，站点独有结构才在 `A_1_获取目录.py` 注册。禁止在模板脚本中复制已内置的解析逻辑。
- 可以继承 BaseCatalogParser 重写 f1,f2,f3来完成三级目录的解析，可以在f1之后来获取其余other  url
- `CatCol` 负责首页请求、原始 HTML 快照、失败时读取快照以及写出目录。解析器只负责节点过滤、名称、URL 和父子关系；不要在模板脚本中复制目录采集、扁平化或 JSON 保存逻辑。
- 普通 Shopify 使用 `_ljp.mb.shopify.CatCol`，魔改 Shopify 使用 `_ljp.mb.mg_shopify.CatCol`。应优先使用已内置的目录解析器；只有页面结构未覆盖时才新增站点解析器。确认结构可复用时，应将解析器加入对应 `_ljp.mb.*.catalog` 内置集合并同步公共导出.
- 普通与魔改 Shopify 只保留 collection URL，排除 product URL；无 URL 但包含子级的目录分组必须保留。站点特有的过滤条件必须以页面导航结构为依据，不能用“全部商品”入口代替分类树。
- 同时页面上有分类链接，但是不在导航栏上或者啥的，也必须获取，这些链接作为二级目录(重要),都挂载在自定义一级目录Other上，若存在Other则命名为Other2
- 同一个url但是在不同目录下的，需要保留
- 最终目录最多三级。按商品浏览语义合并超过三级的结构：仅用于页面布局或聚合的标题（例如 `Shop all`、`All products`、`Categories`）保留其自身的分类 URL，但其子链接提升为与该标题同级；有明确商品归属的父子分类（例如 `Hand care` -> `Hand lotion`）必须保留。不要因压缩层级而删除分类 URL 或将真实分类树完全扁平化。


## 数据和字段约束

解析过程的树节点形状是 `{"名称": {"url": "绝对 URL 或空字符串", "child": {...}}}`。最终由 `CatCol` / `Tool.to_ml_data()` 写为 `data/ml.json` 的扁平映射，例如 `{"一级,一级 二级": "collection URL"}`。每个映射键是不可拆分的分类原子值；其中逗号是 `Tool.to_ml_data()` 生成的层级编码，后续合并分类时不能拆分它，独立目录路径的组合使用 ` | `。

URL 必须经 `Tool.URL.add_site()` 规范为绝对链接。不要手写路径分隔符、原始 `save_json` 或直接维护 `ml.json`。

URL为站点基地址或带有'/'的基地址,全部替换为空字符。

禁止导航扁平化
## 流程和验收

1. 通过 `CatCol(Tool, base_url, Tool.File.path_add_site('data/ml.json'), snapshot_path).run()` 运行模板。只有调试需要完整脚本时才使用 `Tool.HTML.save_raw`。
2. 从首页 DOM、hydration/Next 数据或公开导航接口递归提取菜单，保留真实父子关系。发现 `Shop All` 或 `All Products` 后仍必须继续收集其他公开目录。
3. 验证至少两个非空分组和两个 collection 叶子；若站点确实没有更多分类，记录导航/采样页面证据。检查输出中没有产品、博客、页面等非 collection URL。
4. 阶段 2 直接读取该映射；不得将其替换为单一全量商品页或手工构造分类名称。
5. 必须输出结构，检查层级是否缺少，若用户给出层级，必须检查是否完成目标。统计扁平 JSON 键中的逗号分段，确认最大目录深度不超过三级；抽样确认被合并的布局标题及其原子分类处于同级，真实业务父子分类仍处于相邻层级。
