from pathlib import Path
from urllib.parse import urlsplit

from lxml import etree

from config import Tool
from _ljp.mb.model import PageModel
from _ljp.mb.zj import GetDetail


input_path = Tool.File.path_add_site('data/ml.json')
output_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

# Validate the first two category pages before attempting a full catalog run.
ts_num = None
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
catch_save_num = None


class Pc(GetDetail):
    """Collect Sonos product detail URLs from server-rendered PLP cards."""

    def fetch_page(self, page: PageModel, params):
        response = Tool.get(page.url)
        if response.status_code != 200 or not response.text:
            return self._failed_page(page, response.text, f'HTTP {response.status_code}')

        document = etree.HTML(response.text)
        if document is None:
            return self._failed_page(page, response.text, 'invalid HTML')

        product_urls = []
        seen_urls = set()
        for anchor in document.xpath(
            '//*[@data-testid="product-tile"]'
            '//a[@data-testid="cart-link-container"][@href]'
        ):
            product_url = Tool.URL.add_site(anchor.get('href'))
            if product_url in seen_urls:
                continue

            seen_urls.add(product_url)
            product_urls.append(product_url)

        if not product_urls:
            return self._failed_page(page, response.text, 'no product tile links')

        # Sonos renders the complete PLP product list in the initial response.
        page.set_end()
        return product_urls, None

    def _failed_page(self, page, html_text, reason):
        page.set_fail()
        if html_text:
            try:
                Tool.HTML.save_raw(html_text, self._debug_path(page.url))
            except OSError as exc:
                Tool.print(f'[A_2] failed to save debug HTML: {exc}', color='yellow')

        Tool.print(f'[A_2] {reason}: {page.url}', color='yellow')
        return [], None

    @staticmethod
    def _debug_path(url):
        slug = urlsplit(url).path.rstrip('/').split('/')[-1] or 'shop'
        return Path(__file__).parent / 'ts' / '02-detail-links' / f'{slug}_page.html'


if __name__ == '__main__':
    try:
        Pc(
            tool=Tool,
            input_path=input_path,
            output_path=output_path,
            catch_path=catch_path,
            index_path=index_path,
            ts_num=ts_num,
            flush=flush,
            skip_input_url_ls=skip_input_url_ls,
            skip_output_url_ls=skip_output_url_ls,
            catch_save_num=catch_save_num,
        ).run()
    finally:
        Tool.close()
