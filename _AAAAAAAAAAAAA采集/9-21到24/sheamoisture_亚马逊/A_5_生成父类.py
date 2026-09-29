from config import Tool
from _ljp.mb.base import Variable

merge_fields = ["Images", "Attribute 1 value(s)", "Attribute 2 value(s)"]
description_fields = ["Description",
                      'important_information(product.metafields.c_f.important_information)',
                      'productDescription(product.metafields.c_f.productdescription)',
                      'Product_details(product.metafields.c_f.product_details)',
                      'About_this_item(product.metafields.c_f.about_this_item)',
                      ]

input_file = Tool.File.path_add_site("res/quchong.csv")

output_file = Tool.File.path_add_site("fwq/variable.csv")


if __name__ == "__main__":
    Variable(Tool, merge_fields=merge_fields,
             description_fields=description_fields,
             output_file=output_file,
             input_file=input_file
             ).run()
