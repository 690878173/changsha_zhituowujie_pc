from config import Tool
from _ljp.mb.base import Replace_imgs

image_url_base = f"https://cdn.zhimatrix.com/{Tool.site}_amazon_ljp/images/"

input_path = Tool.File.path_add_site("fwq/variable.csv")

output_path = Tool.File.path_add_site("res/picture.csv")
class CdnImageStep(Replace_imgs):
    def build_new_url_base(self):
        return image_url_base


if __name__ == "__main__":
    CdnImageStep(Tool, input_path=input_path,output_path=output_path).run()

    # wb = Tool.File.Web(csv_output_path)
    # wb.run('fail/失败图片链接.csv')
