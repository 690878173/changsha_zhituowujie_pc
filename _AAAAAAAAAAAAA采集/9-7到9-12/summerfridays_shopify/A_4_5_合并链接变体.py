from config import Tool
from merge_variants import SummerFridaysMergeVariants


INPUT_FILE = Tool.File.path_add_site('fwq/quchong.csv')
OUTPUT_FILE = Tool.File.path_add_site('fwq/merged_link_variants.csv')


if __name__ == '__main__':
    SummerFridaysMergeVariants(Tool, INPUT_FILE, OUTPUT_FILE).run()
    Tool.close()
