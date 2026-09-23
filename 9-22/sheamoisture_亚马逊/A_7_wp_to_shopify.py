from config import Tool
from _ljp.mb.base import WpToShopify

# Add any site-specific Shopify metafield column names here.
extra_meta_columns = [
   'Important_information (product.metafields.c_f.zdy_tabs1)',
       'Product_description (product.metafields.c_f.zdy_tabs2)',
       'Product_details (product.metafields.c_f.zdy_tabs3)',
       'About_this_item (product.metafields.c_f.zdy_tabs4)',
]
if __name__ == "__main__":
    step = WpToShopify(Tool)
    step.EXTRA_META_COLUMNS = list(extra_meta_columns)
    step.run()
