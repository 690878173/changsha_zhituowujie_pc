from pathlib import Path

from config import Tool, base_url
from catalog import TommyJohnCatCol


if __name__ == '__main__':
    TommyJohnCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).with_name('1.html'),
    ).run()
    Tool.close()
