import pandas as pd
from typing import Optional


def transform_images_by_rule(csv_path: str,
                             output_path: Optional[str] = None,
                             target_prefix: str = "https://cdn.zhimatrix.com/choczero_ljp/images/"):
    """
    读取 csv_path 的 Images 列，按新版下载器规则转换每个图片 URL：
      统一将后缀及特殊字符转化为下划线，并强制以 .webp 结尾，以匹配下载后的实体图片。

    :param csv_path: 输入 CSV 路径（必须含 Images 列）
    :param output_path: 输出路径；若 None 则覆盖输入文件
    :param target_prefix: 目标 URL 前缀
    """
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    if "Images" not in df.columns:
        raise KeyError("CSV 中缺少 'Images' 列")

    def convert_cell(cell: str) -> str:
        if pd.isna(cell):
            return cell
        # 兼容逗号加空格或纯逗号的分隔情况
        parts = [p.strip() for p in str(cell).split(",") if p.strip()]
        new_parts = []
        for p in parts:
            # 若已是目标前缀则跳过（避免重复转换）
            if p.startswith(target_prefix):
                new_parts.append(p)
                continue

            # 1. 取 URL 最后一段（包含文件名、可能存在的特殊后缀或查询参数）
            last = p.split("/")[-1]

            # 2. 同步下载器的 sanitize_filename 规则：
            # 将所有可能干扰路径的特殊字符（包括点号）全部替换为下划线
            for char in [".", "?", "&", "#", "$", "=", ",", ":", " "]:
                last = last.replace(char, "_")

            # 3. 去除首尾可能因替换产生的多余下划线，并统一加上 .webp
            transformed = last.strip('_') + ".webp"

            # 4. 拼接新的云端/本地映射前缀
            new_url = target_prefix + transformed
            new_parts.append(new_url)

        return ", ".join(new_parts)

    df["Images"] = df["Images"].apply(convert_cell)

    if output_path is None:
        output_path = csv_path
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 转换完成，结果已保存到: {output_path}")


# 示例用法
if __name__ == "__main__":
    transform_images_by_rule(
        csv_path=r"J:\changsha\choczero\data\choczero_quchong.csv",  # 改为你的文件路径
        output_path=r"J:\changsha\choczero\data\choczero_picture.csv",  # 可选：不填则覆盖输入
        target_prefix="https://cdn.zhimatrix.com/choczero_ljp/images/"  # 可改为你想要的前缀
    )