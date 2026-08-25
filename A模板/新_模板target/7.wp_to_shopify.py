from config import Tool
from _ljp.mb.base import Step8WpToShopify

# Add any site-specific Shopify metafield column names here.
extra_meta_columns = []


input_csv = Tool.File.path_add_site(r"res/picture.csv")
output_csv = Tool.File.path_add_site(r"data/wp_to_shopify.csv")

if __name__ == "__main__":
    step = Step8WpToShopify(Tool)
    step.EXTRA_META_COLUMNS = list(extra_meta_columns)
    step.run()
