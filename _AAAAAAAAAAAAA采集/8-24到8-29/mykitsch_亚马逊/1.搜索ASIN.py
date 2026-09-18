
from _ljp.mb.amazon.step1 import YMXStep1
from config import Tool


keyword = 'mykitsch'
output_path = Tool.File.path_add_site('data/1.json')
url_mb = 'https://www.amazon.com/s?k=mykitsch&page={}&xpid=yrpvvfX5QHYD2&crid=84T4WW9F8RF4&qid=1787725576&sprefix=mykitsch%2Caps%2C401&ref=sr_pg_{}'


class YMXStep1(YMXStep1):

    def get_url(self,page_num,search_keyword):
        url = f'https://www.amazon.com/s?k=kitsch&rh=p_123%3A253556&dc&page={page_num}&xpid=rrEvBQ3QRuYvX&crid=1YTLEWWOWXTEL&qid=1787795010&rnid=85457740011&sprefix=kitsch%2Caps%2C445&ref=sr_pg_{page_num}'
        return url

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,url_mb=url_mb,all_num=7).run()
