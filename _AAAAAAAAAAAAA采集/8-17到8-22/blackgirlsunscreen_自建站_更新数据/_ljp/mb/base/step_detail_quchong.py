"""详情 URL 去重模板

通用流程：读取 {分类: [url,...]} 结构 -> 全局去重（保持顺序）-> 输出 list JSON
适用于需要将分步抓取的详情链接压平去重的场景（如 Shopify 站点）。
"""


class Detail_QuChong:
    """详情 URL 去重基类"""

    def __init__(self, tool, file_path, save_path):
        self.tool = tool
        self.Tool = tool
        self.file_path = file_path
        self.save_path = save_path

    def run(self):
        data = self.tool.File.load_json(self.file_path)

        all_urls = []
        seen = set()
        for url_list in data.values():
            for url in url_list:
                if url not in seen:
                    all_urls.append(url)
                    seen.add(url)

        self.tool.File.save_json(all_urls, self.save_path)
        self.Tool.print(
            f"去重完成：原始 {sum(len(v) for v in data.values())} 条 -> "
            f"去重后 {len(all_urls)} 条，保存至 {self.save_path}",
            color='green',
        )
        return all_urls
