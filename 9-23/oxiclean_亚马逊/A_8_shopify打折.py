from config import Tool
from _ljp.mb.base import Shopify_dz

input_path = Tool.File.path_add_site('data/wp_to_shopify.csv')
# 输出 CSV 路径
output_path = Tool.File.dz_path()

if __name__ == "__main__":
    Shopify_dz(Tool, input_path=input_path, output_path=output_path).run()


    # from _ljp import split_shopify_csv_large
    #
    # products_per_file = 600  # 每个文件的产品数
    # chunksize = 100000  # 每次分块读取行数
    #
    # split_shopify_csv_large(input_path=output_path,
    #                         products_per_file=products_per_file,
    #                         chunksize=chunksize)
