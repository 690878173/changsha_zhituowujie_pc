from config import Tool
from _ljp.mb.shopify import Collection


input_file = Tool.File.dz_path()
output_file = Tool.File.fl_path()


if __name__ == '__main__':
    try:
        Collection(Tool, input_file, output_file).run()
    finally:
        Tool.close()
