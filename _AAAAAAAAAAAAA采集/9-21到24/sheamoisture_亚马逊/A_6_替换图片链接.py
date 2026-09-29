from urllib.parse import unquote

from config import Tool
import pandas as pd

from _ljp.mb.base import Replace_imgs

image_url_base = f"https://cdn.zhimatrix.com/{Tool.site}_zt/images_webp/"

input_path = Tool.File.path_add_site("fwq/variable.csv")

output_path = Tool.File.path_add_site("res/picture.csv")


def sanitize_filename(image_url):
    """根据URL生成唯一的基准文件名（不含后缀）"""
    decoded_url = unquote(image_url)               # ① URL 解码
    clean_name = decoded_url.split('/')[-1]        # ② 取最后一段

    for char in [".", "?", "&", "#", "$", "=", ",", ":", " ", "%"]:
        clean_name = clean_name.replace(char, "_") # ③ 特殊字符替换为 _

    return clean_name.strip('_')                   # ④ 去掉首尾下划线
class CdnImageStep(Replace_imgs):
    def build_new_url_base(self):
        return image_url_base

    def group_variable_families(self, df):
        """Move each variation next to its variable parent before image processing."""
        required_columns = {"Type", "SKU", "Parent"}
        if not required_columns.issubset(df.columns):
            return df

        parent_rows = {}
        variation_rows = {}
        for index, row in df.iterrows():
            product_type = self._field_value(row, "Type").lower()
            if product_type == "variable":
                sku = self._field_value(row, "SKU")
                if not sku:
                    raise ValueError(f"第 {index + 2} 行 variable 商品缺少 SKU")
                if sku in parent_rows:
                    raise ValueError(f"variable SKU 重复，无法关联变体: {sku!r}")
                parent_rows[sku] = index
            elif product_type == "variation":
                parent_sku = self._field_value(row, "Parent")
                variation_rows.setdefault(parent_sku, []).append(index)

        orphan_parents = [
            parent_sku for parent_sku in variation_rows if parent_sku not in parent_rows
        ]
        if orphan_parents:
            raise ValueError(
                "variation 商品找不到对应的 variable 父类: "
                + ", ".join(repr(parent_sku) for parent_sku in orphan_parents)
            )

        ordered_indexes = []
        for index, row in df.iterrows():
            product_type = self._field_value(row, "Type").lower()
            if product_type == "variation":
                continue

            ordered_indexes.append(index)
            if product_type == "variable":
                sku = self._field_value(row, "SKU")
                ordered_indexes.extend(variation_rows.get(sku, []))

        return df.loc[ordered_indexes].reset_index(drop=True)

    @staticmethod
    def hash_image_url(image_url):
        return sanitize_filename(image_url) + '.webp'

    def run(self):
        df = pd.read_csv(self.input_path)
        df = self.group_variable_families(df)
        df = self.reverse_product_families(df)
        failed_set = self.load_failed_images()

        df["Images"] = df["Images"].apply(
            lambda images: self.to_new_url(images, failed_set)
        )
        df = self.remove_no_image_groups(df)

        self.Tool.File.save_csv(df, self.output_path)
        print(f"处理完成，结果已保存到 {self.output_path}")
        return df


if __name__ == "__main__":
    CdnImageStep(Tool, input_path=input_path,output_path=output_path).run()

    wb = Tool.File.Web(output_path)
    wb.run('fail/失败图片链接.csv')
