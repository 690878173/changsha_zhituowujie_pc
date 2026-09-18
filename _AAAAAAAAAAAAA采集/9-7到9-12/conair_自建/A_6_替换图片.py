from config import Tool

csv_input_path = Tool.File.path_add_site(r'fwq/variable.csv')
csv_output_path = Tool.File.path_add_site(r'res/picture.csv')

from _ljp.mb.zj import Replace_imgs



class Pc(Replace_imgs):


    def build_new_url_base(self):
        web_name = self.Tool.site + "_ljp"
        return f"https://cdn.zhimatrix.com/{web_name}/images/"


    def to_new_url(self, image_urls, failed_set):
        """将单个单元格内多个 url 转为新链接，跳过失败图片"""

        import pandas as pd
        if pd.isna(image_urls) or str(image_urls).strip() == "":
            return ""

        images_split = self.Tool.config.images_split
        text = str(image_urls)
        if images_split not in text and ",http" in text:
            images_split = ","
            print(f'替换为,分割')

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
            all_url = '''https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/SHV30B/SHV30B--inset-08.png
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/SD9NXL_features_inset_03.jpg
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/CLS1L_whatsinthebox_inset_07.png
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/650L_before%20after_inset_08.png
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/CLS1L_features_inset_03.png
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/BC86L_features_inset_02.jpg
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/910P_before%20after_inset_08.png
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/CLS1L_before%20after_inset_06.png
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/753L_features_inset_01.png
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/CB05_features_inset_02.jpg
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/CD1003L_features_inset_03.png
https://www.conair.com/dw/image/v2/ABAF_PRD/on/demandware.static/-/Sites-conair-master/en_US/v1789013455476/359L_Infographic_0008.jpg
'''

            if url in all_url.split('\n'):
                continue
            new_urls.append(new_url)

            print(f'新URL: {new_url} => 原始url；{url}')

        return ",".join(new_urls)





if __name__ == '__main__':
    Pc(tool=Tool,input_path=csv_input_path,output_path=csv_output_path).run()

    wb = Tool.File.Web(csv_output_path)
    wb.run('fail/失败图片链接.csv')



