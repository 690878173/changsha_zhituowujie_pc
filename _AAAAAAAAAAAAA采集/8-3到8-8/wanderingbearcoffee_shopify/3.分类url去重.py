import json

from config import Tool

file_path = Tool.File.path_add_site('data/detail_url.json')
save_path = Tool.File.path_add_site('data/quchong_detail_url.json')


def process_urls(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        all_urls = []
        seen = set()

        for url_list in data.values():
            for url in url_list:
                # 去重并保持顺序
                if url not in seen:
                    all_urls.append(url)
                    seen.add(url)

        # 3. 将结果保存为列表格式的 JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_urls, f, ensure_ascii=False, indent=4)

        print(f"处理完成！")
        print(f"原始 URL 总数（含重复）: {sum(len(v) for v in data.values())}")
        print(f"去重后 URL 总数: {len(all_urls)}")
        print(f"结果已保存至: {output_file}")

    except FileNotFoundError:
        print(f"错误：找不到文件 {input_file}，请确保脚本与文件在同一目录。")
    except Exception as e:
        print(f"发生错误: {e}")

def main():
    process_urls(file_path, save_path)


if __name__ == "__main__":
    main()