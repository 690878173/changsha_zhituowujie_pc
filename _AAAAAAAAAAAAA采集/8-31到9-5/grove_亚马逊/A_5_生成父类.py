from config import Tool
from _ljp.mb.base import Variable

merge_fields = ["Images", "Attribute 1 value(s)", "Attribute 2 value(s)"]
description_fields = ["Description"]

input_file = Tool.File.path_add_site("res/quchong.csv")

output_file = Tool.File.path_add_site("fwq/variable.csv")


if __name__ == "__main__":
    Variable(Tool, merge_fields=merge_fields,
             description_fields=description_fields,
             output_file=output_file,
             input_file=input_file
             ).run()
