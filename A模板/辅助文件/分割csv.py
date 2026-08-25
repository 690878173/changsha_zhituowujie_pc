import os
import pandas as pd
from tqdm import tqdm

def split_shopify_csv_large(input_file, output_dir, products_per_file=1350, chunksize=100000):
    """
    按Handle拆分大型Shopify CSV文件，每个输出文件包含指定数量的产品。
    支持分块读取，不会因数据过大而崩溃。

    参数:
        input_file (str): 输入Shopify CSV文件路径
        output_dir (str): 输出文件夹路径
        products_per_file (int): 每个文件包含的产品数（按Handle计）
        chunksize (int): 每次读取的行数（建议10万行）
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"🔍 正在扫描唯一产品（Handle）...")

    # 第一次扫描，只提取所有 Handle（节省内存）
    handle_set = set()
    for chunk in tqdm(pd.read_csv(input_file, dtype=str, chunksize=chunksize)):
        if 'Handle' not in chunk.columns:
            raise ValueError("❌ 输入文件中缺少 'Handle' 列。请确认是Shopify格式。")
        handle_set.update(chunk['Handle'].dropna().unique())

    handles = sorted(list(handle_set))
    total_products = len(handles)
    print(f"✅ 检测到 {total_products} 个唯一产品 Handle。")

    # 拆分批次
    num_batches = (total_products + products_per_file - 1) // products_per_file
    print(f"📦 将生成 {num_batches} 个文件，每个文件约 {products_per_file} 个产品。")

    # 开始逐批导出
    for batch_index in range(num_batches):
        start = batch_index * products_per_file
        end = min((batch_index + 1) * products_per_file, total_products)
        batch_handles = set(handles[start:end])
        output_file = os.path.join(output_dir, f"products_part_{batch_index + 1}.csv")

        print(f"\n🧩 正在生成第 {batch_index + 1}/{num_batches} 个文件: {output_file}")
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
            header_written = False
            for chunk in pd.read_csv(input_file, dtype=str, chunksize=chunksize):
                filtered_chunk = chunk[chunk['Handle'].isin(batch_handles)]
                if not filtered_chunk.empty:
                    filtered_chunk.to_csv(f_out, index=False, header=not header_written, mode='a', encoding='utf-8-sig')
                    header_written = True

        print(f"✅ 已保存: {output_file}  （包含 {len(batch_handles)} 个产品）")

    print("\n🎉 拆分完成！所有文件已保存到：", output_dir)


if __name__ == "__main__":
    # ======== 配置部分 ========
    input_csv = r"J:\changsha\8-17到8-22\asics_自建\res\asics_70%off_ljp.csv"  # 输入文件路径
    output_folder = r"J:\changsha\8-17到8-22\asics_自建\res\分割"  # 输出文件夹
    products_per_file = 318  # 每个文件的产品数
    chunksize = 100000  # 每次分块读取行数
    # =========================

    split_shopify_csv_large(input_csv, output_folder, products_per_file, chunksize)
