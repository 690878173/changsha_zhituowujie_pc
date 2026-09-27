"""Collect non-bundle CASETiFY design pages from its category grid."""

from urllib.parse import urlsplit, urlunsplit
import sys

from lxml import etree

from config import Tool
from _ljp.mb.model import PageModel
from _ljp.mb.zj import GetDetail


if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


INPUT_PATH = Tool.File.path_add_site('data/ml.json')
OUTPUT_PATH = Tool.File.path_add_site('data/detail_url.json')
CATCH_PATH = Tool.File.path_add_site('hc/2/data.json')
INDEX_PATH = Tool.File.path_add_site('hc/2/index.json')

# Validate two category inputs before changing this to None for a full run.
ts_num = None
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
catch_save_num = 10


class CasetifyDetailUrls(GetDetail):
    """Read only listing cards, never the category page's navigation links."""

    request_headers = {'User-Agent': 'python-requests/2.32.3'}

    product_xpath = (
        '//div[contains(concat(" ", normalize-space(@class), " "), '
        '" listing-product-container ")]//a[@itemprop="url"]/@href'
    )

    bundle_markers = ('bundle', 'blind-box', '-set', '-sets', 'box-')

    @classmethod
    def is_bundle_card(cls, anchor):
        text = ' '.join(anchor.xpath('.//text()')).casefold()
        href = (anchor.get('href') or '').casefold()
        return 'value set' in text or any(marker in href for marker in cls.bundle_markers)

    def normalize_product_url(self, href):
        parsed = urlsplit(href)
        parts = [part for part in parsed.path.split('/') if part]
        if len(parts) < 3 or parts[:2] != ['en_US', 'product']:
            return ''
        base = urlsplit(Tool.URL.base_url)
        path = f'/en_US/product/{parts[2]}'
        return urlunsplit((base.scheme, base.netloc, path, '', ''))

    def next_page_url(self, tree):
        hrefs = tree.xpath('//a[@rel="next"]/@href')
        if not hrefs:
            return None
        return Tool.URL.add_site(hrefs[0])

    def fetch_page(self, page: PageModel, params):
        response = Tool.get(page.url, headers=self.request_headers)
        if response.status_code == 404:
            page.set_end()
            return [], None
        if response.status_code != 200 or not response.text:
            page.set_fail()
            return [], None

        try:
            tree = etree.HTML(response.text)
            if tree is None:
                raise ValueError('invalid HTML')
            product_urls = []
            for anchor in tree.xpath(self.product_xpath.replace('/@href', '')):
                if self.is_bundle_card(anchor):
                    continue
                url = self.normalize_product_url(anchor.get('href') or '')
                if url:
                    product_urls.append(url)
            next_url = self.next_page_url(tree)
        except (TypeError, ValueError, etree.ParserError):
            page.set_fail()
            return [], None

        if not product_urls:
            if next_url:
                page.set_fail()
            else:
                page.set_end()
            return [], None

        if not next_url or next_url == page.url:
            page.set_end()
            return product_urls, None
        return product_urls, next_url


if __name__ == '__main__':
    CasetifyDetailUrls(
        tool=Tool,
        input_path=INPUT_PATH,
        output_path=OUTPUT_PATH,
        catch_path=CATCH_PATH,
        index_path=INDEX_PATH,
        ts_num=ts_num,
        flush=flush,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        catch_save_num=catch_save_num,
    ).run()
