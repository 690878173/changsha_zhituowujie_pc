from config import Tool

# ================= 维护区：自定义字段写在这里 =================
EXTRA_META_COLUMNS = [
    'Fit Carry and Sizing(product.metafields.c_f.fit_carry_and_sizing)',
    'Fabric and Care(product.metafields.c_f.fabric_and_care)',
    'Safety Information(product.metafields.c_f.safety_information)',
    'Sizing(product.metafields.c_f.sizing)',
    'Fabric and Feel(product.metafields.c_f.fabric_and_feel)',
    'Deluxe Features(product.metafields.c_f.deluxe_features)'
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





