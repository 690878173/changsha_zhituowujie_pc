import pandas as pd
import hashlib
from config import Tool

csv_input_path = Tool.File.path_add_site(r'res/blackgirlsunscreen_quchong.csv')
csv_output_path = Tool.File.path_add_site(r'res/picture.csv')


web_name = Tool.site + '_ljp'
new_url_base = f'https://cdn.zhimatrix.com/{web_name}/images/'

@Tool.zs(f'哈希url')
def generate_image_filename(image_url):
    url_hash = hashlib.md5(image_url.encode("utf-8")).hexdigest()
    return f"{url_hash}.webp"

@Tool.zs(f'根据设置分隔符号，对url进行哈希后拼接前缀后.webp')
def replace_row_img_url(cell:str,target_prefix):
    if pd.isna(cell):
        return cell
    images_split = Tool.config.images_split
    if Tool.config.images_split not in str(cell) and ',http' in str(cell):
        images_split = ','

    parts = [p.strip() for p in str(cell).split(images_split) if p.strip()]
    new_parts = []
    for p in parts:
        # 若已是目标前缀则跳过（避免重复转换）
        if p.startswith(target_prefix):
            new_parts.append(p)
            continue

        url = generate_image_filename(p)
        new_url = target_prefix + url
        new_parts.append(new_url)
        print(f'原始url: {p} | 新url: {new_url}')

    return ", ".join(new_parts)

def transform_img(csv_path,output_path,target_prefix):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    if "Images" not in df.columns:
        raise KeyError("CSV 中缺少 'Images' 列")

    df["Images"] = df["Images"].apply(lambda x:replace_row_img_url(x,target_prefix=target_prefix))

    if output_path is None:
        output_path = csv_path
    Tool.File.save_csv(df,output_path)
    print(f"✅ 转换完成，结果已保存到: {output_path}")

def main():
    transform_img(csv_input_path,csv_output_path,target_prefix=new_url_base)


if __name__ == "__main__":
    main()
    for _ in range(3):
        Tool.print(f'当前使用分隔符号:{Tool.config.images_split}')