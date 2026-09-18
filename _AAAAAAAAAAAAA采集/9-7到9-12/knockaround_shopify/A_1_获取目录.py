from pathlib import Path

from config import base_url, Tool
from _ljp.mb.shopify import CatCol

if __name__ == '__main__':
    CatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).with_name('1.html'),
    ).run()


