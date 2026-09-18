"""
还原 roguefitness_cs_pro.json 扁平化数据为正常嵌套 Python 字典。

原理：
  - data 是一个 7777 元素的列表，通过"短路索引"去重存储。
  - data[0] 是全局索引表，指向各模块的起始位置。
  - 每个 dict 如果其 values 全为 int，则视为"映射表"（字段名→data下标），需递归解引用。
  - 列表中的 int 同样视为指针并解引用。
  - str / bool / None / float / int（叶子值）直接保留。
"""

import json


def resolve(flat_data, idx):
    """
    递归解引用：从 flat_data 的 idx 位置取出值并还原为嵌套结构。

    参数:
        flat_data: 扁平列表
        idx: 当前下标

    返回:
        还原后的 Python 对象（dict / list / 标量）
    """
    # 安全检查
    if idx is None or idx is False or idx is True:
        return idx
    if not isinstance(idx, int):
        # 非 int 直接返回（字符串、布尔、None 等已在数据中被引用）
        return idx

    value = flat_data[idx]

    # ---- 标量 ----
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return value   # 叶子 int/float，不做进一步解引用

    # ---- 列表 ----
    if isinstance(value, list):
        # 列表中如果全是 int，每个都是指针；否则按元素类型逐个处理
        return [resolve(flat_data, item) if isinstance(item, int) else item
                for item in value]

    # ---- 字典 ----
    if isinstance(value, dict):
        result = {}
        for key, val in value.items():
            if isinstance(val, int):
                result[key] = resolve(flat_data, val)
            else:
                # 极少数情况下字典值可能非 int（如包含字符串），原样保留
                result[key] = val
        return result

    # 兜底
    return value


def resolve_all(filepath):
    """
    读取 JSON 文件并还原所有模块数据。

    参数:
        filepath: roguefitness_cs_pro.json 路径

    返回:
        dict，键为模块名（categories/cms/products/...），值为还原后的结构化数据
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    flat_data = json.loads(raw['pinia'])

    # data[0] 是全局索引表
    index = flat_data[0]

    result = {}
    for module_name, start_idx in index.items():
        print(f'[resolve] {module_name} ...')
        result[module_name] = resolve(flat_data, start_idx)

    return result


def main():
    import os
    filepath = os.path.join(os.path.dirname(__file__), 'roguefitness_cs_pro.json')
    data = resolve_all(filepath)

    # ---- 打印摘要 ----
    for module, value in data.items():
        t = type(value).__name__
        if isinstance(value, dict):
            print(f'  {module}: dict, keys={list(value.keys())[:8]}')
        elif isinstance(value, list):
            print(f'  {module}: list, len={len(value)}')
        else:
            print(f'  {module}: {t}')

    # ---- 演示：取第一个商品 ----
    print('\n' + '=' * 60)
    print('示例：第一个商品')
    products_info = data['products']
    # products 是一个 dict，key=产品ID, value=商品对象
    first_id = list(products_info['products'].keys())[0]
    first_product = products_info['products'][first_id]
    print(json.dumps(first_product, indent=2, ensure_ascii=False)[:1500])

    # ---- 保存结果 ----
    out_path = os.path.join(os.path.dirname(__file__), 'roguefitness_resolved.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'\n已保存到: {out_path}')

    return data


if __name__ == '__main__':
    main()
