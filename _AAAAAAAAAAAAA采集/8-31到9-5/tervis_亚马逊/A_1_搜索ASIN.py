
from _ljp.mb.amazon.step1 import YMXStep1 as Ys
from config import Tool


keyword = 'tervis'
output_path = Tool.File.path_add_site('data/1.json')
all_num = 6


class YMXStep1(Ys):
    def get_url(self,page_num,search_keyword):
        url = ''
        return f'https://www.amazon.com/s?k=tervis&page={page_num}&xpid=Qy9PVQSuw1I9i&crid=2NCNI7U75745V&qid=1788403330&sprefix=tervis%2Caps%2C374&ref=sr_pg_{page_num}'

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,all_num=all_num).run()
