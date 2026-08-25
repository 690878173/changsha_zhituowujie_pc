from config import Tool

input_csv = Tool.File.dz_path()
output_csv = Tool.File.fl_path()

from _ljp.mb.shopify import Step10Collection

pc = Step10Collection(Tool, input_csv, output_csv)

if __name__ == "__main__":
    pc.run()
