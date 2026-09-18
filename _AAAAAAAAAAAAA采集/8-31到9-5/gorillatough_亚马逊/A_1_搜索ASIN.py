
from _ljp.mb.amazon.step1 import YMXStep1 as Ys
from config import Tool


keyword = 'gorilla'
output_path = Tool.File.path_add_site('data/1.json')
all_num = 7


class YMXStep1(Ys):
    def get_url(self,page_num,search_keyword):
        url = ''
        return f'https://www.amazon.com/s?k=gorilla&page={page_num}&crid=2RGZ42F0CNZHK&qid=1788484705&sprefix=gorilla%2Caps%2C765&xpid=RyZP28XI2onIb&ref=sr_pg_{page_num}'

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,all_num=all_num).run()
