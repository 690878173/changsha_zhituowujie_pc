from pathlib import Path

from catalog import OrbitkeyCatCol
from config import Tool, base_url


if __name__ == '__main__':
    OrbitkeyCatCol(
        Tool,
        base_url,
        Tool.File.path_add_site('data/ml.json'),
        Path(__file__).with_name('1.html'),
    ).run()
    Tool.close()


