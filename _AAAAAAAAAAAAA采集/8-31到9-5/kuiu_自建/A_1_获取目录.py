import json
import subprocess
from pathlib import Path

from config import base_url, Tool


HTML_PATH = Path(__file__).with_name('1.html')
SAVE_PATH = Tool.File.path_add_site('data/ml.json')
HEADER_ASSIGNMENT = "window.__VPV.sections['global-header'] ="


def extract_object(source, start):
    """Extract one JavaScript object literal while respecting quoted strings."""
    start = source.index('{', start)
    depth = 0
    quote = None
    escaped = False

    for index in range(start, len(source)):
        character = source[index]
        if quote:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif character == quote:
                quote = None
            continue

        if character in "'\"`":
            quote = character
        elif character == '{':
            depth += 1
        elif character == '}':
            depth -= 1
            if depth == 0:
                return source[start:index + 1]

    raise ValueError('global-header navigation configuration is not complete')


def load_html():
    response = Tool.get(base_url)
    if response.status_code == 200 and response.text:
        Tool.HTML.save(response.text, HTML_PATH)
        return response.text

    if HTML_PATH.exists():
        Tool.print(f'首页请求失败（{response.status_code}），使用本地 HTML', color='yellow')
        return HTML_PATH.read_text(encoding='utf-8')

    raise RuntimeError(f'首页请求失败（{response.status_code}），且本地 HTML 不存在')


def load_shop_drawers():
    source = load_html()
    starts = []
    position = 0
    while True:
        position = source.find(HEADER_ASSIGNMENT, position)
        if position < 0:
            break
        starts.append(position)
        position += len(HEADER_ASSIGNMENT)

    for start in reversed(starts):
        payload = extract_object(source, start)
        if 'shopDrawers' not in payload:
            continue

        # The saved page comments scripts, but the original response executes this object.
        runner = (
            "const fs=require('fs');"
            "const window={__VPV:{sections:{'global-header':{}}}};"
            "window.__VPV.sections['global-header']=eval('('+fs.readFileSync(0,'utf8')+')');"
            "process.stdout.write(JSON.stringify(window.__VPV.sections['global-header']));"
        )
        result = subprocess.run(
            ['node', '-e', runner],
            input=payload,
            capture_output=True,
            check=True,
            encoding='utf-8',
            text=True,
        )
        config = json.loads(result.stdout)
        for key in ('shopDrawersAB', 'shopDrawers'):
            if key in config:
                return config[key]

    raise ValueError('No shop drawer configuration was found')


def is_collection_url(url):
    url = (url or '').lower()
    return '/collections' in url and '/product' not in url


def clean_name(name):
    return (name or '').strip().removesuffix('==us').removesuffix('==ca')


def add_node(nodes, item):
    name = clean_name(item.get('title'))
    children = {}
    for child in item.get('linkList', []) + item.get('links', []):
        add_node(children, child)

    url = item.get('url', '')
    if is_collection_url(url):
        url = Tool.URL.add_site(url)
    else:
        url = ''

    if name and (url or children) and name not in nodes:
        nodes[name] = {'url': url, 'child': children}


@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1():
    menu = {}
    for drawer in load_shop_drawers():
        add_node(menu, drawer)
    return menu


def run():
    menu = f1()
    Tool.to_ml_json(menu, SAVE_PATH)
    Tool.print(f'已采集 {len(menu)} 个一级目录', color='green')


if __name__ == '__main__':
    run()
