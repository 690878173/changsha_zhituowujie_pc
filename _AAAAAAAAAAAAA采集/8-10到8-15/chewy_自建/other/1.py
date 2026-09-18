#!/usr/bin/env python3
"""
从 Chewy 打包 JS 文件中提取并执行 Oc 函数，获取商品分类目录。
原理：提取函数定义 -> mock 外部依赖 -> 使用 execjs 编译执行 -> 解析返回值。
输出格式：{name:{url:url,child:{name:{url:url,child:{}}}}}
"""

import re
import json
import execjs  # 新增导入


def extract_oc_function(js_path: str) -> str:
    """从 JS 文件中用括号匹配提取 Oc 函数的完整定义。"""
    with open(js_path, 'r', errors='replace') as f:
        content = f.read()

    start = content.find('Oc = function')
    if start == -1:
        raise ValueError("未找到 Oc 函数")

    brace_start = content.find('{', start)
    depth = 0
    end = brace_start
    for i in range(brace_start, len(content)):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    return content[start:end]


def build_executable_js(oc_func: str) -> str:
    """
    构造可编译的 JS 代码：mock 外部依赖 + 原始 Oc 函数定义。
    （不包含调用逻辑，调用由 execjs 的 .call() 完成）
    """
    return r"""
// ===== Mock 外部依赖（Oc 函数引用的外部变量）=====
var Y = { Rg: "isFeatureEnabled" };   // 任意字符串键，用于读取参数属性
var E = { Z: function(x) { return x; } };  // 恒等函数，原函数用于数组展开
var Cc = { items: [] };                // 空数组，使动态过滤部分返回空
var kc = [];                           // 空数组，过滤条件
var _c = {};                           // 空对象，名称映射

// ===== 原始 Oc 函数定义 =====
""" + oc_func


def execute_js(js_code: str, args: dict = None) -> list:
    """
    使用 execjs 编译 JS 代码，并调用 Oc 函数。
    返回 Oc({}) 的结果（取前两个数组）。
    """
    if args is None:
        args = {}

    # 编译 JS 上下文
    ctx = execjs.compile(js_code)

    # 调用 Oc 函数，传入参数（Python dict 会自动转为 JS 对象）
    result = ctx.call('Oc', args)

    # 只取前两个数组（商品分类 + 药房），第三个数组是动态营销内容
    product_categories = result[:2]
    return product_categories


def clean_structure(data: list) -> dict:
    """
    【修改重点】转换成 {name: {"url": "...", "child": {...}}} 结构
    """
    def build_dict(node_list) -> dict:
        tree = {}
        for node in node_list:
            name = node.get("name", "").strip()
            if not name:
                continue
            child_nodes = node.get("items", [])
            tree[name] = {
                "url": node.get("url", ""),
                "child": build_dict(child_nodes)
            }
        return tree

    flat_list = []
    for group in data:
        for item in group:
            # 排除营销入口（Deals、New Arrivals）
            if item.get('name') in ('Deals', 'New Arrivals'):
                continue
            flat_list.append(item)

    return build_dict(flat_list)


def print_tree(categories: dict):
    """适配字典树形打印"""
    def walk(node_dict, prefix='', is_last=True):
        items = list(node_dict.items())
        for idx, (name, info) in enumerate(items):
            last_flag = (idx == len(items) - 1)
            connector = '└── ' if last_flag else '├── '
            url = f"  ({info['url']})" if info['url'] else ''
            print(f"{prefix}{connector}{name}{url}")

            child_dict = info["child"]
            if child_dict:
                ext = '    ' if last_flag else '│   '
                walk(child_dict, prefix + ext, last_flag)

    walk(categories)


def main():
    js_path = r'J:\changsha\8-10到8-15\chewy_自建\hc\1jscode.js'

    # 1. 提取函数
    print("正在提取 Oc 函数...")
    oc_func = extract_oc_function(js_path)
    print(f"  函数长度: {len(oc_func)} 字符")

    # 2. 构造可编译的 JS（含 mock 和定义）
    js_code = build_executable_js(oc_func)

    # 3. 执行（使用 execjs）
    print("正在通过 execjs (Node.js) 执行函数...")
    raw_data = execute_js(js_code, {})  # 传入空对象作为参数
    print(f"  返回 {len(raw_data)} 个数组组")

    # 4. 清理结构【现在输出是 dict，不再是 list】
    categories = clean_structure(raw_data)

    # 5. 统计层级节点数量
    def count_node(tree, level, counter):
        counter[level] = counter.get(level, 0) + len(tree)
        for info in tree.values():
            if info["child"]:
                count_node(info["child"], level + 1, counter)

    counter = {}
    count_node(categories, 1, counter)

    print(f"\n===== 提取结果 =====")
    for lvl in sorted(counter):
        label = {1: '一级', 2: '二级', 3: '三级', 4: '四级'}.get(lvl, f'{lvl}级')
        print(f"  {label}分类: {counter[lvl]} 个")
    print(f"  总计: {sum(counter.values())} 个节点")

    # 6. 打印树形预览
    print(f"\n===== 目录预览 =====")
    print_tree(categories)

    # 7. 保存 JSON
    out_path = r'J:\changsha\8-10到8-15\chewy_自建\hc\2jscode.json'
    output_data = categories  # 直接就是目标嵌套字典
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n已保存到: {out_path}")


if __name__ == '__main__':
    main()
