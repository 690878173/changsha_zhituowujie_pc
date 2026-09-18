from pathlib import Path

from config import Tool, base_url
from _ljp.mb.mg_shopify import CatCol


save_path = Tool.File.path_add_site('data/ml.json')
snapshot_path = Path(__file__).parent / 'ts' / '1' / 'homepage.html'
M = CatCol(Tool, base_url, save_path, snapshot_path)


if __name__ == '__main__':
    M.run()
    Tool.close()
