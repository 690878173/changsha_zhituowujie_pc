from config import Tool

# ================= 维护区：自定义字段写在这里 =================
EXTRA_META_COLUMNS = [
    'Product Details(product.metafields.c_f.product_details)',
    'Fabric and Fit(product.metafields.c_f.fabric_and_fit)',
    'Features(product.metafields.c_f.features)',
    'Same legendary shorts—just better(product.metafields.c_f.same_legendary_shorts—just_better)',
    'Heritage Wash(product.metafields.c_f.heritage_wash)',
    'The Details(product.metafields.c_f.the_details)',
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





