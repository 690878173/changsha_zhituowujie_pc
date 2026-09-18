
from _ljp.mb.amazon.step3 import YMXStep3

from config import Tool
input_path = Tool.File.path_add_site('data/2.json')
output_path = Tool.File.path_add_site('res/res.csv')
fail_file = Tool.File.path_add_site('fail/2.csv')
catch_path = Tool.File.path_add_site('hc/3/catch.csv')
index_path = Tool.File.path_add_site('hc/3/index.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
if __name__ == "__main__":
    YMXStep3(tool=Tool,
             input_path=input_path,
             output_path=output_path,
             fail_file=fail_file,
             catch_path=catch_path,
             index_path=index_path,
             output_ts_file=output_ts_file
             ).run()
