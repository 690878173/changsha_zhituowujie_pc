
from _ljp.mb.amazon.step1 import YMXStep1 as Ys
from config import Tool


keyword = 'go+contigo'
output_path = Tool.File.path_add_site('data/1.json')
all_num = 2


class YMXStep1(Ys):
    def get_url(self,page_num,search_keyword):
        url = f'https://www.amazon.com/s?k=go+contigo&rh=p_123%3A237452&dc&page={page_num}&xpid=BmkyZ8eX_-Xlr&crid=ZXWN1GD3HMJS&qid=1788398897&rnid=85457740011&sprefix=go+conti%2Caps%2C361&ref=sr_pg_{page_num}'
        return url

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,all_num=all_num).run()
