# 9. 生成分类

本阶段基于 Shopify 产品 CSV 的 `Tags` 生成 smart collection 导入文件。使用模板的 `Collection`，是纯文件转换；它不应重新推断阶段 1 的网站分类树。

默认直接运行即可，无需修改
## 输入输出和字段约束

- 输入为阶段 8 的折扣 CSV；跳过折扣时输入阶段 7 的 Shopify CSV。输出为 `Tool.File.fl_path()` 对应的 collection CSV 文件或分片文件。
- `Tags` 是唯一的分类来源。按标签值大小写不敏感去重；空标签不生成 collection，也不从产品名称、分类路径或 description 猜测标签。
- 单个 collection 输出文件最多 99 条 smart collection 行。超过上限时由模板分片，不能强行写入超过限制的一份文件。

## 验收

检查每个非空、去重后的标签恰好对应一个 smart collection 规则，大小写差异不产生重复规则。确认所有输出分片均不超过 99 行，且名称、规则和输入标签能逐项追溯。
