from config import Tool

# ================= 维护区：自定义字段写在这里 =================
EXTRA_META_COLUMNS = [
    'Fine Fragrance-Level Scents(product.metafields.c_f.fine_fragrance-level_scents)',
    'Non-toxic, Vegan Formulas(product.metafields.c_f.non-toxic,_vegan_formulas)',
    'Room-filling + Extended burn(product.metafields.c_f.room-filling_+_extended_burn)',
    'Candle Care(product.metafields.c_f.candle_care)'
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





