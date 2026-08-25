
from _ljp.mb.amazon.step1 import YMXStep1
from config import Tool


keyword =
output_path = Tool.File.path_add_site('data/1.json')

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path).run()
