import pandas as pd

from config import Tool
from _ljp.mb.base import Replace_imgs


input_file = Tool.File.path_add_site("fwq/variable.csv")
output_file = Tool.File.path_add_site("res/picture.csv")


class Pc(Replace_imgs):
    def build_new_url_base(self):
        return f"https://cdn.zhimatrix.com/{self.Tool.site}_ljp/images/"

    def run(self):
        df = pd.read_csv(self.input_path, dtype=str, keep_default_na=False)
        failed_images = self.load_failed_images()
        df["Images"] = df["Images"].apply(
            lambda value: self.to_new_url(value, failed_images)
        )
        df = self.remove_no_image_groups(df)
        self.Tool.File.save_csv(df, self.output_path)
        self.Tool.print(f"图片链接替换完成，已保存到 {self.output_path}", color="green")
        return df


if __name__ == "__main__":
    Pc(Tool, input_path=input_file, output_path=output_file).run()



