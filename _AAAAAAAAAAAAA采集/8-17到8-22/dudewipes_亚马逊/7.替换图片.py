from config import Tool
from _ljp.mb.base import Replace_imgs

# CDN prefix must match the location where step 6 output is published.
image_url_base = f"https://cdn.zhimatrix.com/{Tool.site}_ljp/images/"

class CdnImageStep(Replace_imgs):
    def build_new_url_base(self):
        return image_url_base


if __name__ == "__main__":
    CdnImageStep(Tool, input_path=Tool.File.path_add_site("fwq/variable.csv")).run()
