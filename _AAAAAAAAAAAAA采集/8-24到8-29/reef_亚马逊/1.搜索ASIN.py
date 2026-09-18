
from _ljp.mb.amazon.step1 import YMXStep1
from config import Tool


keyword = 'reef'
output_path = Tool.File.path_add_site('data/1.json')
url_mb = 'https://www.amazon.com/s?k=reef&page={}&xpid=2yfjcRd52gojo&crid=21N12YMNNUIG1&qid=1787725075&sprefix=reef%2Caps%2C347&ref=sr_pg_{}'



class YMXStep1(YMXStep1):
    def get_url(self,page_num,search_keyword):
        url = f'https://www.amazon.com/s?k=reef&rh=p_123%3A420196&dc&page={page_num}&xpid=IMCn4pukN1I0G&crid=1K6XFMDOMM2KT&qid=1787801910&rnid=85457740011&sprefix=reef%2Caps%2C373&ref=sr_pg_{page_num}'
        return url
if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,url_mb=url_mb,all_num=7).run()
