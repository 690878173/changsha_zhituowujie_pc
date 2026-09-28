from config import Tool
from _ljp.mb.shopify import Replace_imgs


input_file = Tool.File.path_add_site('fwq/quchong.csv')
output_file = Tool.File.path_add_site('res/picture.csv')
new_url_base = f'https://cdn.zhimatrix.com/{Tool.site}_shopify_ljp/images/'


class EksterReplaceImages(Replace_imgs):
    def build_new_url_base(self):
        return new_url_base


if __name__ == '__main__':
    try:
        EksterReplaceImages(Tool, input_path=input_file, output_path=output_file).run()
    finally:
        Tool.close()
