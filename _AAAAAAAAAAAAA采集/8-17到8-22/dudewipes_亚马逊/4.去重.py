from config import Tool
from _ljp.mb.amazon import Quchong


input_file = 'data/result.csv'

if __name__ == "__main__":
    Quchong(Tool,input_file=input_file).run()
