from config import Tool
from _ljp.mb.base import Variable

# Parent-row field policy.
merge_fields = ["Images", "Attribute 1 value(s)", "Attribute 2 value(s)"]
description_fields = ["Description"]

if __name__ == "__main__":
    Variable(Tool, merge_fields=merge_fields, description_fields=description_fields).run()
