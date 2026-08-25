"""步骤9：Shopify 打折模板

通用流程：读取 wp_to_shopify.csv -> 删除价格为 0 的商品（父类+子类）-> 按折扣 zk 计算售价 -> 输出打折 CSV。
"""
import pandas as pd


class Step9Discount:
    """打折基类"""

    def __init__(self, tool, input_path, output_path):
        self.tool = tool
        self.Tool = tool
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        self.Tool.File.create_dir(self.output_path)

        df = pd.read_csv(self.input_path, dtype=str).fillna("")
        df["Variant Compare At Price"] = pd.to_numeric(df["Variant Compare At Price"], errors="coerce")

        # 价格为 0 的商品：删除父类和所有子类
        zero_price_handles = df.loc[df["Variant Compare At Price"].eq(0), "Handle"].unique()
        deleted_count = df["Handle"].isin(zero_price_handles).sum()
        if len(zero_price_handles) > 0:
            df = df[~df["Handle"].isin(zero_price_handles)].copy()

        print(f"检测到价格为 0 的商品 {len(zero_price_handles)} 个，共删除父类和子类数据 {deleted_count} 行")

        # 按折扣计算售价
        df["Variant Price"] = df["Variant Compare At Price"] * self.Tool.zk
        df["Variant Price"] = df["Variant Price"].round(2)

        df.to_csv(self.output_path, index=False)
        print(f"处理完成，新文件已保存到: {self.output_path}")
        self.Tool.print(f"当前使用折扣:{self.Tool.zk}")
        return df
