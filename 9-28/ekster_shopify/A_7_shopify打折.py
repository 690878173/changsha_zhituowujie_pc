from config import Tool
from _ljp.mb.shopify import Shopify_dz


input_file = Tool.File.path_add_site('res/wp_to_shopify.csv')
output_file = Tool.File.dz_path()


if __name__ == '__main__':
    try:
        Shopify_dz(Tool, input_file, output_file).run()
    finally:
        Tool.close()
