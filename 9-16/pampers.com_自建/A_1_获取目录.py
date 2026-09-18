from config import Tool, base_url
from _ljp.mb.base.get_ml import BaseCatalogParser, CatCol


save_path = Tool.File.path_add_site("data/ml.json")
snapshot_path = Tool.File.path_add_site("ts/1/homepage.html")


class PampersCatalogParser(BaseCatalogParser):
    """Parse the desktop Products mega menu and preserve its menu groups."""

    def f1(self, html, dic):
        products_menu = html.xpath(
            "//nav[contains(concat(' ', normalize-space(@class), ' '), ' nav ')]"
            "//a[normalize-space()='Products' and @href='/en-us/products']"
            "/ancestor::div[@role='listitem'][1]"
        )
        if not products_menu:
            return dic

        products = self.collector.add_node(
            dic, "Products", Tool.URL.add_site("/en-us/products")
        )
        if not isinstance(products, dict):
            return dic

        columns = products_menu[0].xpath(
            ".//div[@role='region']//div[contains(concat(' ', normalize-space(@class), ' '), ' flex-25 ')]"
        )
        for column in columns:
            headings = column.xpath("./p[1]//text()")
            group_name = " ".join(" ".join(headings).split())
            if not group_name:
                continue

            group = self.collector.add_node(products, group_name, "")
            if not isinstance(group, dict):
                continue

            for link in column.xpath("./a[@href]"):
                href = link.get("href", "")
                if not href.startswith("/en-us/products"):
                    continue
                if href == "/en-us/products/diaper-comparison-chart":
                    continue

                name = " ".join(" ".join(link.xpath(".//text()")).split())
                if name:
                    self.collector.add_node(group, name, Tool.URL.add_site(href))

        dic['Other'] = {
            'Best Sellers':{'url':'https://www.pampers.com/en-us/products/bestsellers'}
        }
        return dic


M = CatCol(Tool, base_url, save_path, snapshot_path)
M.parser_types = (*M.parser_types, PampersCatalogParser)


if __name__ == '__main__':
    M.run()



