# 4. 去重

本阶段对 `res/result.csv` 做 SKU 级去重，并合并同一商品在多个分类中的归属。使用模板的 `Quchong`；它是纯文件转换，不发起站点请求。

默认直接运行即可，无需修改
## 输入输出和字段约束

- 输入为阶段 3 输出的 `res/result.csv`，输出通常是 `fwq/quchong.csv`。保持模板已配置的路径，不用独立 pandas 脚本替代。
- `SKU` 是分组键；同 SKU 的 `Categories` 按首次出现顺序合并，其他字段以首行保留并对冲突发出警告。空 SKU 也会组成一个分组，因此产品阶段应尽力提供稳定 SKU。
- 保留原始第一出现顺序。不要排序、删除 product family 的行序，或按分类路径中的逗号拆分后再合并。

## 特殊流程

魔改 Shopify 若一个可售选项被拆成 `Product Name | Variant Value` 的独立产品 URL，先运行 `MergeLinkVariants`，再运行普通 `Quchong`。该转换先合并 SKU 和分类，随后产生 `variable` 父行与 `variation` 子行；已有原生属性时保留它们，否则将 URL 后缀设为 `Variant` 属性。

## 验收

检查输出行数不增加，重复 SKU 只保留一份，分类都仍可追溯。随机检查存在冲突警告的 SKU，确认首行保留符合业务预期。后续如果要生成父商品，输入必须仍然是稳定的 variation 家族顺序。
