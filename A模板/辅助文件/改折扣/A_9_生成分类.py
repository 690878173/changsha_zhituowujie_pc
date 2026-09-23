from config import Tool

input_csv = Tool.File.path_add_site(
    'res/notyourmothers_new_shopify60%off_zst_1.csv'
)
output_csv = Tool.File.path_add_site(
    'res/notyourmothers_new_shopify_col_zst_1.csv'
)

from _ljp.mb.zj import Collection


if __name__ == "__main__":
    Collection(Tool, input_csv, output_csv).run()
