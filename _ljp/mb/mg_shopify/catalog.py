"""魔改 Shopify 首页目录解析。"""

import json
from urllib.parse import urlsplit

from lxml import html as lxml_html

from _ljp.mb.base.get_ml import BaseCatalogParser, CatalogParser, CatCol as BaseCatCol


def _clean_text(value):
    text = ' '.join(str(value or '').split())
    for suffix in (' ->', ' >'):
        if text.endswith(suffix):
            text = text[:-len(suffix)].rstrip()
    return text


def _is_collection_url(url):
    path = urlsplit(url or '').path.lower()
    return '/collections' in path and '/product' not in path


def _put_node(collector, nodes, name, url='', child=None):
    normalized_url = collector.normalize_url(url) if url else ''
    if normalized_url and not _is_collection_url(normalized_url):
        normalized_url = ''
    return collector.add_node(nodes, name, normalized_url, child)


def load_stream_data(html):
    """解码 Shopify React stream 数据。"""
    marker = 'streamController.enqueue("'
    data = []
    position = 0
    while True:
        start = html.find(marker, position)
        if start < 0:
            break
        start += len(marker)
        end = start
        while True:
            end = html.find('"', end)
            if end < 0:
                raise RuntimeError('Shopify 流数据不完整')
            slash_count = 0
            cursor = end - 1
            while cursor >= start and html[cursor] == '\\':
                slash_count += 1
                cursor -= 1
            if slash_count % 2 == 0:
                break
            end += 1
        stream = json.loads('"' + html[start:end] + '"')
        payload = stream.split(':', 1)[-1] if stream.startswith('P') else stream
        if payload.startswith('['):
            data.extend(json.loads(payload))
        position = end + 1
    if not data:
        raise RuntimeError('页面中未找到 Shopify 流数据')
    return data


def _resolve(data, value):
    if isinstance(value, int) and 0 <= value < len(data):
        return data[value]
    return value


def _node(data, value):
    value = _resolve(data, value)
    return value if isinstance(value, dict) else {}


def _field(data, node, key):
    return _resolve(data, node.get(key))


def _indexed_link(data, value):
    node = _node(data, value)
    url = _field(data, node, '_302')
    text = _field(data, node, '_365')
    if not isinstance(url, str) or not isinstance(text, str):
        return None
    return _clean_text(text), url


def _iter_standard_child_items(data, item):
    seen = set()

    def walk(value, is_root=False):
        value = _resolve(data, value)
        if isinstance(value, list):
            for child in value:
                yield from walk(child)
            return
        if not isinstance(value, dict):
            return
        if not is_root and '_197' in value:
            yield value
            return
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)
        for child in value.values():
            yield from walk(child)

    yield from walk(item, is_root=True)


def _parse_standard_item(data, value, collector):
    item = _node(data, value)
    name = _resolve(data, _node(data, item.get('_197')).get('_82'))
    if not isinstance(name, str):
        return {}
    url = _resolve(data, _node(data, item.get('_76')).get('_82'))
    if not isinstance(url, str):
        url = ''
    child = {}
    for child_item in _iter_standard_child_items(data, item):
        child.update(_parse_standard_item(data, child_item, collector))
    result = {}
    _put_node(collector, result, name, url, child)
    return result


def extract_standard_navigation(data, collector):
    for menu_key in ('headerPrimaryMenu', 'headerMenu'):
        try:
            menu_items = _resolve(data, data.index(menu_key) + 1)
        except ValueError:
            continue
        if not isinstance(menu_items, list):
            continue
        result = {}
        for item in menu_items:
            result.update(_parse_standard_item(data, item, collector))
        if result:
            return result
    raise RuntimeError('未找到 headerPrimaryMenu 或 headerMenu 菜单数据')


