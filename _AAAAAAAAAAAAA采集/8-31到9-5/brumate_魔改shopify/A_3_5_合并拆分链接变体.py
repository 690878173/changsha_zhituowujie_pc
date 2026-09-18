from config import Tool
from _ljp.mb.mg_shopify import MergeLinkVariants


INPUT_FILE = Tool.File.path_add_site("res/result.csv")
OUTPUT_FILE = Tool.File.path_add_site("fwq/merged_link_variants.csv")


if __name__ == "__main__":
    MergeLinkVariants(Tool, INPUT_FILE, OUTPUT_FILE).run()
