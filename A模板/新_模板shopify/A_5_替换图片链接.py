from config import Tool

csv_input_path = Tool.File.path_add_site(r'fwq/quchong.csv')
csv_output_path = Tool.File.path_add_site(r'res/picture.csv')


web_name = Tool.site + '_shopify_ljp'
new_url_base = f'https://cdn.zhimatrix.com/{web_name}/images/'

from _ljp.mb.zj import Replace_imgs


class Pc(Replace_imgs):

    def build_new_url_base(self):
        return new_url_base





if __name__ == '__main__':
    pc = Pc(Tool,input_path=csv_input_path,output_path=csv_output_path)
    pc.run()
    # wb = Tool.File.Web(csv_output_path)
    # df = wb.run()
    #
    # Tool.File.save_csv(data=df, path='fail/失败图片链接.csv')