def _bylt_group(data, group_ref, collector):
    group = _node(data, group_ref)
    main = _indexed_link(data, group.get('_2625'))
    if not main:
        return None
    name, url = main
    child = {}
    for link_ref in _resolve(data, group.get('_2667')) or []:
        link = _indexed_link(data, link_ref)
        if link:
            _put_node(collector, child, link[0], link[1])
    return name, url, child


def _collect_bylt_links(data, value, collector, result, seen):
    value = _resolve(data, value)
    if isinstance(value, int):
        return
    if isinstance(value, dict):
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)
        link = _indexed_link(data, value)
        if link:
            _put_node(collector, result, link[0], link[1])
        for child in value.values():
            _collect_bylt_links(data, child, collector, result, seen)
    elif isinstance(value, list):
        for child in value:
            _collect_bylt_links(data, child, collector, result, seen)


def extract_bylt_navigation(data, collector):
    result = {}
    for item in data:
        if not isinstance(item, dict) or '_2628' not in item:
            continue
        top = _indexed_link(data, item.get('_2628'))
        if not top:
            continue
        name, url = top
        child = {}
        for center_ref in _resolve(data, item.get('_2650')) or []:
            center = _node(data, center_ref)
            for group_ref in _resolve(data, center.get('_2653')) or []:
                group = _bylt_group(data, group_ref, collector)
                if group:
                    _put_node(collector, child, group[0], group[1], group[2])
        if not child:
            _collect_bylt_links(data, _resolve(data, item.get('_2745')), collector, child, set())
        _put_node(collector, result, name, url, child)
    if not result:
        raise RuntimeError('未找到 BYLT menuItem 菜单数据')
    return result


def matching_bracket(text, start):
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == '[':
            depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _next_menu(items, collector):
    result = {}
    for item in items:
        name = _clean_text(item.get('linkTitle') or item.get('name') or '')
        url = item.get('slug') or ''
        child = {}
        for group in item.get('linkCollection') or []:
            links = [link for link in group.get('links') or [] if link.get('linkTitle') or link.get('name')]
            if not links:
                continue
            heading = links[0]
            group_child = {}
            for link in links[1:]:
                _put_node(
                    collector,
                    group_child,
                    link.get('linkTitle') or link.get('name'),
                    link.get('slug') or '',
                )
            group_name = heading.get('linkTitle') or heading.get('name')
            group_url = heading.get('slug') or ''
            normalized_url = collector.normalize_url(group_url) if group_url else ''
            if group_child or _is_collection_url(normalized_url):
                _put_node(collector, child, group_name, group_url, group_child)
        _put_node(collector, result, name, url, child)
    return result


def extract_next_navigation(html, collector):
    marker = 'self.__next_f.push([1,"'
    for chunk in html.split(marker)[1:]:
        payload = chunk.split('"])', 1)[0]
        try:
            decoded = json.loads('"' + payload + '"')
        except (TypeError, json.JSONDecodeError):
            continue
        start = decoded.find('navigationData":[')
        if start < 0:
            continue
        start += len('navigationData":')
        end = matching_bracket(decoded, start)
        if end is not None:
            return _next_menu(json.loads(decoded[start:end]), collector)
    raise RuntimeError('首页中未找到 navigationData 目录数据')


class HeaderInlineMenuParser(BaseCatalogParser):
    """解析 Dawn 系 ``header__inline-menu`` 三层菜单。"""

    menu_xpath = '//nav[contains(concat(" ", normalize-space(@class), " "), " header__inline-menu ")]'

    def matches(self, html):
        return 'header__inline-menu' in html

    @staticmethod
    def text(node, xpath):
        return _clean_text(' '.join(node.xpath(xpath)))

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        menus = tree.xpath(self.menu_xpath)
        if not menus:
            raise RuntimeError('页面中未找到 header__inline-menu 菜单')
        result = {}
        for details in menus[0].xpath('./ul/li/header-menu/details'):
            name = self.text(details, './summary/span//text()')
            if not name:
                continue
            child = {}
            for group in details.xpath('./div/ul/li'):
                group_name = self.text(group, './span//text()')
                leaves = {}
                for link in group.xpath('./ul/li/a[@href]'):
                    leaf_name = _clean_text(' '.join(link.xpath('.//text()[not(ancestor::svg)]')))
                    if leaf_name:
                        _put_node(collector, leaves, leaf_name, link.get('href') or '')
                if group_name:
                    _put_node(collector, child, group_name, '', leaves)
                else:
                    child.update(leaves)
            _put_node(collector, result, name, '', child)
        if not result:
            raise RuntimeError('header__inline-menu 没有可用目录')
        return result


