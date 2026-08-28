

from config import Tool
from _ljp.mb.target import Replace_imgs

image_url_base = f"https://cdn.zhimatrix.com/{Tool.site}_target_ljp/images/"

class CdnImageStep(Replace_imgs):
    def build_new_url_base(self):
        return image_url_base

csv_input_path = Tool.File.path_add_site(r'fwq/variable.csv')
csv_output_path = Tool.File.path_add_site(r'res/picture.csv')

if __name__ == "__main__":
    CdnImageStep(Tool,input_path=csv_input_path,output_path=csv_output_path).run()
