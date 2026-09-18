from config import Tool

# ================= 维护区：自定义字段写在这里 =================
EXTRA_META_COLUMNS = [
    'Benefits(product.metafields.c_f.benefits)',
    'Application(product.metafields.c_f.application)',
    'Ingredients(product.metafields.c_f.ingredients)',
    'DETAILS(product.metafields.c_f.details)',
    'HOW TO USE(product.metafields.c_f.how_to_use)',
]

input_csv = Tool.File.path_add_site(r"res/picture.csv")
output_csv = Tool.File.path_add_site(r"data/wp_to_shopify.csv")

# =============================================================

from _ljp.mb.shopify import WpToShopify



class Pc(WpToShopify):
    EXTRA_META_COLUMNS = EXTRA_META_COLUMNS


pc = Pc(Tool, input_csv, output_csv)

if __name__ == '__main__':
    pc.run()





