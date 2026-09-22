from config import Tool
from _ljp.mb.base import Collection
input_csv = Tool.File.dz_path()
output_csv = Tool.File.fl_path()

if __name__ == "__main__":
    Collection(Tool, input_csv=input_csv, output_csv=output_csv).run()
