import json
from pathlib import Path
from urllib.parse import urlsplit


def clean_text(value):
    text = ' '.join(str(value or '').split())
    for suffix in (' →', ' ➜'):
        if text.endswith(suffix):
            text = text[:-len(suffix)].rstrip()
    return text


def is_collection_url(url):
    path = urlsplit(url or '').path.lower()
    return '/collections' in path and '/product' not in path


def load_stream_data(html):
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


def _put(nodes, name, url='', child=None, tool=None):
    name = clean_text(name)
    if not name:
        return
    if tool and url:
        url = tool.URL.add_site(url)
    if not is_collection_url(url):
        url = ''
    item = nodes.setdefault(name, {'url': '', 'child': child or {}})
    if url and not item['url']:
        item['url'] = url
    if child:
        item['child'].update(child)


def _parse_standard_item(data, value, tool):
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
    for reference in item.values():
        child_ref = _node(data, reference)
        if '_321' not in child_ref:
            continue
        child_data = _node(data, child_ref.get('_321'))
        child_items = _resolve(data, child_data.get('_323'))
        if isinstance(child_items, list):
            for child_item in child_items:
                child.update(_parse_standard_item(data, child_item, tool))
            break
    result = {}
    _put(result, name, url, child, tool)
    return result


def extract_standard_navigation(data, tool):
    for menu_key in ('headerPrimaryMenu', 'headerMenu'):
        try:
            menu_items = _resolve(data, data.index(menu_key) + 1)
        except ValueError:
            continue
        if not isinstance(menu_items, list):
            continue
        result = {}
        for item in menu_items:
            result.update(_parse_standard_item(data, item, tool))
        return result
    raise RuntimeError('未找到 headerPrimaryMenu 或 headerMenu 菜单数据')


def _bylt_group(data, group_ref, tool):
    group = _node(data, group_ref)
    main = _indexed_link(data, group.get('_2625'))
    if not main:
        return None
    name, url = main
    child = {}
    for link_ref in _resolve(data, group.get('_2667')) or []:
        link = _indexed_link(data, link_ref)
        if link:
            _put(child, link[0], link[1], tool=tool)
    return name, url, child


def _collect_bylt_links(data, value, tool, result, seen):
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
            _put(result, link[0], link[1], tool=tool)
        for child in value.values():
            _collect_bylt_links(data, child, tool, result, seen)
    elif isinstance(value, list):
        for child in value:
            _collect_bylt_links(data, child, tool, result, seen)


def extract_bylt_navigation(data, tool):
    result = {}
    for item in data:
        if not isinstance(item, dict) or '_2628' not in item:
            continue
        # BYLT stores the visible top-level link in menuItem; the neighboring
        # mainLink field is absent or only contains a presentation reference
        # for some items (for example Women and Kids).
        top = _indexed_link(data, item.get('_2628'))
        if not top:
            continue
        name, url = top
        child = {}
        centerlinks = _resolve(data, item.get('_2650'))
        for center_ref in centerlinks or []:
            center = _node(data, center_ref)
            for group_ref in _resolve(data, center.get('_2653')) or []:
                group = _bylt_group(data, group_ref, tool)
                if group:
                    _put(child, group[0], group[1], group[2], tool)
        if not child:
            _collect_bylt_links(data, _resolve(data, item.get('_2745')), tool, child, set())
        _put(result, name, url, child, tool)
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


def extract_next_navigation(html, tool):
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
        return _next_menu(json.loads(decoded[start:end]), tool)
    raise RuntimeError('首页中未找到 navigationData 目录数据')


def _next_menu(items, tool):
    result = {}
    for item in items:
        name = clean_text(item.get('linkTitle') or item.get('name') or '')
        url = item.get('slug') or ''
        child = {}
        for group in item.get('linkCollection') or []:
            links = [link for link in group.get('links') or [] if link.get('linkTitle') or link.get('name')]
            if not links:
                continue
            heading = links[0]
            group_child = {}
            for link in links[1:]:
                _put(group_child, link.get('linkTitle') or link.get('name'), link.get('slug') or '', tool=tool)
            group_name = heading.get('linkTitle') or heading.get('name')
            group_url = heading.get('slug') or ''
            if group_child or is_collection_url(tool.URL.add_site(group_url)):
                _put(child, group_name, group_url, group_child, tool)
        _put(result, name, url, child, tool)
    return result


def load_html_and_catalog(tool, base_url, html_path):
    response = tool.get(base_url)
    if response.status_code == 200 and response.text:
        tool.HTML.save(response.text, html_path)
        html = response.text
    elif Path(html_path).exists():
        tool.print(f'首页请求失败（{response.status_code}），使用本地 HTML', color='yellow')
        html = Path(html_path).read_text(encoding='utf-8')
    else:
        raise RuntimeError(f'首页请求失败（{response.status_code}），且本地 HTML 不存在')

    if 'navigationData' in html and 'self.__next_f.push' in html:
        return extract_next_navigation(html, tool)
    data = load_stream_data(html)
    if any(isinstance(item, dict) and '_2628' in item for item in data):
        return extract_bylt_navigation(data, tool)
    return extract_standard_navigation(data, tool)


def collect_catalog(tool, base_url, html_path, save_path):
    menu = load_html_and_catalog(tool, base_url, html_path)
    tool.to_ml_json(menu, save_path)
    return menu
