
from config import Tool

# 当前 res 中的 3 折文件。Shopify_dz 会以 Variant Compare At Price
# 作为原价重新计算 Variant Price，因此不会叠加旧的 3 折。
input_path = Tool.File.path_add_site(
    'res/notyourmothers_new_shopify70%off_zst_1.csv'
)
# 4 折对应 60%off，保留原 3 折文件不覆盖。
output_path = Tool.File.path_add_site(
    'res/notyourmothers_new_shopify60%off_zst_1.csv'
)

Tool.File.create_dir(output_path)

from _ljp.mb.zj import Shopify_dz



if __name__ == '__main__':
    Shopify_dz(Tool, input_path, output_path).run()

    # from _ljp import split_shopify_csv_large
    #
    # products_per_file = 600  # 每个文件的产品数
    # chunksize = 100000  # 每次分块读取行数
    #
    # split_shopify_csv_large(input_path=output_path,
    #                         products_per_file=products_per_file,
    #                         chunksize=chunksize)
