from config import Tool
from _ljp.mb.target import Step6Variable

# Parent-row field policy.
merge_fields = ["Images", "Attribute 1 value(s)", "Attribute 2 value(s)"]
description_fields = ["Description"]

input_file = Tool.File.path_add_site('res/quchong.csv')
output_file = Tool.File.path_add_site('fwq/variable.csv')




if __name__ == "__main__":
    Step6Variable(Tool, merge_fields=merge_fields, description_fields=description_fields).run()
