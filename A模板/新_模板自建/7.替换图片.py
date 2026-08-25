from config import Tool

csv_input_path = Tool.File.path_add_site(r'fwq/variable.csv')
csv_output_path = Tool.File.path_add_site(r'res/picture.csv')

from _ljp.mb.zj import Step7



class Pc(Step7):


    def build_new_url_base(self):
        web_name = self.Tool.site + "_ljp"
        return f"https://cdn.zhimatrix.com/{web_name}/images/"





if __name__ == '__main__':
    Pc(tool=Tool,input_path=csv_input_path,output_path=csv_output_path).run()

    # wb = Tool.File.Web(csv_output_path)
    # df = wb.run()
    #
    # Tool.File.save_csv(data=df, path='fail/失败图片链接.csv')


