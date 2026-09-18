
from _ljp.mb.amazon.step1 import YMXStep1
from config import Tool


keyword = 'snif'
output_path = Tool.File.path_add_site('data/1.json')
url_mb = None


class YMXStep1(YMXStep1):


    def get_url(self,page_num,search_keyword):
        url = f"https://www.amazon.com/s?k=snif&rh=p_123%3A2641068&dc&crid=1WTCW4A6NMK6Y&qid=1787793432&rnid=85457740011&sprefix=snif%2Caps%2C607&xpid=cGg0QbM7R5vsC&ref=sr_nr_p_123_1&ds=v1%3AHOX7p3Slt2kXBhNkDulx1I75mPm4i1sKOLrcpT%2BPVA0"
        if self.url_mb:
            url = self.url_mb.format(page_num, page_num)
        return url


if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,url_mb=url_mb,all_num=1).run()
