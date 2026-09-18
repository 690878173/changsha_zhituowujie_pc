from config import Tool
from _ljp.mb.base import WpToShopify

# Add any site-specific Shopify metafield column names here.
extra_meta_columns = [
'important_information(product.metafields.c_f.important_information)','productDescription(product.metafields.c_f.productdescription)',
    'Product_details(product.metafields.c_f.product_details)','About_this_item(product.metafields.c_f.about_this_item)'
]

input_file = Tool.File.path_add_site("res/picture.csv")
output_file = Tool.File.path_add_site("data/wp_to_shopify.csv")

if __name__ == "__main__":
    step = WpToShopify(Tool, input_file=input_file, output_file=output_file)
    step.EXTRA_META_COLUMNS = list(extra_meta_columns)
    step.run()

    import pandas as pd

    df = pd.read_csv(output_file)


    def _f(x):
        if pd.isnull(x):
            return x
        return Tool.HTML.clean_product_desc_str(x)


    for col in extra_meta_columns:
        df[col] = df[col].apply(lambda x :_f(x))


    df.to_csv(output_file)


