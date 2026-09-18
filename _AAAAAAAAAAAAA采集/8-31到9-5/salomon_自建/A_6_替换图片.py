from urllib.parse import unquote

from config import Tool

csv_input_path = Tool.File.path_add_site(r'fwq/variable.csv')
csv_output_path = Tool.File.path_add_site(r'res/picture.csv')

from _ljp.mb.zj import Replace_imgs



class Pc(Replace_imgs):

    @staticmethod
    def hash_image_url(image_url):
        decoded_url = unquote(image_url)
        clean_name = decoded_url

        for char in [".", "?", "&", "#", "$", "=", ",", ":", " ", "%", '/']:
            clean_name = clean_name.replace(char, "_")

        return clean_name.strip('_') + '.webp'


    def build_new_url_base(self):
        web_name = self.Tool.site + "_ljp"
        return f"https://cdn.zhimatrix.com/{web_name}/images/"



if __name__ == '__main__':
    Pc(tool=Tool,input_path=csv_input_path,output_path=csv_output_path).run()

    wb = Tool.File.Web(csv_output_path)
    wb.run('fail/失败图片链接.csv')