class StandardStreamParser(BaseCatalogParser):
    """解析标准魔改 Shopify React 流菜单。"""

    menu_keys = ('headerPrimaryMenu', 'headerMenu')

    def matches(self, html):
        return any(menu_key in html for menu_key in self.menu_keys)

    def parse(self, html, collector):
        return extract_standard_navigation(load_stream_data(html), collector)


class ByltStreamParser(BaseCatalogParser):
    """解析 BYLT 的 React 流菜单。"""

    def matches(self, html):
        return '_2628' in html

    def parse(self, html, collector):
        return extract_bylt_navigation(load_stream_data(html), collector)


class NextNavigationParser(BaseCatalogParser):
    """解析 Next.js ``navigationData`` 菜单。"""

    def matches(self, html):
        return 'navigationData' in html and 'self.__next_f.push' in html

    def parse(self, html, collector):
        return extract_next_navigation(html, collector)


class HydrogenHeaderParser(BaseCatalogParser):
    """解析 Hydrogen/React Router 渲染在 HTML 中的头部菜单。"""

    header_xpath = '//header[@id="header-nav"]'
    desktop_menu_xpath = './/*[@data-comp="DesktopMenu"]'

    def matches(self, html):
        return 'id="header-nav"' in html and 'data-comp="DesktopMenu"' in html

    @staticmethod
    def link_text(element):
        return _clean_text(' '.join(element.xpath('.//text()[not(ancestor::svg)]')))

    def parse_dropdown(self, dropdown, collector):
        result = {}
        for link in dropdown.xpath('.//a[@href]'):
            name = self.link_text(link)
            if name:
                _put_node(collector, result, name, link.get('href') or '')
        return result

    def parse(self, html, collector):
        tree = lxml_html.fromstring(html)
        headers = tree.xpath(self.header_xpath)
        if not headers:
            raise RuntimeError('页面中未找到 header#header-nav')
        header = headers[0]
        main_navs = header.xpath('.//div[@data-comp="header-navigation"]//nav')
        desktop_menus = header.xpath(self.desktop_menu_xpath)
        if not main_navs or not desktop_menus:
            raise RuntimeError('页面中未找到 Hydrogen 主菜单或下拉菜单')
        result = {}
        dropdowns = desktop_menus[0].xpath('./nav')
        for index, item in enumerate(main_navs[0].xpath('./ul/li')):
            link = item.xpath('./a[@href][1]')
            children = item.xpath('./*')
            element = link[0] if link else children[0] if children else item
            child = self.parse_dropdown(dropdowns[index], collector) if index < len(dropdowns) else {}
            _put_node(collector, result, self.link_text(element), link[0].get('href') if link else '', child)
        if not result:
            raise RuntimeError('Hydrogen 主菜单没有可用目录')
        return result


class CatCol(BaseCatCol):
    """魔改 Shopify 目录采集器。"""

    parser_types = (
        HeaderInlineMenuParser,
        HydrogenHeaderParser,
        NextNavigationParser,
        ByltStreamParser,
        StandardStreamParser,
    )
    skip_url_ls = []
    no_url_ls = []


__all__ = [
    'BaseCatalogParser',
    'ByltStreamParser',
    'CatCol',
    'HeaderInlineMenuParser',
    'HydrogenHeaderParser',
    'NextNavigationParser',
    'StandardStreamParser',
    'CatalogParser'
]
