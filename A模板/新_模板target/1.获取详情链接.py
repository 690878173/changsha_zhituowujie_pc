from _ljp.mb.target.detail import GetDetailStep
from config import Tool


keyword = ''
output_path = Tool.File.path_add_site('data/2.json')


if __name__ == '__main__':
    GetDetailStep(tool=Tool,keyword=keyword,output_path=output_path,all_num=9).run()