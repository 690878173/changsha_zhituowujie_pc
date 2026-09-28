from pathlib import Path
from re import fullmatch
from urllib.parse import urlsplit, urlunsplit

from lxml import html as lxml_html

from config import Tool, base_url
from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


save_path = Tool.File.path_add_site('data/ml.json')


class EksterMenuParser(CatalogParser):
    """Parse Ekster's server-rendered menu-blocks navigation."""

    def matches(self, html):
        return 'data-nav-primary' in html and 'mega-menu-level-two-three' in html

    @staticmethod
    def text(node):
        return ' '.join(' '.join(node.xpath('.//text()[not(ancestor::svg)]')).split())

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.rstrip('/').lower()
        return path.startswith('/collections/')

    def collection_url(self, href, collector):
        if not href or href.startswith('#'):
            return ''
        url = collector.normalize_url(href)
        parts = urlsplit(url)
        path_parts = parts.path.split('/')
        if (
            len(path_parts) > 2
            and fullmatch(r'[a-z]{2}(?:-[a-z]{2,3})?', path_parts[1].lower())
            and path_parts[2].lower() == 'collections'
        ):
            canonical_path = '/' + '/'.join(path_parts[2:])
            url = urlunsplit((parts.scheme, parts.netloc, canonical_path, parts.query, ''))
        return url if self.is_collection(url) else ''

    @staticmethod
    def fallback_name(url):
        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
        return handle.replace('-', ' ').title()

    def add_collection(self, nodes, name, href, collector):
        url = self.collection_url(href, collector)
        if not url:
            return ''
        if any(node.get('url') == url for node in nodes.values()):
            return ''

        base_name = ' '.join((name or '').split()) or self.fallback_name(url)
        node_name = base_name
        suffix = 2
        while node_name in nodes and nodes[node_name].get('url') != url:
            node_name = f'{base_name} ({suffix})'
            suffix += 1
        if node_name in nodes:
            return ''

        collector.add_node(nodes, node_name, url)
        return url

    def parse_panel(self, panel, collector):
        children = {}
        for link in panel.xpath('.//a[@href]'):
            self.add_collection(children, self.text(link), link.get('href') or '', collector)
        return children

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        desktop_menus = tree.xpath('//header//menu-blocks[.//*[@data-nav-primary]]')
        if not desktop_menus:
            raise RuntimeError('Ekster desktop menu was not found')

        desktop_menu = desktop_menus[0]
        result = {}
        known_urls = set()
        controls = desktop_menu.xpath(
            './/*[@data-nav-primary]//*[@data-menu-blocks="trigger"][@aria-controls]'
        )
        for control in controls:
            name = self.text(control)
            target_id = control.get('aria-controls')
            if not name or not target_id:
                continue
            panels = desktop_menu.xpath('.//*[@id=$target_id]', target_id=target_id)
            if not panels:
                panels = tree.xpath('//*[@id=$target_id]', target_id=target_id)
            if not panels:
                continue
            children = self.parse_panel(panels[0], collector)
            if not children:
                continue
            collector.add_node(result, name, '', children)
            known_urls.update(
                node['url'] for node in children.values() if node.get('url')
            )

        if not result:
            raise RuntimeError('Ekster desktop menu produced no collection URLs')

        navigation_only = {}
        for link in tree.xpath('//header//a[@href]'):
            url = self.collection_url(link.get('href') or '', collector)
            if not url or url in known_urls:
                continue
            if self.add_collection(navigation_only, self.text(link), link.get('href') or '', collector):
                known_urls.add(url)
        if navigation_only:
            collector.add_node(result, 'Navigation', '', navigation_only)

        other = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath('ancestor::header'):
                continue
            url = self.collection_url(link.get('href') or '', collector)
            if not url or url in known_urls:
                continue
            if self.add_collection(other, self.text(link), link.get('href') or '', collector):
                known_urls.add(url)
        if other:
            group_name = 'Other' if 'Other' not in result else 'Other2'
            collector.add_node(result, group_name, '', other)
        return result


class EksterCatCol(ShopifyCatCol):
    parser_types = (EksterMenuParser,)


if __name__ == '__main__':
    try:
        EksterCatCol(
            Tool,
            base_url,
            save_path,
            Path(__file__).parent / 'ts' / '01-catalog' / 'homepage.html',
        ).run()
    finally:
        Tool.close()
