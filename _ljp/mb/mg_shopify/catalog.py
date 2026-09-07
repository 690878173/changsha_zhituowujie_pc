"""魔改 Shopify 首页目录采集。

这里仅处理 Storefront/Hydrogen/React 流等魔改 Shopify 页面结构；普通
Shopify 主题的菜单解析位于 ``_ljp.mb.shopify.catalog``。
"""

import json

from lxml import html as lxml_html

from _ljp.mb.catalog import CatalogCollectorBase, CatalogParser, clean_text, is_collection_url


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
    return clean_text(text), url


def _put(nodes, name, url='', child=None, collector=None, depth=0):
    collector.put_node(nodes, name, url, child, depth)


def _iter_standard_child_items(data, item):
    """递归寻找 React 流对象中的菜单项。

    不同 Oxygen/Hydrogen 版本使用的字段编号不同：有的通过
    ``_321/_323`` 保存子项，有的通过 ``_320/_322`` 保存。菜单项本身
    都带有 ``_197``，因此只在魔改 Shopify 解析器内按这个特征递归。
    """
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


def _parse_standard_item(data, value, collector, depth=0):
    item = _node(data, value)
    name_ref = _node(data, item.get('_197'))
    name = _resolve(data, name_ref.get('_82'))
    if not isinstance(name, str):
        return {}
    url_ref = _node(data, item.get('_76'))
    url = _resolve(data, url_ref.get('_82'))
    if not isinstance(url, str):
        url = ''
    child = {}
    for child_item in _iter_standard_child_items(data, item):
        child.update(_parse_standard_item(data, child_item, collector, depth + 1))
    result = {}
    _put(result, name, url, child, collector, depth)
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


def _bylt_group(data, group_ref, collector, depth=0):
    group = _node(data, group_ref)
    main = _indexed_link(data, group.get('_2625'))
    if not main:
        return None
    name, url = main
    child = {}
    for link_ref in _resolve(data, group.get('_2667')) or []:
        link = _indexed_link(data, link_ref)
        if link:
            _put(child, link[0], link[1], collector=collector, depth=depth + 1)
    return name, url, child


def _collect_bylt_links(data, value, collector, result, seen, depth=0):
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
            _put(result, link[0], link[1], collector=collector, depth=depth)
        for child in value.values():
            _collect_bylt_links(data, child, collector, result, seen, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _collect_bylt_links(data, child, collector, result, seen, depth)


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
        centerlinks = _resolve(data, item.get('_2650'))
        for center_ref in centerlinks or []:
            center = _node(data, center_ref)
            for group_ref in _resolve(data, center.get('_2653')) or []:
                group = _bylt_group(data, group_ref, collector, 1)
                if group:
                    _put(child, group[0], group[1], group[2], collector, 1)
        if not child:
            _collect_bylt_links(
                data,
                _resolve(data, item.get('_2745')),
                collector,
                child,
                set(),
                1,
            )
        _put(result, name, url, child, collector)
    if not result:
        raise RuntimeError('未找到 BYLT menuItem 菜单数据')
    return result


def matching_bracket(text, start):
    """返回 JSON 数组的结束位置。"""
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


def extract_next_navigation(html, collector):
    marker = 'self.__next_f.push([1,"'
    for chunk in html.split(marker)[1:]:
        payload = chunk.split('"])', 1)[0]
        try:
            decoded = json.loads('"' + payload + '"')
        except (TypeError, json.JSONDecodeError):
            continue
        data_marker = 'navigationData":['
        start = decoded.find(data_marker)
        if start < 0:
            continue
        start += len('navigationData":')
        end = matching_bracket(decoded, start)
        if end is None:
            continue
        return _next_menu(json.loads(decoded[start:end]), collector)
    raise RuntimeError('首页中未找到 navigationData 目录数据')


def _next_menu(items, collector):
    result = {}
    for item in items:
        name = clean_text(item.get('linkTitle') or item.get('name') or '')
        url = item.get('slug') or ''
        child = {}
        for group in item.get('linkCollection') or []:
            links = [
                link for link in group.get('links') or []
                if link.get('linkTitle') or link.get('name')
            ]
            if not links:
                continue
            heading = links[0]
            group_child = {}
            for link in links[1:]:
                _put(
                    group_child,
                    link.get('linkTitle') or link.get('name'),
                    link.get('slug') or '',
                    collector=collector,
                    depth=2,
                )
            group_name = heading.get('linkTitle') or heading.get('name')
            group_url = heading.get('slug') or ''
            if group_child or collector.should_keep_url(collector.normalize_url(group_url)):
                _put(child, group_name, group_url, group_child, collector, 1)
        _put(result, name, url, child, collector)
    return result


class StandardStreamParser(CatalogParser):
    """解析标准魔改 Shopify React 流菜单。"""

    menu_keys = ('headerPrimaryMenu', 'headerMenu')

    def matches(self, html):
        return any(menu_key in html for menu_key in self.menu_keys)

    def parse(self, html, collector):
        return extract_standard_navigation(load_stream_data(html), collector)


class ByltStreamParser(CatalogParser):
    """解析 BYLT 的 React 流菜单。"""

    def matches(self, html):
        return '_2628' in html

    def parse(self, html, collector):
        return extract_bylt_navigation(load_stream_data(html), collector)


class NextNavigationParser(CatalogParser):
    """解析 Next.js ``navigationData`` 菜单。"""

    def matches(self, html):
        return 'navigationData' in html and 'self.__next_f.push' in html

    def parse(self, html, collector):
        return extract_next_navigation(html, collector)


class HydrogenHeaderParser(CatalogParser):
    """解析 Hydrogen/React Router 渲染在 HTML 中的头部菜单。"""

    header_xpath = '//header[@id="header-nav"]'
    desktop_menu_xpath = './/*[@data-comp="DesktopMenu"]'

    def matches(self, html):
        return 'id="header-nav"' in html and 'data-comp="DesktopMenu"' in html

    @staticmethod
    def link_text(element):
        values = element.xpath('.//text()[not(ancestor::svg)]')
        return clean_text(' '.join(values))

    def parse_dropdown(self, dropdown, collector, depth=1):
        result = {}
        for link in dropdown.xpath('.//a[@href]'):
            name = self.link_text(link)
            if name:
                collector.put_node(result, name, link.get('href') or '', depth=depth)
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

        top_items = main_navs[0].xpath('./ul/li')
        dropdowns = desktop_menus[0].xpath('./nav')
        result = {}
        for index, item in enumerate(top_items):
            link = item.xpath('./a[@href][1]')
            children = item.xpath('./*')
            element = link[0] if link else children[0] if children else item
            name = self.link_text(element)
            url = link[0].get('href') if link else ''
            child = self.parse_dropdown(dropdowns[index], collector) if index < len(dropdowns) else {}
            collector.put_node(result, name, url or '', child, index)
        if not result:
            raise RuntimeError('Hydrogen 主菜单没有可用目录')
        return result


class CatalogCollector(CatalogCollectorBase):
    """魔改 Shopify 自己的目录采集器。"""

    parser_types = (
        HydrogenHeaderParser,
        NextNavigationParser,
        ByltStreamParser,
        StandardStreamParser,
    )


def collect_catalog(tool, base_url, html_path, save_path, collector_cls=CatalogCollector):
    """使用魔改 Shopify 内置解析器采集目录。"""
    return collector_cls(tool, base_url, html_path, save_path).run()


__all__ = [
    'CatalogCollector',
    'CatalogParser',
    'HydrogenHeaderParser',
    'NextNavigationParser',
    'ByltStreamParser',
    'StandardStreamParser',
    'collect_catalog',
]
