from config import Tool
from _ljp.mb.base import WpToShopify

# Add any site-specific Shopify metafield column names here.
extra_meta_columns = [
    'Label info (product.metafields.c_f.zdy_tabs1)','Specifications (product.metafields.c_f.zdy_tabs2)'
]


input_csv = Tool.File.path_add_site(r"res/picture.csv")
output_csv = Tool.File.path_add_site(r"data/wp_to_shopify.csv")

if __name__ == "__main__":
    step = WpToShopify(Tool)
    step.EXTRA_META_COLUMNS = list(extra_meta_columns)
    step.run()

    import pandas as pd

    df = pd.read_csv(output_csv)


    def _f(x):
        if pd.isnull(x):
            return x
        return Tool.HTML.clean_product_desc_str(x)


    for col in extra_meta_columns:
        df[col] = df[col].apply(lambda x: _f(x))

    df.to_csv(output_csv)
