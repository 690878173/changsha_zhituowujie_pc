import pandas as pd

from config import Tool
from _ljp.mb.base import WpToShopify

# Add any site-specific Shopify metafield column names here.
extra_meta_columns = [
'Label info (product.metafields.c_f.label_info)',
       'Specifications (product.metafields.c_f.specifications)'
]


input_csv = Tool.File.path_add_site(r"res/picture.csv")
output_csv = Tool.File.path_add_site(r"data/wp_to_shopify.csv")

if __name__ == "__main__":
    step = WpToShopify(Tool)
    step.EXTRA_META_COLUMNS = list(extra_meta_columns)
    step.run()


    df = pd.read_csv(output_csv)


    def f_(x):
        if pd.isnull(x):
            return x

        return x.replace('Grocery Disclaimer:','')


    for i in extra_meta_columns:
        df[i] = df[i].apply(lambda x : f_(x))



    df.to_csv(output_csv, index=False)
