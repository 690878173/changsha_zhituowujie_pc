from config import Tool
from _ljp.mb.base import Quchong


input_file = Tool.File.path_add_site(r'res/res.csv')
output_file= Tool.File.path_add_site(r'res/quchong.csv')

if __name__ == "__main__":
    Quchong(Tool,input_file=input_file,output_file=output_file).run()
