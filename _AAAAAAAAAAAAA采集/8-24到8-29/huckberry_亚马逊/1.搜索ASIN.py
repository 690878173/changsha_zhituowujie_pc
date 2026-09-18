
from _ljp.mb.amazon.step1 import STEP1,YMXStep1
from config import Tool
keyword = "huckberry"
output_path = Tool.File.path_add_site('data/1.json')

if __name__ == "__main__":
    url_mb = 'https://www.amazon.com/s?k=huckberry&page={}&crid=24PWRIX3HR7UX&qid=1787645880&sprefix=huckberry%2Caps%2C348&xpid=YQ2vIpj-3mQIa&ref=sr_pg_3'
    YMXStep1(search_keyword=keyword,output_path=output_path,url_mb=url_mb).run()
