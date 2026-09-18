
from _ljp.mb.amazon.step1 import YMXStep1
from config import Tool


keyword = 'shokz'
output_path = Tool.File.path_add_site('data/1.json')
url_mb = 'https://www.amazon.com/s?k=shokz&page={}&xpid=dgHETOL-sTF1Y&crid=2JEE4HNTI2XAZ&qid=1787724700&sprefix=shokz%2Caps%2C370&ref=sr_pg_{}'


class YMXStep1(YMXStep1):
    def get_url(self,page_num,search_keyword):
        url = f'https://www.amazon.com/s?k=shokz&rh=p_123%3A1074925&dc&page={page_num}&crid=3INWIUWR55O85&qid=1787794121&rnid=85457740011&sprefix=shokz%2Caps%2C367&xpid=hMakvhuqFgruu&ref=sr_pg_{page_num}'
        return url
if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,url_mb=url_mb,all_num=7).run()
