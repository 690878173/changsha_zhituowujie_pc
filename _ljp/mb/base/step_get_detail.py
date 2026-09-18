import copy

from _ljp.mb.model import Base, PageModel


class GetDetail(Base):
    """分类详情 URL 分页抓取基类"""

    skip_in_url_ls = ['gift-card','giftcard','gift_card']

    def __init__(self, tool,
                 input_path,
                 output_path,
                 catch_path,
                 index_path,
                 skip_input_url_ls=None,
                 skip_output_url_ls=None,
                 ts_num=None,
                 flush=False,
                 catch_save_num = None,
                 retry_failed_pages=True,
                 ):
        self.tool = tool
        self.Tool = tool
        self.input_path = input_path
        self.save_path = output_path
        self.catch_path = catch_path
        self.index_path = index_path
        self.skip_input_url_ls = skip_input_url_ls or []
        self.skip_output_url_ls = skip_output_url_ls or []
        self.ts_num = ts_num
        self.flush = flush
        self.catch_save_num = catch_save_num or 10
        self.retry_failed_pages = bool(retry_failed_pages)
        # A failed page is deliberately absent from the normal cache. Keep its
        # live pagination state here so it can be resumed once after the first
        # pass without restarting successfully cached pages.
        self.failed_pages = {}
        self._initial_failed_page_keys = set()
        self._recovered_failed_page_keys = set()
        self._init()

    # ================= 缓存管理（基于 BaseCatch 模型） =================

    def _init(self):
        super()._init()

        self.total_category = len(self.input_data)

    def save_catch(self):
        self.index.save()
        self.catch.save()

    # ================= 专有逻辑（子类实现） =================

    def fetch_page(self, P:PageModel, params) ->tuple[list[str],str|None]:
        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空或等于当前 url 表示停止翻页
        """
        raise NotImplementedError

    def build_params(self, p:PageModel):
        """构造参与缓存哈希的请求参数；默认仅包含页码"""
        return None

    def before_request(self, p: PageModel):
        p.extra['before_request'] = None


    def after_one_request(self, p:PageModel):
        pass

    @staticmethod
    def _failed_page_key(name, pagemodel):
        return name, pagemodel.url

    @staticmethod
    def _clone_pagemodel(pagemodel):
        return PageModel(
            url=pagemodel.url,
            next_url=pagemodel.next_url,
            page=pagemodel.page,
            is_next=pagemodel.is_next,
            extra=copy.deepcopy(pagemodel.extra),
            status=pagemodel.status,
        )

    def _record_failed_page(self, name, category_idx, pagemodel, retry):
        key = self._failed_page_key(name, pagemodel)
        self.failed_pages[key] = {
            'name': name,
            'category_idx': category_idx,
            'pagemodel': self._clone_pagemodel(pagemodel),
        }
        if not retry:
            self._initial_failed_page_keys.add(key)

    def _clear_failed_page(self, name, pagemodel):
        key = self._failed_page_key(name, pagemodel)
        if key in self.failed_pages:
            self.failed_pages.pop(key, None)
            if key in self._initial_failed_page_keys:
                self._recovered_failed_page_keys.add(key)

    # ================= 通用流程（无需修改） =================

    def get_detail_url(self, pagemodel: PageModel):
        """处理单页，含缓存命中。

        返回 (index_id, is_next, from_cache, product_count)

        子类可在 fetch_page 内设置 page.status 标记本页状态：
            'end'  - 确认已到头/无数据（含无效地址），写入缓存，下次直接跳过
            'fail' - 请求失败（临时性），不写缓存，下次重新请求
            不设置 - 按正常结果处理
        """
        params = self.build_params(pagemodel)
        index_id = self.get_index_id(url=pagemodel.url, params=params)
        catch = self.index.check(pagemodel.url, index_id)

        # 命中缓存：确认到头，或缓存内有数据
        if catch:
            catch_data = catch.get('data')
            if catch.get('end'):
                pagemodel.next_url = None
                pagemodel.is_next = False
                return index_id, False, True, len(catch_data or [])
            if catch_data:
                pagemodel.next_url = catch.get('next_url')
                pagemodel.is_next = bool(pagemodel.next_url)
                return index_id, pagemodel.is_next, True, len(catch_data)

        # 未命中缓存（或缓存数据为空），重新请求
        pagemodel.status = None  # 重置状态，避免上一页标记污染
        product_urls, next_link = self.fetch_page(pagemodel, params)

        pagemodel.is_next = bool(next_link)
        pagemodel.next_url = next_link if pagemodel.is_next else None

        # 失败不写缓存，下次重试
        if pagemodel.is_fail():
            return index_id, False, False, 0
        # Keep the source page order while removing duplicate detail URLs.
        product_urls = list(dict.fromkeys(product_urls or []))
        ls = []
        for i in product_urls:
            for j in self.skip_in_url_ls:
                if j in i:
                    break
            else:
                continue

            ls.append(i)

        if len(product_urls) == 0:
            self.Tool.print(f'url数量为0,{pagemodel.url}', color='yellow')
        self.index.append(index_id, pagemodel.url, {
            'data': product_urls,
            'next_url': pagemodel.next_url,
            'end': pagemodel.is_end(),
        })
        return index_id, pagemodel.is_next, False, len(product_urls or [])

    def get_all_detail_url(self, url, name, category_idx, pagemodel=None, retry=False):
        _num = 0
        if pagemodel is None:
            pagemodel = PageModel(url=url, next_url=url, page=_num + 1)
            self.before_request(pagemodel)
        phase = '补抓' if retry else '首轮'
        self.Tool.print(f'[{phase}分类] 正在请求:  {name} ',color='cyan')
        while True:
            # A retry resumes a PageModel that was previously marked failed.
            # Clear that marker before a potential cache hit or fresh request.
            pagemodel.status = None
            index_id, is_next, from_cache, count = self.get_detail_url(pagemodel)


            if from_cache:
                self.Tool.print(
                    f"【分类 {category_idx}/{self.total_category} | {name}】"
                    f"第 {pagemodel.page} 页命中缓存，商品 {count} 条：{pagemodel.url}",
                    color='green',
                )
            elif pagemodel.is_fail():
                self._record_failed_page(name, category_idx, pagemodel, retry)
                self.Tool.print(
                    f"【分类 {category_idx}/{self.total_category} | {name}】"
                    f"第 {pagemodel.page} 页抓取失败，"
                    f"{'本轮补抓后仍失败' if retry else '将在首轮结束后补抓一次'}",
                    color='yellow',
                )
                break
            else:
                self._clear_failed_page(name, pagemodel)
                self.Tool.print(
                    f"【分类 {category_idx}/{self.total_category} | {name}】"
                    f"第 {pagemodel.page} 页抓取成功，商品 {count} 条：{pagemodel.url}",
                    color='green',
                )

                _num += 1

            # dict 天然去重，重复 append 仅覆盖
            self.catch.append(name, index_id, pagemodel.url)

            if not is_next:
                self.Tool.print(
                    f"  分类「{name}」已无下一页，共处理 {pagemodel.page} 页，结束。",
                    color='cyan',
                )
                break


            pagemodel.page += 1

            if pagemodel.page > 20:
                self.Tool.print(f'  页数超过 20（当前 {pagemodel.page}），仅警告继续运行。', color='yellow')

            if _num % self.catch_save_num == 0:
                self.save_catch()
            current_url = pagemodel.url
            self.after_one_request(pagemodel)
            # The default transition follows the parsed pagination link.  A
            # site hook can still replace ``page.url`` for exceptional flows.
            if pagemodel.url == current_url and pagemodel.next_url:
                pagemodel.url = pagemodel.next_url
        self.save_catch()


    def _before_get_all_detail_url(self,url,name, category_idx):
        # 预留的请求预处理，子类可覆盖实现特定实现,默认原样返回】】

        return url,name,category_idx


    def output_res(self):
        # 扁平化 index：index_id -> data 列表，解决分页数据按 next_url 存储导致汇总丢失的问题
        global_data = {}
        for pages in self.index.data.values():
            if not isinstance(pages, dict):
                continue
            for index_id, item in pages.items():
                if isinstance(item, dict):
                    global_data[index_id] = item.get('data', [])

        res_dic = {}
        for name, seq_dict in self.catch.data.items():
            ls = []
            for seq_id in seq_dict:
                ls.extend(global_data.get(seq_id, []))
            ls = list(dict.fromkeys(ls))
            ls = [u for u in ls if u not in self.skip_output_url_ls]
            res_dic[name] = ls
            self.Tool.print(f"  分类「{name}」：汇总到 {len(ls)} 条商品链接。", color='cyan')

        self.Tool.File.save_json(res_dic, self.save_path)

        return res_dic

    def run(self):
        self.Tool.print(f"开始处理，共 {self.total_category} 个分类。", color='cyan')

        category_idx = 0
        for name, urls in self.input_data.items():
            category_idx += 1
            if isinstance(urls,str):
                urls = [urls]

            for url in urls:
                if url in self.skip_input_url_ls:
                    self.Tool.print(
                        f'【{category_idx}/{self.total_category}】跳过分类：{name}，目标 url 在排除名单中',
                        color='yellow',
                    )
                    continue

                if isinstance(self.ts_num, int) and (category_idx - 1) >= self.ts_num:
                    self.Tool.print(f"已达到测试条数限制 {self.ts_num}，任务结束。", color='yellow')
                    break
                url,name,category_idx = self._before_get_all_detail_url(url, name, category_idx)
                self.get_all_detail_url(url, name, category_idx)

        if self.failed_pages and self.retry_failed_pages:
            retry_pages = list(self.failed_pages.values())
            self.Tool.print(
                f"首轮分类页失败 {len(retry_pages)} 页，开始集中补抓一次。",
                color='yellow',
            )
            for item in retry_pages:
                page = self._clone_pagemodel(item['pagemodel'])
                self.get_all_detail_url(
                    page.url,
                    item['name'],
                    item['category_idx'],
                    pagemodel=page,
                    retry=True,
                )

        self.Tool.print(
            "分类页失败统计："
            f"首轮失败 {len(self._initial_failed_page_keys)} 页，"
            f"补抓恢复 {len(self._recovered_failed_page_keys)} 页，"
            f"最终失败 {len(self.failed_pages)} 页。",
            color='yellow' if self.failed_pages else 'green',
        )
        if self.failed_pages:
            for item in self.failed_pages.values():
                page = item['pagemodel']
                self.Tool.print(
                    f"  最终失败：分类「{item['name']}」第 {page.page} 页 {page.url}",
                    color='yellow',
                )

        self.Tool.print("所有分类抓取完成，开始汇总输出最终详情链接……", color='green')

        res_dic = self.output_res()
        total = sum(len(v) for v in res_dic.values())
        self.Tool.print(
            f"任务全部完成！汇总详情 URL 总数：{total}，结果保存至 {self.save_path}",
            color='green',
        )
        self.close()
        return res_dic


    def close(self):
        self.Tool.print(f'执行关闭方法', color='cyan')

        self.close_playwright()
