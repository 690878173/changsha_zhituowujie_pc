# 7. WP 转 Shopify

本阶段将标准 WooCommerce 风格产品行转换为 Shopify 导入 CSV。使用 `WpToShopify`，它以流式方式处理大文件；输入必须保留产品 family 的顺序。

## 输入输出和字段约束

- 输入为阶段 6 输出，或明确跳过图片替换后的前一阶段 CSV；输出通常为 `data/wp_to_shopify.csv`。使用模板的输入输出路径，不另建转换脚本。
- 每个可变产品 family 必须是 `variable` 父行后紧跟其 `variation` 子行。不要在转换前排序、按任意行数切块，或拆分父子家族；转换器会跨 pandas chunk 保留最后一个未完成家族。
- `EXTRA_META_COLUMNS` 是 Shopify 最终导出的附加列白名单。只写完整最终列名，例如 `Name(product.metafields.c_f.name)`；只加入阶段 3 已验证存在且有值的列。保持动态列，不用固定 `fieldnames` 过滤掉自定义字段。
- 保留 `Handle` 与变体关联字段的转换结果；同次运行中 handle 冲突检测跨 chunk 生效，不能每个 chunk 独立重置。

## 验收

检查 Shopify CSV 包含所有预期父体、变体、图片、分类和 `EXTRA_META_COLUMNS`；抽查跨 chunk 的 product family，确认最后一个家族没有丢失变体。输出中不存在无父体的变体或重复 handle 导致的不同产品合并。
