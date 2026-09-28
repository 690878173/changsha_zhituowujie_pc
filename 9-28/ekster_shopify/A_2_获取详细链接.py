from urllib.parse import urlsplit, urlunsplit

from config import Tool
from _ljp.mb.model import PageModel
from _ljp.mb.shopify import GetDetail


file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

ts_num = None
skip_input_url_ls = []
skip_output_url_ls = []
catch_save_num = None
flush = False


class EksterDetailCollector(GetDetail):
    page_size = 250

    @staticmethod
    def build_collection_products_api_url(collection_url: str) -> str:
        """Append ``/products.json`` before the original query string."""
        parts = urlsplit(collection_url.strip())
        path = f"{parts.path.rstrip('/')}/products.json"
        return urlunsplit((parts.scheme, parts.netloc, path, parts.query, ''))

    def fetch_page(self, page: PageModel, params):
        api_url = self.build_collection_products_api_url(page.url)
        try:
            response = self.tool.get(api_url, params=params, timeout=20)
            if response.status_code == 404:
                page.set_end()
                return [], None
            if response.status_code != 200:
                self.tool.print(f'Collection API failed ({response.status_code}): {api_url}')
                page.set_fail()
                return [], None
            products = response.json().get('products')
        except (TypeError, ValueError, OSError) as exc:
            self.tool.print(f'Collection API parse failed: {api_url}: {exc}')
            page.set_fail()
            return [], None

        if not isinstance(products, list):
            self.tool.print(f'Collection API returned no product list: {api_url}')
            page.set_fail()
            return [], None
        if not products:
            page.set_end()
            return [], None

        product_urls = [
            self.tool.URL.add_site(f"/products/{product['handle']}")
            for product in products
            if product.get('handle')
        ]
        if len(products) < self.page_size:
            page.set_end()
            return product_urls, None
        return product_urls, page.url

    def build_params(self, page: PageModel):
        return {'page': page.page, 'limit': self.page_size}


if __name__ == '__main__':
    try:
        EksterDetailCollector(
            tool=Tool,
            input_path=file_path,
            output_path=save_path,
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
