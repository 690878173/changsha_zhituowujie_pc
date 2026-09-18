from config import Tool

# ================= 维护区：自定义字段写在这里 =================
EXTRA_META_COLUMNS = [
    'key benefits(product.metafields.c_f.key_benefits)',
    "who it's good for(product.metafields.c_f.who_it's_good_for)",
    'how to use(product.metafields.c_f.how_to_use)',
    'claims(product.metafields.c_f.claims)',
    'clinical claims(product.metafields.c_f.clinical_claims)'
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





