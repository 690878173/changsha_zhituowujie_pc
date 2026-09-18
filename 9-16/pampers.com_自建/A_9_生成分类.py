from config import Tool
from _ljp.mb.base import Collection


input_file = Tool.File.dz_path()
output_file = Tool.File.fl_path()


if __name__ == "__main__":
    Collection(Tool, input_file, output_file).run()
