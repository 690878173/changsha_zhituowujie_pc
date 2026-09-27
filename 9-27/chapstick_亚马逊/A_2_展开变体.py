from config import Tool
from _ljp.mb.amazon.step2 import YMXStep2

input_path = Tool.File.path_add_site('data/1.json')
output_path = Tool.File.path_add_site('data/2.json')

catch_path = Tool.File.path_add_site('hc/2/catch.json')
index_path = Tool.File.path_add_site('hc/2/index.json')


if __name__ == "__main__":
    YMXStep2(tool=Tool,
             input_path=input_path,
             output_path=output_path,
             catch_path=catch_path,
             index_path=index_path
             ).run()
