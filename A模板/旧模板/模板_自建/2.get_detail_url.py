import hashlib
import json

from config import Tool

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2/data.json')

index_path = Tool.File.path_add_site('hc/2/index.json')

# 测试数据条数,以初始url数量计数
ts_num = None

# 排除某些 URL（输入分类黑名单）
input_url_no_ls = []
# 输出商品链接黑名单
output_url_no_ls = []

# 覆盖缓存：True=无视本地缓存强制重新请求
flush = False


from playwright.sync_api import sync_playwright
from fingerprint_toolkit import FingerprintKit
edge = sync_playwright().start()
browser = edge.chromium.launch(headless=False)
context = browser.new_context()

fpk = FingerprintKit()
e_page = context.new_page()
fpk.inject(e_page)


class Sc(object):
    def __init__(self):
        self.catch_data = Tool.File.load_json(catch_path)
        self.input_data = Tool.File.load_json(file_path)
        self.index_data = Tool.File.load_json(index_path)
        self.total_category = len(self.input_data)

    def get_index_id(self, url, params: dict) -> str:
        """生成单页唯一缓存key，url+请求参数哈希"""
        raw = json.dumps(
            {"url": url, "params": params},
            sort_keys=True,
            ensure_ascii=False
        ).encode("utf-8")
        return hashlib.md5(raw).hexdigest()

    def get_all_detail_url(self, url, name, category_idx):
        """单个分类分页循环入口
        循环逻辑：依靠get_detail_url返回的is_next判断是否继续翻页
        """
        _num = 0
        par = {'_raw_url': url, 'page': _num}
        current_page_url = url
        while True:
            Tool.print(f"【分类 {category_idx}/{self.total_category} | {name}】正在处理第 {_num + 1} 页: {current_page_url}")
            index_id, is_next = self.get_detail_url(current_page_url, par=par)

            # 记录本页缓存索引，避免重复执行
            id_list = self.catch_data.setdefault(name, [])
            if index_id not in id_list:
                id_list.append(index_id)
            else:
                Tool.print(f'分类:{name}，分页索引已存在，跳过', color='green')

            # 下游业务层控制is_next；模板不干涉链接相等判断
            if not is_next:
                break

            try:
                current_page_url = par['next_url']
            except KeyError:
                Tool.print(f'par未设置next_url，终止当前分类翻页', color="yellow")
                break

            _num += 1
            par['page'] += 1

            # 页数上限告警（仅提醒，不强制终止）
            if _num > 20:
                Tool.print(f'页数超过20,当前{_num},仅警告继续运行', color='yellow')

            # 每10页落地一次缓存文件
            if _num % 10 == 0:
                Tool.File.save_json(self.index_data, index_path)
                Tool.File.save_json(self.catch_data, catch_path)

        # 当前分类抓取结束，持久化缓存
        Tool.File.save_json(self.index_data, index_path)
        Tool.File.save_json(self.catch_data, catch_path)

    @Tool.zs(f'重写逻辑获取数据')
    def get_detail_url(self, url, par: dict):
        """
        【模板标准接口，请勿修改外层逻辑】
        ↓↓↓ 仅在【下游业务实现区域】编写网站抓取代码 ↓↓↓
        下游开发约定：
        1. product_urls：当前页面商品链接列表
        2. next_link：下一页完整链接；
        3. 业务自行判断：next_link == 当前url / 为空 / 重复链接 → 设置 is_next=False
        4. 若存在合法下一页：is_next=True，并给 par['next_url'] = next_link
        """
        is_next = False
        par['next_url'] = None
        raw_url = par['_raw_url']

        page = par['page']

        page = str(int(page)+1)

        # 可以在这里追加接口请求参数，参与缓存hash计算
        params = {
            'page':page
        }

        url = raw_url + f'?page={page}'

        index_id = self.get_index_id(raw_url, params=params)
        _catch = self.index_data.get(raw_url, {}).get(index_id)

        # 缓存命中分支
        if not flush and _catch:
            cached_next_url = _catch.get('next_url')
            cached_has_next = bool(cached_next_url)
            par['next_url'] = cached_next_url
            return index_id, cached_has_next






        e_page.goto(url)


        product_urls = []
        next_link = ""

        if next_link and next_link != url:
            is_next = True
            par['next_url'] = next_link
        # ========== 【下游业务实现区域 END】 ==========

        # 写入缓存，永久保存当前页结果
        self.index_data.setdefault(raw_url, {})[index_id] = {
            'data': product_urls,
            'next_url': par['next_url']
        }
        return index_id, is_next

    def run(self):
        category_idx = 0
        for name, url in self.input_data.items():
            category_idx += 1
            if url in input_url_no_ls:
                Tool.print(f'【{category_idx}/{self.total_category}】跳过分类：{name}，目标url排除', color='yellow')
                continue

            print(f"\n====== 【{category_idx}/{self.total_category}】正在处理分类：{name} ======")
            print(f"分类首页URL: {url.strip()}")

            # 测试条数限制
            if isinstance(ts_num, int) and (category_idx - 1) >= ts_num:
                print(f"已达到测试条数限制 {ts_num}，任务结束")
                break

            self.get_all_detail_url(url, name, category_idx)

        Tool.print("\n所有分类抓取完成，开始汇总输出最终详情链接……", color='green')
        res_dic = {}
        for name, index_ls in self.catch_data.items():
            ls = []
            base_raw_key = self.input_data[name]
            for index in index_ls:
                cache_item = self.index_data.get(base_raw_key, {}).get(index, {})
                page_url_list = cache_item.get("data", [])
                ls.extend(page_url_list)
            # 全局商品链接去重
            ls = list(dict.fromkeys(ls))
            # 最终输出再次过滤黑名单
            ls = [u for u in ls if u not in output_url_no_ls]
            res_dic[name] = ls

        Tool.File.save_json(res_dic, save_path)
        total = sum(len(v) for v in res_dic.values())
        Tool.print(f"\n✅ 任务全部完成！汇总详情URL总数：{total}，结果保存至 {save_path}", color='green')


if __name__ == '__main__':
    Sc().run()
