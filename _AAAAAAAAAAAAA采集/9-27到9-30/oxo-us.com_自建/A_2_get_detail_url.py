"""Collect OXO product detail URLs from WooCommerce category pages."""

from urllib.parse import urlsplit

from lxml import etree

from config import Tool
from _ljp.mb.model import PageModel
from _ljp.mb.zj import GetDetail


INPUT_PATH = Tool.File.path_add_site("data/ml.json")
OUTPUT_PATH = Tool.File.path_add_site("data/detail_url.json")
CATCH_PATH = Tool.File.path_add_site("hc/2/data.json")
INDEX_PATH = Tool.File.path_add_site("hc/2/index.json")

# Full directory run after the two-category pagination sample was verified.
ts_num = None
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
catch_save_num = 10


class OxoDetailUrls(GetDetail):
    """Read product cards and rel=next pagination from OXO category pages."""

    product_xpath = (
        '//div[contains(concat(" ", normalize-space(@class), " "), " product-small ")]'
        '//a[contains(concat(" ", normalize-space(@class), " "), " woocommerce-LoopProduct-link ") and @href]'
    )

    def normalize_product_url(self, href):
        if not href or href.startswith(("#", "javascript:")):
            return ""
        url = Tool.URL.add_site(href)
        parsed = urlsplit(url)
        base = urlsplit(Tool.URL.base_url)
        if parsed.netloc != base.netloc or not parsed.path.strip("/"):
            return ""
        if parsed.path.startswith(("/wp-", "/cart", "/checkout", "/my-account")):
            return ""
        return url

    def fetch_page(self, page: PageModel, params):
        response = Tool.get(page.url)
        if response.status_code == 404:
            page.set_end()
            return [], None
        if response.status_code != 200 or not response.text:
            Tool.print(f"分类页请求失败: {response.status_code} {page.url}", color="red")
            page.set_fail()
            return [], None

        try:
            tree = etree.HTML(response.text)
            if tree is None:
                raise ValueError("invalid HTML")

            product_urls = []
            for href in tree.xpath(self.product_xpath + "/@href"):
                url = self.normalize_product_url(href)
                if url and url not in product_urls:
                    product_urls.append(url)

            next_hrefs = tree.xpath('//link[@rel="next"]/@href | //a[@rel="next"]/@href')
            next_url = Tool.URL.add_site(next_hrefs[0]) if next_hrefs else None
        except (TypeError, ValueError, etree.ParserError) as exc:
            Tool.print(f"分类页解析失败: {exc} {page.url}", color="red")
            page.set_fail()
            return [], None

        if not product_urls:
            if next_url and next_url != page.url:
                page.set_fail()
            else:
                page.set_end()
            return [], None

        if not next_url or next_url == page.url:
            page.set_end()
            return product_urls, None
        return product_urls, next_url

    def build_params(self, page):
        return None


if __name__ == "__main__":
    OxoDetailUrls(
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

