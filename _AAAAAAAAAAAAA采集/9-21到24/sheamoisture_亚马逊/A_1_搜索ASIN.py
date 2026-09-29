from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from _ljp.mb.amazon.step1 import YMXStep1 as Ys
from config import Tool


keyword = ''
output_path = Tool.File.path_add_site('data/1.json')
all_num = 6


class YMXStep1(Ys):

    def get_url(self, page_num, search_keyword):
        url = ""
        parsed = urlparse(url)

        # 构建基础链接（scheme + netloc + path）
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # 解析查询参数
        params_dict = parse_qs(parsed.query)

        params_dict['page'][-1] = str(page_num)
        params_dict['ref'][-1] = f'sr_pg_{page_num}'

        # 将参数字典重新编码为查询字符串
        #    doseq=True 保证每个参数只出现一次（而非列表形式）
        new_query = urlencode(params_dict, doseq=True)

        # 用 urlunparse 重新构造 URL
        new_url = urlunparse((
            parsed.scheme,  # 协议
            parsed.netloc,  # 域名
            parsed.path,  # 路径
            parsed.params,  # 参数（通常为空）
            new_query,  # 新的查询字符串
            parsed.fragment  # 锚点
        ))

        print(new_url)

        return new_url

if __name__ == "__main__":
    YMXStep1(search_keyword=keyword,output_path=output_path,all_num=all_num).run()
