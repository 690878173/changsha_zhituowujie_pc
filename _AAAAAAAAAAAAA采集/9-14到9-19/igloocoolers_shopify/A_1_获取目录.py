from pathlib import Path

from config import base_url, Tool

save_path = Tool.File.path_add_site('data/ml.json')
from catalog import IglooCoolersCatCol


M = IglooCoolersCatCol(
    Tool,
    base_url,
    save_path,
    Path(__file__).with_name('1.html'),
)


if __name__ == '__main__':
    M.run()
    Tool.close()


