import hashlib
import json

from lxml import etree

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

cookies = {
    '__apex_test__': '',
    '__apex_test__': '',
    'dwac_505af6cc998cc5f9f827821855': 'edlBIFDWjGPOcg9XsM8_3Wk_X6Rh50pANLw%3D|dw-only|||USD|false|US%2FPacific|true',
    'cqcid': 'abVj6lxZLAIIeMuMmYX4AupE66',
    'cquid': '||',
    'dwanonymous_adb6f0c0bea1959b44ade4a112139272': 'abVj6lxZLAIIeMuMmYX4AupE66',
    'sid': 'edlBIFDWjGPOcg9XsM8_3Wk_X6Rh50pANLw',
    'dwsid': 'TUSlS7q70NXU6R_bVqECQl2iu8-Lihb2Licw0Z0i2garABVWc1eKVpjebLBrBc9jGbOIMzRrgM6u--BpN91jdQ==',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    'osano_consentmanager_uuid': 'e7a32569-6385-42ff-9cf7-1db238e0452d',
    'osano_consentmanager': 'KgmRt9QJJhI3LEFdcokYh3o-gfsobvE5T4wfld-JvIS63aU5YmtNG8cjhLfiQtpM-xs8JiTiEriN-KU29WgreitZzeKuD19X08zzeEQJOHZfssmusSjd-o4UBmX7xkQVxKMde_PGyM6zw1jnTNaIIvAJWNQ0_cBs0lkBRnSFPbDhOSXMCEplumFLmTxKbppgQDQ6eFZJ4vxbMLCZYQrDyKslPhk-oOA-ozT07wnxKV6sMGVLSDnSbDmxI82cOIOH_giz-7MZR18hRuUy7NygMMOEbhmhCGH3-sBGBu_-xFYlvdECA3Bwbs5tOY0sPTlDO7YqgNAR6uo=',
    '__apex_test__': '',
    'locale_pref': 'en_US',
    '__attn_eat_id': '4e8a3969778646918dd8615afbfcabd5',
    '__attentive_id': '237f6bc864214bf28f213b809092a977',
    '__attentive_session_id': '35ce2ff326ee4af9a8bea129373a9df2',
    '__attentive_cco': '1786763462598',
    '_attn_bopd_': 'browser',
    '__attentive_dv': '1',
    '__attentive_ss_referrer': 'https://www.hoka.com/',
    'pixlee_analytics_cookie': '%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2237c5ae71-19f0-1f76-8a45-646edc14eecf%22%7D',
    'pixlee_analytics_cookie_legacy': '%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2237c5ae71-19f0-1f76-8a45-646edc14eecf%22%7D',
    'yotpo_pixel': '3897cbee-3ac8-4815-9ef2-08c59dd7ee10',
    '_sp_ses.1f99': '*',
    'tfExperimentId': 't-9519872adb1046528acf84034a2c0ea6',
    'tf-version': 'v1',
    'visitCount': '6',
    '_attn_': 'eyJ1Ijoie1wiY29cIjoxNzg2NzYzNDYyNTkxLFwidW9cIjoxNzg2NzYzNDYyNTkxLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjIzN2Y2YmM4NjQyMTRiZjI4ZjIxM2I4MDkwOTJhOTc3XCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg2NzYzNDk3OTc0LFwidW9cIjoxNzg2NzYzNDk3OTc0LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL25iaWF2Lmhva2EuY29tXCJ9In0=',
    '_sp_id.1f99': 'fbec3ac5cf8faf9d.1786763475.1.1786763498.1786763475',
    '__attentive_pv': '5',
    'forterToken': 'b453ed77463b42848e4c1ff207f2ca2a_1786763496777__UDF43-m4_23ck_',
    'datadome': 'IEAsnmHgQvMCPvElY4k_G9cgG_Pg6LJ6Fg_8yZOFuN72fn2FnOv7aSxJEHf0ymwlalCsOrZdQJn1vI1bDZldfp1YG09EKBMcY2M2F3zuPoM6JVRty3WzizDKTuOudEOw',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.hoka.com/en/us/new-arrivals/',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    # 'cookie': '__apex_test__=; __apex_test__=; dwac_505af6cc998cc5f9f827821855=edlBIFDWjGPOcg9XsM8_3Wk_X6Rh50pANLw%3D|dw-only|||USD|false|US%2FPacific|true; cqcid=abVj6lxZLAIIeMuMmYX4AupE66; cquid=||; dwanonymous_adb6f0c0bea1959b44ade4a112139272=abVj6lxZLAIIeMuMmYX4AupE66; sid=edlBIFDWjGPOcg9XsM8_3Wk_X6Rh50pANLw; dwsid=TUSlS7q70NXU6R_bVqECQl2iu8-Lihb2Licw0Z0i2garABVWc1eKVpjebLBrBc9jGbOIMzRrgM6u--BpN91jdQ==; __cq_dnt=0; dw_dnt=0; osano_consentmanager_uuid=e7a32569-6385-42ff-9cf7-1db238e0452d; osano_consentmanager=KgmRt9QJJhI3LEFdcokYh3o-gfsobvE5T4wfld-JvIS63aU5YmtNG8cjhLfiQtpM-xs8JiTiEriN-KU29WgreitZzeKuD19X08zzeEQJOHZfssmusSjd-o4UBmX7xkQVxKMde_PGyM6zw1jnTNaIIvAJWNQ0_cBs0lkBRnSFPbDhOSXMCEplumFLmTxKbppgQDQ6eFZJ4vxbMLCZYQrDyKslPhk-oOA-ozT07wnxKV6sMGVLSDnSbDmxI82cOIOH_giz-7MZR18hRuUy7NygMMOEbhmhCGH3-sBGBu_-xFYlvdECA3Bwbs5tOY0sPTlDO7YqgNAR6uo=; __apex_test__=; locale_pref=en_US; __attn_eat_id=4e8a3969778646918dd8615afbfcabd5; __attentive_id=237f6bc864214bf28f213b809092a977; __attentive_session_id=35ce2ff326ee4af9a8bea129373a9df2; __attentive_cco=1786763462598; _attn_bopd_=browser; __attentive_dv=1; __attentive_ss_referrer=https://www.hoka.com/; pixlee_analytics_cookie=%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2237c5ae71-19f0-1f76-8a45-646edc14eecf%22%7D; pixlee_analytics_cookie_legacy=%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2237c5ae71-19f0-1f76-8a45-646edc14eecf%22%7D; yotpo_pixel=3897cbee-3ac8-4815-9ef2-08c59dd7ee10; _sp_ses.1f99=*; tfExperimentId=t-9519872adb1046528acf84034a2c0ea6; tf-version=v1; visitCount=6; _attn_=eyJ1Ijoie1wiY29cIjoxNzg2NzYzNDYyNTkxLFwidW9cIjoxNzg2NzYzNDYyNTkxLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjIzN2Y2YmM4NjQyMTRiZjI4ZjIxM2I4MDkwOTJhOTc3XCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg2NzYzNDk3OTc0LFwidW9cIjoxNzg2NzYzNDk3OTc0LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL25iaWF2Lmhva2EuY29tXCJ9In0=; _sp_id.1f99=fbec3ac5cf8faf9d.1786763475.1.1786763498.1786763475; __attentive_pv=5; forterToken=b453ed77463b42848e4c1ff207f2ca2a_1786763496777__UDF43-m4_23ck_; datadome=IEAsnmHgQvMCPvElY4k_G9cgG_Pg6LJ6Fg_8yZOFuN72fn2FnOv7aSxJEHf0ymwlalCsOrZdQJn1vI1bDZldfp1YG09EKBMcY2M2F3zuPoM6JVRty3WzizDKTuOudEOw',
}


