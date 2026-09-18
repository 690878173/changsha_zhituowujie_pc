
from _ljp.mb.amazon.step1 import YMXStep1 as Ys
from config import Tool


keyword = 'therabody'
output_path = Tool.File.path_add_site('data/1.json')
all_num = 7


class YMXStep1(Ys):
    def get_url(self,page_num,search_keyword):
        url = ''
        return f'https://www.amazon.com/s?k=therabody&page={page_num}&crid=2HQ4KEBCRUIBZ&qid=1788484992&sprefix=therabody%2Caps%2C1297&xpid=QmYH2sb7cMC4x&ref=sr_pg_{page_num}'

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,all_num=all_num).run()
