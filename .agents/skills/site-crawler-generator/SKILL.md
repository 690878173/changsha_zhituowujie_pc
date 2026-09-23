---
name: site-crawler-generator
description: 为本仓库的电商站点创建、完善或验证采集和 Shopify 导出流水线。适用于 Shopify、魔改 Shopify、自建站、Target 和 Amazon 模板；不用于与本仓库模板无关的通用爬虫。
metadata:
  short-description: 按阶段构建站点采集流水线
---

# 站点采集流水线

为指定站点生成或修改模板时，先完整阅读 `docs/LJP_TOOL_GUIDE.md`。它是 `_ljp`、浏览器、缓存、字段和输出行为的主契约；只有指南缺少 API、运行行为冲突或需要排错时才查看实现源码。

然后阅读 [流程总契约](references/00-pipeline-contract.md)，根据站点类型选择实际需要的阶段。每个阶段都必须在开始前按需阅读对应 reference；网站不具备某个阶段的前置条件时，明确跳过它，不能用临时脚本替代。

| 阶段 | Reference | 何时阅读 |
| --- | --- | --- |
| 1. 获取目录 | [01-catalog.md](references/01-catalog.md) | 需要站点导航或分类目录时 |
| 2. 获取详细链接 | [02-detail-links.md](references/02-detail-links.md) | 从目录、搜索或平台任务生成产品详情任务时 |
| 3. 获取产品数据 | [03-product-data.md](references/03-product-data.md) | 实现或验证产品、变体和自定义字段解析时 |
| 4. 去重 | [04-deduplication.md](references/04-deduplication.md) | 合并重复 SKU 和分类时 |
| 5. 生成 variable | [05-variable-products.md](references/05-variable-products.md) | 源数据只有 variation 行且需要父商品时 |
| 6. 替换图片 | [06-image-replacement.md](references/06-image-replacement.md) | 图片已下载到 CDN 或需要重写图片 URL 时 |
| 7. WP 转 Shopify | [07-wp-to-shopify.md](references/07-wp-to-shopify.md) | 输出 Shopify 导入 CSV 时 |
| 8. Shopify 打折 | [08-shopify-discount.md](references/08-shopify-discount.md) | 生成折扣导入文件时 |
| 9. 生成分类 | [09-collections.md](references/09-collections.md) | 从标签生成 Shopify smart collections 时 |

所有字段、缓存、模板边界和验收要求以相应 reference 为准。

目录阶段输出最多三级；读取 [01-catalog.md](references/01-catalog.md) 中的业务合并规则，不能将仅用于页面布局的菜单标题当作额外分类层级。

运行对应步骤的脚本时，必须进入到脚本所在目录执行，避免生成的文件出现在根目录

调试 HTML/JSON 必须保存在站点 `ts/<阶段>/` 下，并以可反查的业务标识命名，例如
`<product-slug>_<parent-sku>_page.html` 与
`<product-slug>_<parent-sku>_<variant-sku>_variation.json`。禁止仅使用哈希、
序号或时间戳命名快照。
