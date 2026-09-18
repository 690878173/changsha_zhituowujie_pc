
from _ljp.mb.amazon.step1 import YMXStep1 as Ys
from config import Tool


keyword = 'woxer'
output_path = Tool.File.path_add_site('data/1.json')
all_num = 6


class YMXStep1(Ys):
    def get_url(self,page_num,search_keyword):
        url = f'https://www.amazon.com/s?k=woxer&page={page_num}&crid=44RFO1AQMWZV&qid=1788139218&sprefix=woxer%2Caps%2C597&xpid=ZKayaWbmfpuXG&ref=sr_pg_{page_num}'
        return url

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,all_num=all_num).run()
