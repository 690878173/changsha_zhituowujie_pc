from lxml import etree
from urllib.parse import urlsplit, parse_qs
from config import Tool
from _ljp.mb.zj import GetDetail
from _ljp.mb.model import PageModel

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')
ts_num = None
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
catch_save_num = None

class Pc(GetDetail):
    def fetch_page(self, page: PageModel, params):
        res = Tool.get(page.url)
        if res.status_code != 200 or not res.text:
            page.set_fail()
            return [], None
        tree = etree.HTML(res.text)
        urls = []
        for href in tree.xpath('//a[contains(@class,"product-item-link")]/@href | //a[contains(@href,"/shop/")]/@href'):
            href = Tool.URL.add_site(href)
            if '/shop/' in href and href not in urls:
                urls.append(href)
        nxt = tree.xpath('//a[contains(@class,"pages-item-next")]/@href')
        next_url = Tool.URL.add_site(nxt[0]) if nxt else None
        # Magento may render a wrapped "next" link on the last page; stop when
        # it does not advance the explicit page number.
        if next_url:
            current_num = int(parse_qs(urlsplit(page.url).query).get('p', ['1'])[0])
            next_query = parse_qs(urlsplit(next_url).query)
            next_num = int(next_query.get('p', [str(current_num + 1)])[0])
            if (current_num > 1 and 'p' not in next_query) or next_num <= current_num:
                next_url = None
        if not urls and not next_url:
            page.set_end()
        return urls, next_url

    def build_params(self, page: PageModel):
        return {'page': page.page}

    def after_one_request(self, page):
        # Base GetDetail increments page.page but keeps the current URL; advance
        # to Magento's explicit next URL before the next request.
        if page.next_url:
            page.url = page.next_url

if __name__ == '__main__':
    Pc(tool=Tool, input_path=file_path, output_path=save_path,
       catch_path=catch_path, index_path=index_path, ts_num=ts_num,
       flush=flush, skip_input_url_ls=skip_input_url_ls,
       skip_output_url_ls=skip_output_url_ls,
       catch_save_num=catch_save_num).run()
