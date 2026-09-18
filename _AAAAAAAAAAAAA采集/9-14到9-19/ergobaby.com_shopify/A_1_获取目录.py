"""阶段 1：获取目录。

ergobaby 首页使用自研的桌面 mega menu 与移动端抽屉菜单，内置 Shopify 解析器
无法识别，因此由站点 ``catalog.py`` 注册专属解析器。

站点首页受 Cloudflare 挑战保护，普通 HTTP 请求会拿到挑战页，``CatCol`` 因此
读取同目录快照 ``ts/1/homepage.html``（真实首页 HTML，由浏览器抓取）。
"""

from pathlib import Path

from config import Tool, base_url
from catalog import ErgobabyCatCol


if __name__ == '__main__':
    ErgobabyCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).parent / 'ts' / '1' / 'homepage.html',
    ).run()
    Tool.close()


