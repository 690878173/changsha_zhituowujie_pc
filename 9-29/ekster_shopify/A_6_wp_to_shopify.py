from config import Tool
from _ljp.mb.shopify import WpToShopify


input_file = Tool.File.path_add_site('res/picture.csv')
output_file = Tool.File.path_add_site('res/wp_to_shopify.csv')


if __name__ == '__main__':
    try:
        WpToShopify(Tool, input_file, output_file).run()
    finally:
        Tool.close()
