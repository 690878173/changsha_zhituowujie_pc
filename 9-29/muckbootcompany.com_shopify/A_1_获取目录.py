from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol


class ThemeLinklistParser(CatalogParser):
    """解析主题公开的 ``theme.linklist`` 多级导航数据。"""

    menu_variable = 'theme.linklist'

    def matches(self, html):
        return self.menu_variable in html

    @staticmethod
    def clean_name(value):
        return ' '.join(str(value or '').split()).replace(',', ' ')

    @staticmethod
    def is_collection_url(url):
        path = urlsplit(url or '').path.rstrip('/').lower()
        return path.startswith('/collections/') and path != '/collections'

    def parse_links(self, links, collector):
        result = {}
        for link in links or []:
            if not isinstance(link, dict):
                continue
            name = self.clean_name(link.get('title'))
            if not name:
                continue
            child = self.parse_links(link.get('links'), collector)
            href = link.get('url') or ''
            url = collector.normalize_url(href) if href else ''
            if not self.is_collection_url(url):
                href = ''
            if not href and not child:
                continue
            collector.add_node(result, name, href, child)
        return result

    @staticmethod
    def collect_urls(nodes, found=None):
        if found is None:
            found = set()
        for node in nodes.values():
            url = node.get('url')
            if url:
                found.add(url)
            ThemeLinklistParser.collect_urls(node.get('child') or {}, found)
        return found

    def link_name(self, link):
        text = self.clean_name(' '.join(link.xpath('.//text()')))
        if text:
            return text
        for value in (
            link.get('aria-label'),
            link.get('title'),
            *(link.xpath('.//img/@alt')),
        ):
            text = self.clean_name(value)
            if text:
                return text
        return ''

    def parse_other_links(self, html, collector, known):
        tree = {}
        for link in html.xpath('//a[@href]'):
            href = link.get('href') or ''
            url = collector.normalize_url(href) if href else ''
            if not self.is_collection_url(url) or url in known:
                continue
            name = self.link_name(link)
            if not name:
                continue
            unique_name = name
            handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            number = 2
            while unique_name in tree:
                unique_name = f'{name} ({handle})'
                if unique_name in tree:
                    unique_name = f'{name} ({handle} {number})'
                    number += 1
            if collector.add_node(tree, unique_name, href) is not None:
                known.add(url)
        return tree

    def parse(self, html, collector):
        payload = collector.tool.HTML.extract_js_object(html, self.menu_variable)
        if not isinstance(payload, dict):
            raise RuntimeError('theme.linklist 导航数据解析失败')
        result = self.parse_links(payload.get('links'), collector)
        if not result:
            raise RuntimeError('theme.linklist 没有可用目录')

        page = lxml_html.fromstring(html)
        extra = self.parse_other_links(page, collector, self.collect_urls(result))
        if extra:
            group_name = 'Other'
            number = 2
            while group_name in result:
                group_name = f'Other{number}'
                number += 1
            collector.add_node(result, group_name, '', extra)
        return result


snapshot_path = Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html'
M = CatCol(
    Tool,
    base_url,
    Tool.File.path_add_site('data/ml.json'),
    snapshot_path,
)
M.parser_types = (ThemeLinklistParser, *M.parser_types)


if __name__ == '__main__':
    M.run()



