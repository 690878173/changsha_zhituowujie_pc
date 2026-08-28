
from _ljp.mb.amazon.step1 import YMXStep1 as Ys
from config import Tool


keyword =
output_path = Tool.File.path_add_site('data/1.json')
url_mb = None
all_num = 6


class YMXStep1(Ys):
    def get_url(self,page_num,search_keyword):
        return super().get_url(page_num,search_keyword)

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,url_mb=url_mb,all_num=all_num).run()
