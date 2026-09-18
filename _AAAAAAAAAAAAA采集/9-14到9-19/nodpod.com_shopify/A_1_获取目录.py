"""阶段 1：获取目录。

nodpod 首页主题使用自研的 ``nav.nodpod-mega`` mega menu，内置 Shopify 解析器
无法识别，因此在本脚本内注册站点专属解析器。解析器只保留 collection 链接、
保留真实菜单层级；导航栏之外的 collection 链接（公告栏、首页卡片、页脚、移动
端抽屉）统一挂到一级目录 ``Other``。
"""

from pathlib import Path
from urllib.parse import urlsplit

from lxml import html as lxml_html

from config import Tool, base_url

from _ljp.mb.base.get_ml import CatalogParser
from _ljp.mb.shopify import CatCol as ShopifyCatCol


class NodpodMegaMenuParser(CatalogParser):
    """解析 ``nav.nodpod-mega`` 菜单结构。"""

    nav_xpath = (
        '//nav[contains(concat(" ", normalize-space(@class), " "), " nodpod-mega ")]'
    )
    nav_ancestor_xpath = (
        'ancestor::nav[contains(concat(" ", normalize-space(@class), " "), " nodpod-mega ")]'
    )
    item_xpath = (
        './ul/li[contains(concat(" ", normalize-space(@class), " "), " megamenu-wrapper ")]'
    )
    panel_links_xpath = (
        './/div[contains(concat(" ", normalize-space(@class), " "),'
        ' " megamenu-menu-links ")]/a[@href]'
    )
    card_xpath = (
        './/div[contains(concat(" ", normalize-space(@class), " "),'
        ' " megamenu-menu-image ")]'
    )
    card_title_xpath = (
        './/div[contains(concat(" ", normalize-space(@class), " "),'
        ' " megamenu-image-text ")]//text()'
    )
    text_xpath = './/text()[not(ancestor::svg)]'
    page_group_name = 'Other'
    generic_link_names = frozenset(
        {'shop', 'shop now', 'shop all', 'view all', 'see more', 'learn more', 'buy now'}
    )

    def matches(self, html):
        return 'nodpod-mega' in html and 'megamenu-wrapper' in html

    @staticmethod
    def clean_text(values):
        """合并文本节点并去掉主题 hover 动画留下的 ``->`` 尾巴。"""
        text = ' '.join(' '.join(values).split())
        for suffix in (' ->', ' >'):
            if text.endswith(suffix):
                text = text[:-len(suffix)].rstrip()
        return text

    @classmethod
    def node_text(cls, node, xpath=None):
        return cls.clean_text(node.xpath(xpath or cls.text_xpath))

    @staticmethod
    def is_collection(url):
        path = urlsplit(url or '').path.lower()
        return '/collections' in path and '/product' not in path

    def put_node(self, nodes, name, url, child, collector):
        """写入节点：非 collection 链接置空，空分组直接丢弃。"""
        normalized_url = collector.normalize_url(url) if url else ''
        if normalized_url and not self.is_collection(normalized_url):
            normalized_url = ''
        if not normalized_url and not child:
            return None
        return collector.add_node(nodes, name, normalized_url, child)

    def parse_panel_links(self, item, collector):
        """读取一个一级菜单项内部的二级 collection 链接。"""
        result = {}
        for link in item.xpath(self.panel_links_xpath):
            self.put_node(result, self.node_text(link), link.get('href') or '', {}, collector)
        for card in item.xpath(self.card_xpath):
            links = card.xpath('./a[@href][1]')
            if not links:
                continue
            link = links[0]
            name = self.node_text(card, self.card_title_xpath) or self.node_text(link)
            self.put_node(result, name, link.get('href') or '', {}, collector)
        return result

    @staticmethod
    def tree_urls(nodes, found=None):
        """收集目录树中已经出现的绝对链接，供 ``Other`` 去重。"""
        if found is None:
            found = set()
        for node in nodes.values():
            if node.get('url'):
                found.add(node['url'])
            NodpodMegaMenuParser.tree_urls(node.get('child') or {}, found)
        return found

    def page_link_name(self, link, url):
        """导航外链接命名：aria-label > 链接文本 > URL handle。"""
        label = self.clean_text([link.get('aria-label') or ''])
        if label:
            return label
        name = self.node_text(link)
        if name and name.lower() not in self.generic_link_names:
            return name
        handle = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
        return ' '.join(part for part in handle.replace('_', '-').split('-')).title()

    def parse_page_links(self, tree, collector, known):
        """收集导航栏之外的 collection 链接，作为 ``Other`` 的二级目录。"""
        extra = {}
        for link in tree.xpath('//a[@href]'):
            if link.xpath(self.nav_ancestor_xpath):
                continue
            href = link.get('href') or ''
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue
            url = collector.normalize_url(href)
            if not url or url in known or not self.is_collection(url):
                continue
            if urlsplit(url).path.rstrip('/').endswith('/collections'):
                continue
            if self.put_node(extra, self.page_link_name(link, url), href, {}, collector) is not None:
                known.add(url)
        return extra

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        navs = tree.xpath(self.nav_xpath)
        if not navs:
            raise RuntimeError('页面中未找到 nav.nodpod-mega 菜单')
        result = {}
        for item in navs[0].xpath(self.item_xpath):
            links = item.xpath('./a[@href][1]')
            if not links:
                continue
            link = links[0]
            self.put_node(
                result,
                self.node_text(link),
                link.get('href') or '',
                self.parse_panel_links(item, collector),
                collector,
            )
        if not result:
            raise RuntimeError('nodpod mega 菜单没有可用目录')
        extra = self.parse_page_links(tree, collector, self.tree_urls(result))
        if extra:
            self.put_node(result, self.page_group_name, '', extra, collector)
        return result


class NodpodCatCol(ShopifyCatCol):
    """站点目录采集器：只注册 nodpod 专属解析器。"""

    parser_types = (NodpodMegaMenuParser,)


if __name__ == '__main__':
    NodpodCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).with_name('1.html'),
    ).run()
    Tool.close()
