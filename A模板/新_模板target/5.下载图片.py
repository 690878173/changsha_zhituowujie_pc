from pathlib import Path

from config import Tool
from _ljp.mb.base import download_new


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    downloader = download_new.IMG_download_ljp(base_dir / "config.ini")
    downloader.config["PATHS"]["input_csv"] = str(Tool.File.path_add_site("fwq/variable.csv"))
    downloader.config["PATHS"]["output_images"] = str(Tool.File.path_add_site("images"))
    downloader.failed_log = str(Tool.File.path_add_site("fail/failed_images.txt"))
    downloader.config["PATHS"]["failed_log"] = downloader.failed_log
    downloader.config["REQUEST"]["csv_images_split"] = Tool.config.images_split
    downloader.run()
