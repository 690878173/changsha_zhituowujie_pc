"""Export OXO WooCommerce products while excluding reviews and FAQ content."""

from html import escape
from pathlib import Path
from re import sub
from urllib.parse import urlsplit

from lxml import etree

from config import Tool, site
from _ljp.mb.zj import Get_Product


INPUT_FILE = Tool.File.path_add_site("data/detail_url.json")
OUTPUT_FILE = Tool.File.path_add_site("res/result.csv")
FAIL_FILE = Tool.File.path_add_site("fail/3/fail.json")
CATCH_PATH = Tool.File.path_add_site("hc/3/data.json")
INDEX_PATH = Tool.File.path_add_site("hc/3/index.json")
OUTPUT_TS_FILE = Tool.File.path_add_site("hc/3/ts_url.csv")

# Keep the first run small so the page fields can be checked before a full export.
ts_num = None
catch_save_num = 10
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
fieldnames = None
max_threads = 2


class Pc(Get_Product):
    """Request OXO product pages and delegate parsing to the site adapter."""

    def fetch_product(self, url, category):
        response = Tool.get(url)
        if response.status_code != 200 or not response.text:
            raise ValueError(f"PDP request failed: HTTP {response.status_code}")
        return _T(url, category, response.text).run()


class _T:
    """Parse one simple WooCommerce product without visiting review or FAQ content."""

    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.html = etree.HTML(res_text)
        if self.html is None:
            raise ValueError("PDP HTML is invalid")

    @staticmethod
    def text(node):
        return " ".join(" ".join(node.xpath(".//text()")).split())

    def get_main_name(self):
        nodes = self.html.xpath('//h1[contains(@class, "product_title")]')
        name = self.text(nodes[0]) if nodes else ""
        if not name:
            raise ValueError("PDP has no product title")
        return name

    def get_main_sku(self):
        skus = self.html.xpath(
            '//span[contains(concat(" ", normalize-space(@class), " "), " sku ")]/text()'
        )
        sku = " ".join(" ".join(skus).split())
        if not sku:
            raise ValueError("PDP has no SKU")
        return sku

    def get_main_prices(self):
        price_boxes = self.html.xpath('//p[contains(@class, "price")]')
        if not price_boxes:
            raise ValueError("PDP has no price")
        price_box = price_boxes[0]
        sale_nodes = price_box.xpath('.//ins')
        sale = self.text(sale_nodes[0]) if sale_nodes else ""
        if not sale:
            amounts = price_box.xpath(
                './/*[contains(concat(" ", normalize-space(@class), " "), " woocommerce-Price-amount ")]'
            )
            sale = self.text(amounts[0]) if amounts else ""
        regular_nodes = price_box.xpath('.//del')
        regular = self.text(regular_nodes[0]) if regular_nodes else sale
        sale = Tool.clean_price(sale)
        regular = Tool.clean_price(regular or sale)
        if not sale or not regular:
            raise ValueError("PDP has an empty price")
        return sale, regular

    def get_main_desc(self):
        nodes = self.html.xpath(
            '//div[@id="tab-description" and contains(@class, "woocommerce-Tabs-panel--description")]'
        )
        if not nodes:
            raise ValueError("PDP has no description tab")
        description = Tool.HTML.clean_product_desc(nodes[0])
        if not description:
            raise ValueError("PDP description is empty")
        return description

    def get_main_imgs(self):
        images = self.html.xpath(
            '//div[contains(@class, "woocommerce-product-gallery__image")]'
            '//img[@data-large_image]/@data-large_image'
        )
        images = list(dict.fromkeys(images))
        if not images:
            raise ValueError("PDP has no gallery images")
        return images

    def get_product_details(self):
        rows = self.html.xpath(
            '//div[@id="tab-additional_information"]'
            '//tr[contains(@class, "woocommerce-product-attributes-item")]'
        )
        values = []
        for row in rows:
            label = self.text(row.xpath('.//th')[0]) if row.xpath('.//th') else ""
            value = self.text(row.xpath('.//td')[0]) if row.xpath('.//td') else ""
            if label and value:
                values.append(f"<li><strong>{escape(label)}:</strong> {escape(value)}</li>")
        return "<ul>" + "".join(values) + "</ul>" if values else ""

    @staticmethod
    def safe_filename_part(value):
        value = sub(r"[^A-Za-z0-9._-]+", "_", str(value or "unknown"))
        return value.strip("._") or "unknown"

    def save_debug_snapshot(self, sku):
        slug = Path(urlsplit(self.url).path.rstrip("/")).name
        filename = f"{self.safe_filename_part(slug)}_{self.safe_filename_part(sku)}_page.html"
        Tool.HTML.save_raw(
            self.res_text,
            Path(__file__).with_name("ts") / "03-product-data" / filename,
        )

    def run(self):
        name = self.get_main_name()
        sku = self.get_main_sku()
        sale_price, regular_price = self.get_main_prices()
        self.save_debug_snapshot(sku)
        product = Tool.Product.Simple(
            url=self.url,
            cat=self.category,
            imgs=self.get_main_imgs(),
            name=name,
            sku=sku,
            price=sale_price,
            desc=self.get_main_desc(),
            brand=site,
            **{"Product Details": self.get_product_details()},
        ).to_dic()
        product["Regular price"] = regular_price
        return [product]


if __name__ == "__main__":
    Pc(
        tool=Tool,
        input_path=INPUT_FILE,
        output_path=OUTPUT_FILE,
        fail_file=FAIL_FILE,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        ts_num=ts_num,
        fieldnames=fieldnames,
        catch_path=CATCH_PATH,
        index_path=INDEX_PATH,
        output_ts_file=OUTPUT_TS_FILE,
        flush=flush,
        max_threads=max_threads,
        catch_save_num=catch_save_num,
    ).run()

