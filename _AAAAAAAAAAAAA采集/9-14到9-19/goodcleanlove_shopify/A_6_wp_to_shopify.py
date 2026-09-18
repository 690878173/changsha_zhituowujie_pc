from config import Tool

# ================= 维护区：自定义字段写在这里 =================
EXTRA_META_COLUMNS = [
    'Ingredients(product.metafields.c_f.ingredients)',
    'How to Use(product.metafields.c_f.how_to_use)',
    'Bio-Match Technology(product.metafields.c_f.bio-match_technology)',
    'Benefits(product.metafields.c_f.benefits)'
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





