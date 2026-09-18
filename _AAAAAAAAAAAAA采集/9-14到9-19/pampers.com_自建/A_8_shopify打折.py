
from config import Tool
from _ljp.mb.base import Shopify_dz


input_file = Tool.File.path_add_site("data/wp_to_shopify.csv")
output_file = Tool.File.dz_path()


if __name__ == "__main__":
    Shopify_dz(Tool, input_file, output_file).run()
