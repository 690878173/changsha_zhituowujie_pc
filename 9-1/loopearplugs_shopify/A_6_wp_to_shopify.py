from config import Tool

# ================= 维护区：自定义字段写在这里 =================
EXTRA_META_COLUMNS = [
    'What you get (product.metafields.c_f.what_you_get)',
    'Understanding noise reduction (product.metafields.c_f.understanding_noise_reduction)',
]

input_csv = Tool.File.path_add_site(r"res/picture.csv")
output_csv = Tool.File.path_add_site(r"res/wp_to_shopify.csv")

# =============================================================

from _ljp.mb.shopify import WpToShopify



class Pc(WpToShopify):
    EXTRA_META_COLUMNS = EXTRA_META_COLUMNS


pc = Pc(Tool, input_csv, output_csv)

if __name__ == '__main__':
    pc.run()





