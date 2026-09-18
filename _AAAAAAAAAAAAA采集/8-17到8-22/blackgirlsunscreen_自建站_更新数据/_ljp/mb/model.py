import hashlib
import json


class PageModel:
    """分页状态对象，用于在分页循环中传递当前页与下一页信息"""

    def __init__(self, url, next_url, page, is_next=False,extra:dict|None=None, status=None):
        self.url = url
        self.next_url = next_url
        self.page = page
        self.is_next = is_next
        self.extra = extra if extra else {}
        self.status = status

    def set_fail(self):
        self.status = 'fail'

    def set_end(self):
        self.status = 'end'


    def is_fail(self):
        return self.status == 'fail'

    def is_end(self):
        return self.status == 'end'





class BaseCatch:
    def __init__(self,tool,catch_path,flush=False):
        self.Tool = tool
        self.catch_path = catch_path
        self.catch_data = self.Tool.File.load_json(self.catch_path) or {}

        if flush:
            self.catch_data = {}
        self.data: dict[str, dict] = self.catch_data

    def save(self):
        self.Tool.File.save_json(self.data, self.catch_path)


class Catch(BaseCatch):
    # id 必须根据url和params生成

    def append(self,category,seq_id,url):
        self.data.setdefault(category,{})[seq_id] = {'url':url}


    def check(self,category):
        return self.data.get(category,{}).keys()

class Index(BaseCatch):
    def append(self, seq_id, url, data):
        self.data.setdefault(url, {})[seq_id] = data

    def check(self,url,seq_id):
        return self.data.get(url, {}).get(seq_id)


class Base:
    """带磁盘缓存的步骤基类。

    约定：子类在 `__init__` 中赋值以下属性后调用 `self._init()`：
        self.Tool        -> Base_tool 实例
        self.file_path   -> 输入数据文件路径
        self.catch_path  -> 缓存数据文件路径
        self.index_path  -> 缓存索引文件路径
        self.flush       -> 是否清空缓存
    """

    def _init(self):

        self.input_data = self.Tool.File.load_json(self.input_path)
        self.catch = Catch(self.Tool, self.catch_path)
        self.index = Index(self.Tool, self.index_path)
        if self.flush:
            self.catch.data = {}
            self.index.data = {}
            self.Tool.print('flush=True，已清空缓存，将强制重新请求。', color='yellow')
        else:
            self.Tool.print(
                f'已加载缓存：分页索引 {len(self.index.data)} 组，分类进度 {len(self.catch.data)} 条。',
                color='cyan',
            )


    def get_page(self, url=None, **kwargs):
        """获取注入指纹的 Page；启用插件后可传 URL 直接导航。"""
        return self.Tool.browser.get_page(url, **kwargs)

    def close_playwright(self):
        """关闭当前线程的 Playwright 资源。"""
        self.Tool.browser.close()


    def get_index_id(self, url, category=None, params=None):
        """生成单页唯一缓存 key：url + 分类 + 请求参数哈希"""
        raw = {
            'url': url,
            'category': category,
            'par': params,
        }
        return hashlib.md5(
            json.dumps(raw, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

    def save_catch(self):
        """持久化缓存索引与数据"""
        self.catch.save()
        self.index.save()




class Browser_Tool:

    pass
