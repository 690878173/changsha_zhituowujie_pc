from config import Tool
from _ljp.mb.target import Step10Collection
input_csv = Tool.File.dz_path()
output_csv = Tool.File.fl_path()

if __name__ == "__main__":
    Step10Collection(Tool,input_csv,output_csv).run()
