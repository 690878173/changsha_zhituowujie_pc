from config import Tool
from _ljp.mb.base import Variable


input_file = Tool.File.path_add_site("fwq/quchong.csv")
output_file = Tool.File.path_add_site("fwq/variable.csv")


if __name__ == "__main__":
    Variable(
        Tool,
        input_file=input_file,
        output_file=output_file,
        merge_fields=("Images", "Attribute 1 value(s)", "Attribute 2 value(s)"),
        description_fields=("Description",),
    ).run()
