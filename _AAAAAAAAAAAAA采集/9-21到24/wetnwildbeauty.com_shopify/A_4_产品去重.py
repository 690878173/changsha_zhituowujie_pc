import pandas as pd

from config import Tool
from _ljp.mb.target import Quchong





input_file = Tool.File.path_add_site(r'res/result.csv')


# input_file = Tool.File.path_add_site(r'fwq/merged_link_variants.csv')

output_file= Tool.File.path_add_site(r'fwq/quchong.csv')

if __name__ == "__main__":
    Quchong(Tool,input_file=input_file,output_file=output_file).run()

    df = pd.read_csv(output_file)

    df = df.drop(columns=['__source_handle', '__linked_handles',
                          '__linked_options', '__linked_target_options'])
    df.to_csv(output_file,index=False)
