
from _ljp.mb.amazon.step1 import YMXStep1
from config import Tool


keyword = 'psycho+bunny'
output_path = Tool.File.path_add_site('data/1.json')
all_num = 6
url_mb = 'https://www.amazon.com/s?k=psycho+bunny&rh=p_123%3A408474&dc&page={}&xpid=91hK1adDjsRAD&crid=2QRSIXRSMHCCD&qid=1787709534&rnid=85457740011&sprefix=psycho+bunny%2Caps%2C478&ref=sr_pg_{}'
if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,url_mb=url_mb).run()
