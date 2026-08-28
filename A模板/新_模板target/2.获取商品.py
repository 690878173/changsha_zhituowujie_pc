from _ljp.mb.target.product import Step4

from config import Tool
input_path = Tool.File.path_add_site('data/2.json')
output_path = Tool.File.path_add_site('res/res.csv')
fail_file = Tool.File.path_add_site('fail/2.csv')
catch_path = Tool.File.path_add_site('hc/3/catch.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
if __name__ == '__main__':

    Step4(input_path=input_path,
          output_path=output_path,
          fail_file=fail_file,
          catch_path=catch_path,
          index_path=index_path,
          output_ts_file=output_ts_file,
          tool=Tool).run()