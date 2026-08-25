from config import Tool

input_csv = Tool.File.dz_path()
output_csv = Tool.File.fl_path()

from _ljp.mb.zj import Step10Collection


if __name__ == "__main__":
    Step10Collection(Tool, input_csv, output_csv).run()
