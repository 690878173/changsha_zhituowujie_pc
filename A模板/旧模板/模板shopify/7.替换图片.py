import pandas as pd
import re
import os
import hashlib
from config import Tool

csv_input_path = Tool.File.path_add_site(r'res/quchong.csv')
failed_images_path = Tool.File.path_add_site(r'data/failed_images.txt')
csv_output_path = Tool.File.path_add_site(r'res/picture.csv')


web_name = Tool.site + '_ljp'
new_url_base = f'https://cdn.zhimatrix.com/{web_name}/images/'


def run():
    df = pd.read_csv(csv_input_path)

    failed_images = set()
    if os.path.exists(failed_images_path) and os.path.isfile(failed_images_path):
        try:
            with open(failed_images_path, 'r', encoding='utf-8') as f:
                failed_images = {line.strip() for line in f if line.strip()}
            print(f"成功读取失败图片列表，共 {len(failed_images)} 个失败URL")
        except Exception as e:
            print(f"读取失败图片列表时出错: {e}，将忽略")
    else:
        print(f"未找到失败图片列表文件 {failed_images_path}，将忽略")

    df['Images'] = df['Images'].apply(lambda x: to_new_url(x, failed_images))

    required_columns = ['Type', 'SKU', 'Parent', 'Images']

    if all(col in df.columns for col in required_columns):
        # 填充 NaN 以避免字符串匹配时报错
        df['Type'] = df['Type'].fillna('').astype(str)
        df['SKU'] = df['SKU'].fillna('').astype(str)
        df['Parent'] = df['Parent'].fillna('').astype(str)
        df['Images'] = df['Images'].fillna('').astype(str)

        # ==========================================
        # (A) 处理无图父类：如果 variable 没有图，删除它以及它的所有子类
        # ==========================================
        invalid_parents_mask = (df['Type'].str.lower() == 'variable') & (df['Images'] == '')
        invalid_parent_skus = set(df[invalid_parents_mask]['SKU'])

        # 删除无图的父类本身
        df = df[~invalid_parents_mask]
        # 删除属于这些无图父类的所有子类数据
        df = df[~df['Parent'].isin(invalid_parent_skus)]

        # ==========================================
        # (B) 处理无图子类：如果 variation 没有图，且该父类下包含 >1 个子类，才删除
        # ==========================================
        # 1. 先统计当前数据中，每个 Parent 下有几个 variation
        variations_only = df[df['Type'].str.lower() == 'variation']
        variation_counts = variations_only.groupby('Parent').size()

        # 2. 将统计的数量映射回原数据，生成辅助列 'var_count'
        df['var_count'] = df['Parent'].map(variation_counts).fillna(0)

        # 3. 标记需要删除的 variation：类型为变体 AND 没图片 AND 同级变体数量大于1
        invalid_variation_mask = (
                (df['Type'].str.lower() == 'variation') &
                (df['Images'] == '') &
                (df['var_count'] > 1)
        )

        # 执行删除
        # df = df[~invalid_variation_mask]

        # 删掉刚刚生成的辅助列，保持表结构干净
        df = df.drop(columns=['var_count'])

        print(f"因父类无图，连带移除了 {len(invalid_parent_skus)} 组商品(含子类)。")
    else:
        print(f"警告: 数据中缺失 {required_columns} 中的部分列，无法执行无图删除逻辑。")

    print(f"清理后数据总行数: {len(df)}")

    # 5. 将结果保存为csv文件
    df.to_csv(csv_output_path, index=False, encoding='utf-8')
    print(f"处理完成，结果已保存到 {csv_output_path}")

def hash_image_url(image_url):
    url_hash = hashlib.md5(image_url.encode("utf-8")).hexdigest()
    return f"{url_hash}.webp"

def to_new_url(image_urls, failed_set):
    """
    将图片 URL 转换成新的链接，同时跳过失败的图片
    """
    if pd.isna(image_urls) or str(image_urls).strip() == "":
        return ""
    new_image_urls = []
    for url in str(image_urls).split(Tool.config.images_split):
        url = url.strip()
        if not url or url in failed_set:
            continue


        filename = hash_image_url(url)
        filename = filename.split('?')[0]

        new_url = f"{new_url_base}{filename}"
        print(f'新的图片链接: {new_url}, 原始链接: {url}')
        new_image_urls.append(new_url)

    return ','.join(new_image_urls)


if __name__ == "__main__":
    run()
    # wb = Tool.File.Web(csv_output_path)
    # wb.run()