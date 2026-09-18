from config import Tool
from _ljp.mb.base import WpToShopify


EXTRA_META_COLUMNS = [
    "Size Range(product.metafields.c_f.size_range)",
    "Age Range(product.metafields.c_f.age_range)",
    "Baby Weight Range(product.metafields.c_f.baby_weight_range)",
    "Baby Weight(product.metafields.c_f.baby_weight)",
    "Retailers(product.metafields.c_f.retailers)",
]

input_file = Tool.File.path_add_site("res/picture.csv")
output_file = Tool.File.path_add_site("data/wp_to_shopify.csv")


class Pc(WpToShopify):
    EXTRA_META_COLUMNS = EXTRA_META_COLUMNS


if __name__ == "__main__":
    Pc(Tool, input_file, output_file).run()
