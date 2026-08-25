import hashlib

import pandas as pd


class Step7:
    """图片 URL 哈希替换基类"""

    def __init__(self, tool, input_path, output_path):
        self.tool = tool
        self.Tool = tool
        self.input_path = input_path
        self.output_path = output_path
        self.new_url_base = self.build_new_url_base()

    # ================= 专有逻辑（子类覆写） =================

    def build_new_url_base(self):
        web_name = self.Tool.site + "_ljp"
        return f"https://cdn.zhimatrix.com/{web_name}/images/"

    def load_failed_images(self):
        """返回失败图片 url 集合；默认无过滤"""
        return set()

    # ================= 通用逻辑（无需修改） =================

    @staticmethod
    def hash_image_url(image_url):
        return f"{hashlib.md5(image_url.encode('utf-8')).hexdigest()}.webp"

    def to_new_url(self, image_urls, failed_set):
        """将单个单元格内多个 url 转为新链接，跳过失败图片"""
        if pd.isna(image_urls) or str(image_urls).strip() == "":
            return ""

        images_split = self.Tool.config.images_split
        text = str(image_urls)
        if images_split not in text and ",http" in text:
            images_split = ","

        new_urls = []
        for url in text.split(images_split):
            url = url.strip()
            if not url or url in failed_set:
                continue
            # 已是目标前缀则跳过，避免重复转换
            if url.startswith(self.new_url_base):
                new_urls.append(url)
                continue
            filename = self.hash_image_url(url).split("?")[0]

            new_url = f"{self.new_url_base}{filename}"
            new_urls.append(new_url)

            print(f'新URL: {new_url} => 原始url；{url}')

        return ",".join(new_urls)

    # ================= 无图删除逻辑 =================

    def remove_no_image_groups(self, df):
        """删除无图父类（及其子类）；子类可覆写 clean_no_image 时调用"""
        required = ["Type", "SKU", "Parent", "Images"]
        if not all(c in df.columns for c in required):
            print(f"警告: 缺失 {required} 中部分列，跳过无图删除逻辑。")
            return df

        df = df.copy()
        # 填充 NaN 以避免字符串匹配时报错
        for col in required:
            df[col] = df[col].fillna("").astype(str)

        # (A) 无图父类：删除 variable 及其所有子类
        invalid_parents = (df["Type"].str.lower() == "variable") & (df["Images"] == "")
        invalid_skus = set(df[invalid_parents]["SKU"])
        df = df[~invalid_parents]
        df = df[~df["Parent"].isin(invalid_skus)]

        # (B) 无图子类：variation 无图且同级变体数量 >1 时删除（默认关闭，按需开启）
        r_move = False
        if r_move:
            # 1. 先统计当前数据中，每个 Parent 下有几个 variation
            variations = df[df["Type"].str.lower() == "variation"]
            variation_counts = variations.groupby("Parent").size()

            # 2. 将统计的数量映射回原数据，生成辅助列 'var_count'
            df["var_count"] = df["Parent"].map(variation_counts).fillna(0)
            # 3. 标记需要删除的 variation：类型为变体 AND 没图片 AND 同级变体数量大于1
            invalid_variation_mask = (
                    (df['Type'].str.lower() == 'variation') &
                    (df['Images'] == '') &
                    (df['var_count'] > 1)
            )

            # 执行删除
            df = df[~invalid_variation_mask]
            # 删掉刚刚生成的辅助列，保持表结构干净
            df = df.drop(columns=["var_count"])

        print(f"因父类无图，连带移除了 {len(invalid_skus)} 组商品(含子类)。")
        return df

    def run(self):
        df = pd.read_csv(self.input_path)
        failed_set = self.load_failed_images()

        df["Images"] = df["Images"].apply(lambda x: self.to_new_url(x, failed_set))
        df = self.remove_no_image_groups(df)

        self.Tool.File.save_csv(df, self.output_path)
        print(f"处理完成，结果已保存到 {self.output_path}")
        return df
