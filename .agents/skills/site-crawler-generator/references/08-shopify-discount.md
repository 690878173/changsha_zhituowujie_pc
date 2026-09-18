# 8. Shopify 打折

本阶段从 Shopify 导入 CSV 生成折扣版 CSV。仅在需要按站点 `zk` 输出折扣价格时执行，使用模板的 `Shopify_dz`，不在产品采集或 WP 转换阶段直接改价。

默认直接运行即可，无需修改
## 输入输出和字段约束

- 输入为阶段 7 的 Shopify CSV，输出为 `Tool.File.dz_path()`，文件名含 `(1 - zk) * 100` 的折扣百分比。
- `zk` 必须在 `0..1`，来自站点 `config.toml`。`Variant Compare At Price` 必须能解析为数值；价格计算为 `Variant Price = Variant Compare At Price * Tool.zk`，保留两位小数。
- 任一 handle 的 `Variant Compare At Price` 为数值零时，移除该 handle 的所有行。不要只删除单一变体，否则会破坏 Shopify family。

## 验收

抽查多个 handle：折扣价等于 compare-at price 乘以 `zk` 并正确四舍五入，compare-at price 保持可追溯。确认零 compare-at 的完整 handle 已移除，非零产品的父体和变体关系仍保持完整。
