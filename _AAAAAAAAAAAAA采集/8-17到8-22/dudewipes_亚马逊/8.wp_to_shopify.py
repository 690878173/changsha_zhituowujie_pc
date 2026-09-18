from curl_cffi.cli import output

from config import Tool
from _ljp.mb.base import WpToShopify

# Add any site-specific Shopify metafield column names here.
extra_meta_columns = [
    "important_information",
    "productDescription",
    "Product_details",
    "About_this_item"
]


input_file = 'data/clean.csv'

output_file = Tool.File.path_add_site('data/wp_to_shopify.csv')
if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv(input_file)

    def _cl(col):
        if col and pd.notnull(col):
            print(col)
            col = col.replace('?\n', '').replace(':\n','\n')

        return col
    for i in extra_meta_columns:
        if i in df.columns:
            df[i] = df[i].apply(lambda col: _cl(col))


    df.to_csv(input_file)







    step = WpToShopify(Tool, input_file=input_file)
    step.EXTRA_META_COLUMNS = list(extra_meta_columns)
    step.run()

    def build_custom_field_name(field: str) -> str:
        if '(product.metafields.c_f.' in field:
            return field
        field = field.replace('&','').replace('  ','')
        return f"{field}(product.metafields.c_f.{field.replace(' ', '_').lower()})"



    import pandas as pd
    df = pd.read_csv(output_file)
    for i in extra_meta_columns:
        if i in df.columns:
            df[build_custom_field_name(i)] = df[i]
            df.drop(columns=[i],inplace=True)

    df.to_csv(output_file)
