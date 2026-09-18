# 5. 生成 variable

本阶段只在结果包含 variation 行、但没有满足 Shopify 导入要求的父商品时执行。自建站、Target 和 Amazon 模板通常需要它；普通 Shopify、普通魔改 Shopify 通常跳过。魔改 Shopify 的 `MergeLinkVariants` 已产生父体时，不再重复生成。

默认直接运行即可，无需修改
## 输入输出和字段约束

- 输入为 `fwq/quchong.csv`，输出为 `fwq/variable.csv`。沿用模板既有的父体生成阶段；模板提供 `Variable` / `Step6Variable` 时优先使用它，不另写平行 CSV 转换器。
- 以 variation 的 `Parent` 作为父商品 `SKU`，插入一行 `Type=variable`、空 `Parent` 的父行，并让其紧邻且排在本家族 variation 行之前。simple 行原样保留。
- 当 `Categories` 存在时，它参与 family 分组，防止不同分类的同名父体误合并。每个变体的 `SKU`、价格、库存和变体属性必须保留在子行。
- `merge_fields` 仅用于应在父体合并的字段（通常为 `Images` 和属性值）；`description_fields` 只保留给父体，并清空子行中的相应值。图片使用 `Tool.config.images_split`，属性值按模板定义的分隔符处理。

## 验收

检查每个 variation 家族恰好有一个父行，父行在所有子行前，且 simple 产品未被改成 variable。父体图片/属性合并不应丢失任一子行资源；子行的库存、SKU、价格和选项仍各自正确。该行序必须保持至阶段 7 结束。
