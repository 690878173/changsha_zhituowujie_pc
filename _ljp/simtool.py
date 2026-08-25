class SimTool:
    _C = {
        "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
        "blue": "\033[34m", "purple": "\033[35m", "cyan": "\033[36m",
        "white": "\033[37m", "black": "\033[30m", "reset": "\033[0m",
    }
    _msg = ""

    @staticmethod
    def print(msg, color="red"):
        msg = f'=====>{msg}\n'
        print(f"{SimTool._C.get(color, '')}{msg}{SimTool._C['reset']}")

    @staticmethod
    def zs(desc=""):
        """无操作步骤标记装饰器，标注"""
        def _deco(fn):
            return fn
        return _deco
