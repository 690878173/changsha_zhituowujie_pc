from config import Tool
from lxml import etree, html as lxml_html

from _ljp.mb.mg_shopify import GetDetail


file_path = Tool.File.path_add_site("data/ml.json")
save_path = Tool.File.path_add_site("data/detail_url.json")
catch_path = Tool.File.path_add_site("hc/2/data.json")
index_path = Tool.File.path_add_site("hc/2/index.json")

ts_num = None
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
catch_save_num = None


class Pc(GetDetail):
    def storefront_settings(self):
        # 站点专有信息只放在 Step 接口中，不污染 Tool.config。
        return {
            "storefront_token": "07a42fb28f2b14504c14f1de815cbd45",
            "store_domain": "checkout.honeylove.com",
            "api_version": "unstable",
            "country": "US",
            "language": "EN",
        }

    def build_params(self, page):
        # Honeylove renders some collection cards on the server, but its public
        # Storefront token returns an empty products connection for them.
        return {
            "source": "honeylove-rendered-collection-cards-v1",
            "page": page.page,
        }

    def fetch_page(self, page, params):
        try:
            response = self.tool.get(page.url)
            if response.status_code != 200:
                self.tool.print(
                    f"   [!] Honeylove 分类页响应异常: {response.status_code} {page.url}",
                    color="yellow",
                )
                page.set_fail()
                return [], None

            tree = lxml_html.fromstring(response.text)
            hrefs = tree.xpath(
                '//a[normalize-space()="View More Details" and starts-with(@href, "/products/")]/@href'
            )
            if not hrefs:
                # A successful page with no product cards is a confirmed empty
                # collection, so preserve the normal Step2 end-cache behavior.
                page.set_end()
                return [], None

            product_urls = []
            for href in hrefs:
                product_url = self.tool.URL.del_par(self.tool.URL.add_site(href))
                if product_url not in product_urls:
                    product_urls.append(product_url)

            page.set_end()
            return product_urls, None
        except (TypeError, ValueError, etree.ParserError) as exc:
            self.tool.print(f"   [!] Honeylove 分类页解析失败: {page.url}: {exc}", color="yellow")
            page.set_fail()
            return [], None


if __name__ == "__main__":
    Pc(
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
