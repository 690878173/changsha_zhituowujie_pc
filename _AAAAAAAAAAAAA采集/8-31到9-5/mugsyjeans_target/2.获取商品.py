from _ljp.mb.target import Get_Product
from pathlib import Path

from config import Tool
input_path = Tool.File.path_add_site('data/2.json')
output_path = Tool.File.path_add_site('res/res.csv')
fail_file = Tool.File.path_add_site('fail/2.csv')
catch_path = Tool.File.path_add_site('hc/3/catch.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
variant_cache_path = Tool.File.path_add_site('hc/3/variant_prices.json')
html_save_dir = Path(__file__).resolve().parent / 'html'
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')
if __name__ == '__main__':

    Get_Product(input_path=input_path,
                output_path=output_path,
                fail_file=fail_file,
                catch_path=catch_path,
                index_path=index_path,
                variant_cache_path=variant_cache_path,
                save_html=True,
                html_save_dir=html_save_dir,
                max_threads=3,
                output_ts_file=output_ts_file,
                tool=Tool).run()
