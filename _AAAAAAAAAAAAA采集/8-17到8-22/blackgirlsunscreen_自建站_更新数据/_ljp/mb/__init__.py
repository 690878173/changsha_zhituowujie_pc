"""mb 模板包：站点数据抓取/转换的 1-10 步流水线模板。

每个步骤提供通用基类（实现通用流程），专有逻辑交由子类覆写抽象方法。
"""
import importlib

from .model import PageModel