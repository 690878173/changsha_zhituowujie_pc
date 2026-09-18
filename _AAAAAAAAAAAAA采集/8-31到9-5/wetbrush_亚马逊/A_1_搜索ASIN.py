
from _ljp.mb.amazon.step1 import YMXStep1 as Ys
from config import Tool


keyword = 'wetbrush'
output_path = Tool.File.path_add_site('data/1.json')
all_num = 6


class YMXStep1(Ys):
    def get_url(self,page_num,search_keyword):
        url = ''
        return f'https://www.amazon.com/s?k=wetbrush&page={page_num}&crid=32BVY489HS3MP&qid=1788404128&sprefix=wetbrush%2Caps%2C376&xpid=CL0m3hP5GNVdl&ref=sr_pg_{page_num}'

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,all_num=all_num).run()
