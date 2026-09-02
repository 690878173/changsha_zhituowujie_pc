import pandas as pd
from config import Tool

# 原始 CSV 路径
input_path = Tool.File.path_add_site('data/wp_to_shopify.csv')
# 输出 CSV 路径
output_path = Tool.File.dz_path()

Tool.File.create_dir(output_path)

from _ljp.mb.shopify import Shopify_dz


pc = Shopify_dz(Tool, input_path, output_path)
if __name__ == '__main__':
    pc.run()

    # from _ljp import split_shopify_csv_large
    #
    # products_per_file = 600  # 每个文件的产品数
    # chunksize = 100000  # 每次分块读取行数
    #
    # split_shopify_csv_large(input_path=output_path,
    #                         products_per_file=products_per_file,
    #                         chunksize=chunksize)