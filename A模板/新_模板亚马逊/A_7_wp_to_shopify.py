from config import Tool
from _ljp.mb.base import WpToShopify

# Add any site-specific Shopify metafield column names here.
extra_meta_columns = [
'important_information(product.metafields.c_f.important_information)',
'productDescription(product.metafields.c_f.productdescription)',
'Product_details(product.metafields.c_f.product_details)',
'About_this_item(product.metafields.c_f.about_this_item)',
]
if __name__ == "__main__":
    step = WpToShopify(Tool)
    step.EXTRA_META_COLUMNS = list(extra_meta_columns)
    step.run()
