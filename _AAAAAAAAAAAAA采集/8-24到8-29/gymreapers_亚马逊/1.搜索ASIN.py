
from _ljp.mb.amazon.step1 import YMXStep1
from config import Tool


keyword = 'gymreapers'
output_path = Tool.File.path_add_site('data/1.json')
url_mb = 'https://www.amazon.com/s?k=gymreapers&rh=p_123%3A218529&dc&page={}&xpid=bZXNdPkFVlnNc&crid=1UW3KO04J1L2M&qid=1787708556&rnid=85457740011&sprefix=gymreapers%2Caps%2C534&ref=sr_pg_{}'
if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,url_mb=url_mb,all_num=3).run()
