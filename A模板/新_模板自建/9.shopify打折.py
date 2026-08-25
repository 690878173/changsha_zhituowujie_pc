
from config import Tool

# 原始 CSV 路径
input_path = Tool.File.path_add_site('data/wp_to_shopify.csv')
# 输出 CSV 路径
output_path = Tool.File.dz_path()

Tool.File.create_dir(output_path)

from _ljp.mb.zj import Step9Discount



if __name__ == '__main__':
    Step9Discount(Tool, input_path, output_path).run()