class Sc(object):
    def __init__(self):
        self.catch_data = Tool.File.load_json(catch_path)
        self.input_data = Tool.File.load_json(file_path)
        self.index_data = Tool.File.load_json(index_path)
        self.total_category = len(self.input_data)
        self._init()


    def _init(self):
        if flush:
            self.catch_data = {}
            self.index_data = {}

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

        total_ls = self.catch_data[name]
        total = 0
        for item in total_ls:
            total += len(self.index_data[url][item]['data'])
        Tool.print(f'当前分类 {category_idx}/{self.total_category} | {name} 抓取完毕，共{total}个')

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

        # 可以在这里追加接口请求参数，参与缓存hash计算
        params = {
            'sz':222
        }

        index_id = self.get_index_id(raw_url, params=params)
        _catch = self.index_data.get(raw_url, {}).get(index_id)

        # 缓存命中分支
        if not flush and _catch:
            cached_next_url = _catch.get('next_url')
            cached_has_next = bool(cached_next_url)
            par['next_url'] = cached_next_url
            return index_id, cached_has_next

        # ========== 【下游业务实现区域 START】==========
        """
        # 示例代码，下游自行替换
        # res = Tool.get(url)
        # html = etree.HTML(res.text)
        raw_links = html.xpath('//a/@href')
        # 商品链接清洗 + 过滤output_url_no_ls
        product_urls = [link for link in raw_links if link not in output_url_no_ls]
        # 获取下一页链接
        next_link = html.xpath('//a[text()="Next"]/@href')
        next_link = next_link[0].strip() if next_link else ""

        # 【重要！下游自行控制判重逻辑】
        # 场景：下一页链接和当前页面一致、空链接、无效链接 → 禁止翻页
        if next_link and next_link != url:
            is_next = True
            par['next_url'] = next_link
        """

        res = Tool.get(url,headers=headers,cookies=cookies,params=params)

        html = etree.HTML(res.text)
        Tool.HTML.save(res.text)
        products = html.xpath('.//div[@itemid="#product"]/div')

        no_ls = ['https://www.hoka.com/en/us/login/','/en/us/membership/','/en/us/clifton/','https://www.hoka.com/en/us/account/',
                 '/en/us/transport/','/en/us/members-only/','/en/us/back-to-school/',"/en/us/fly-human-fly/",'/en/us/fly-human-fly/',
                 'https://www.hoka.com/en/us/hoka-shoe-finder.html','/en/us/trail-running-guide/','/en/us/kids/',
                 '/en/us/big-kids-shoes/','/en/us/little-kids-shoes/','/en/us/discount-programs/','/en/us/best-sellers/',
                 '/en/us/road-running-guide/']
        ls = []
        for product in products:
            # fl = product.xpath('.//div[@class="image-container null "]/a/@href')
            # print(fl)


            kl = product.xpath('.//a/@href')
            kl = list(set(kl))
            kl = [i for i in kl if i not in no_ls]


            for i in kl:
                if '.html' not in i:
                    print(i)
                    continue
                ls.append(i)





            # ls.extend(kl)

        ls = [Tool.URL.add_site(i) for i in ls]

        product_urls = ls
        next_link = None

        # 下游在这里实现请求、解析、赋值 product_urls、next_link
        # 下游自行控制：next_link == url 时不要开启is_next
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
