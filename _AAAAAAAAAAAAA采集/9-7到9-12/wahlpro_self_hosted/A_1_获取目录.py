from pathlib import Path
from lxml import etree
from config import base_url, Tool
from _ljp.mb.base.get_ml import CatalogParser, CatCol

save_path = Tool.File.path_add_site('data/ml.json')

class WahlMenuParser(CatalogParser):
    def matches(self, html):
        return 'menu-seed-main-menu-desktop' in html

    def parse(self, html, collector):
        tree = etree.HTML(html)
        result = {}
        nav = tree.xpath('//nav[@id="menu-seed-main-menu-desktop"]')
        if not nav:
            return result
        for top in nav[0].xpath('./ul/li[contains(@class,"level-0")]'):
            label = ''.join(top.xpath('./div/button//text()')).strip()
            child = collector.add_node(result, label, '')
            if child is None:
                continue
            for item in top.xpath('.//li[contains(@class,"level-1") or contains(@class,"level-2")]'):
                a = item.xpath('./a[1]')
                if not a:
                    continue
                name, url = Tool.HTML.get_a_text_and_url(a[0])
                if not url or '/shop/' in url or '/pages/' in url or '/blogs/' in url:
                    continue
                if 'level-2' in (item.get('class') or ''):
                    # Hyva renders all level-2 lists as siblings, so associate
                    # them with the level-1 URL prefix rather than an ancestor li.
                    parent = None
                    for parent_item in child.values():
                        parent_url = parent_item.get('url') or ''
                        parent_slug = parent_url.rstrip('/').rsplit('/', 1)[-1]
                        if parent_url and (url.startswith(parent_url.rstrip('/') + '/') or parent_slug in url):
                            parent = parent_item.get('child')
                            break
                    if parent is not None:
                        collector.add_node(parent, name, url)
                else:
                    collector.add_node(child, name, url)
        return result

M = CatCol(Tool, base_url, save_path, Path(__file__).with_name('1.html'))
M.parser_types = (WahlMenuParser,)

if __name__ == '__main__':
    M.run()



