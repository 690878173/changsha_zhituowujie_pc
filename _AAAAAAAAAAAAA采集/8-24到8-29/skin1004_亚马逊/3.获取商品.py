
from _ljp.mb.amazon.step3 import Step3

input_file = 'data/2.json'

output_file = 'res/res.csv'

fail_file = 'fail/fail.csv'

img_split = ','
if __name__ == "__main__":
    Step3(input_file=input_file,output_file=output_file,fail_file=fail_file,img_split=img_split).run()
