from curl_cffi import requests
import json
import os
from lxml import etree
import time



class Product:
    # 将爬取到的数据进行初步清洗，使其转变为纯json数据
    def __init__(self):
        self.cookies = {
            'JSESSIONID': '14b781f9b6c9683f4e5d84f8ba4a',
            'BNES_JSESSIONID': 'DtoSHKwcCFCKyvSsiyvglGcotWnbtxhws1iTGQ+SzhyezvXs5Cfg8vz5DUWXylpN6eTDjTaKqOFF4a4PWDoFwgD7v+7IdWHCBi2IuYL7tfo=',
            '_ga': 'GA1.1.407778976.1763169299',
            '__exponea_etc__': '204b77de-09de-46ad-ad83-3845d985f7a9',
            '__kla_id': 'eyJjaWQiOiJNVFZqTURRNE1XRXRZbUppWWkwME9ETTNMVGt6WXpZdE9HTmpaV0UyWVRjM04yRXoifQ==',
            '_pin_unauth': 'dWlkPVlqVmlZbVV3T1RNdE5XTTNOQzAwTmpVeExXSmhOV1F0TkRGaU1ERXhZak5tT1dRMg',
            '__exponea_etc__': '204b77de-09de-46ad-ad83-3845d985f7a9',
            '_pin_unauth': 'dWlkPVlqVmlZbVV3T1RNdE5XTTNOQzAwTmpVeExXSmhOV1F0TkRGaU1ERXhZak5tT1dRMg',
            '__exponea_time2__': '1.8724076747894287',
            '_fbp': 'fb.1.1763169309294.271086549155591275',
            'addshoppers.com': '2%7C1%3A0%7C10%3A1763169317%7C15%3Aaddshoppers.com%7C44%3AZDMzYTdmNzNlNmQxNDFiMDk0Yzc4OTAyOGVjNmI2YTg%3D%7Cb6e79244c073b88e22dc55ea65a50111cf1674f26fdb376ac0fab1b361301edc',
            '_svsid': '37067ce023062a9d873fdbf4454469a6',
            '_svsid': '37067ce023062a9d873fdbf4454469a6',
            'SSID': 'CQBO8x0qAAAAAAAQ1Bdp_jCDJBDUF2kDAAAAAAAAAAAAmfQaaQCd6VRIAQNXnigAENQXaQMAlOgAA_WAIAAQ1BdpAwApJgEDfmIlABDUF2kDAA',
            'SSSC': '791.G7572754464243921150.3|59540.2130165:75305.2450046:84052.2661975',
            'bo_pin': 'no_pin',
            'BNES_bo_pin': 'D0eANSOsGOyWMNlm6oWVm5UoCDnfcZmzgdihBoMQhrmO/IFc7Pymb+gJa0QgzWXOn92PBvRYFIk=',
            '__exponea_time2__': '1.8724076747894287',
            '_hp5_meta.978363606': "%7B%22userId%22%3A%221132074270891361%22%2C%22sessionId%22%3A%221689160390787567%22%2C%22sessionProperties%22%3A%7B%22time%22%3A1763374246343%2C%22id%22%3A%221689160390787567%22%2C%22utm%22%3A%7B%22source%22%3A%22%22%2C%22medium%22%3A%22%22%2C%22term%22%3A%22%22%2C%22content%22%3A%22%22%2C%22campaign%22%3A%22%22%7D%2C%22initial_pageview_info%22%3A%7B%22time%22%3A1763374246343%2C%22id%22%3A%225992344453158199%22%2C%22title%22%3A%22New%20Men's%20Boots%20%7C%20New%20Boots%20for%20Men%20-%20Bogs%22%2C%22previous_page%22%3A%22%2Fshop%2Findex.html%22%2C%22url%22%3A%7B%22domain%22%3A%22www.bogsfootwear.com%22%2C%22path%22%3A%22%2Fshop%2Fnew-mens-boots-shoes%22%2C%22query%22%3A%22%3Fpt_asset%3DSubMenunewArrivals%22%2C%22hash%22%3A%22%22%7D%7D%2C%22search_keyword%22%3A%22%22%2C%22referrer%22%3A%22https%3A%2F%2Fwww.bogsfootwear.com%2Fshop%2Findex.html%22%7D%7D",
            'SSRT': 'TfUaaQADAA',
            'BNES__pin_unauth': 'QXMLhopq/HhZoVJFPohb7jvddL9kibIWvRj2Z4VMlsNVN2xsdbrAjET21oho5xolSAkuZ+zobXKxFz6srVN2D5mVixNgY22UK1vaVDABTd1EDBJCi3GG/c9dYjUQCFl+2pt2EBeBSbPOR9ukthAOLSfE8ryB1ZWb',
            'BNES__svsid': 'gZ4qVTr7TPRMWBI+ImYKpnbWj+9nlnJ0BD8fiMGF0v9eiuC0nzdw05CRPZc006si6/pr/fjHv9dAB8QXvnVdMsfXabVcSFGzIXK6qzmQDks=',
            'BNES___exponea_time2__': 'Em4duvLY8Gvnqs5S92Lk8yho4WgCVKuj3Clesb3VOA9sv0QrsxKU9E867bmFPm/srlqB7ddXDA8nFOytAA4SPu1NA3uaEMUVdmkmXJUJk6I=',
            'BNES___exponea_etc__': 'NH+KTXy2tA04Z5qjqYGrawfBlNaA22UlYr0gEDD0UxMcjJ7Q3FANuVlkrQjKwu1dVl+22GvhquUCUklybklu9SVTBw18ApqBFuuJxA0Hwfjp0zuTu+YTxT5JKApExUsw',
            '_hp5_event_props.978363606': '%7B%22VariationID%22%3A%2259540%3A2130165%2C75305%3A2450046%2C84052%3A2661975%22%7D',
            'cto_bundle': 'bJ6Vi19oeXl2NU95SnN2Wk9UNTIzalBGOExzR0dKM09vR0J2Mzltb1FFWEJsRVBGb2N3NVNmMXNCVG9qMDdzYjMyRWIyN3c5S0tHM2s2dGNlZ1ZUaWN2bm5EcVF6bFhvSklUSTJOcE14QiUyQlkzTUlBNlNIaHUyeUFpSWp6eWFyWEtNSWNWQVZlbXJYNFdPU3dXOVg1d1FWRDVvM0l6YVRqRWNPUUlsNG5OckE3RzNZTSUzRA',
            '_hp5_let.978363606': '1763374415792',
            'SSOD': 'AKylAAAAEgBl7YAAMAAAAKL0GmlS9RppMAAAAA',
            '_ga_2QRBYCWTWB': 'GS2.1.s1763374237$o6$g1$t1763374426$j60$l0$h0',
        }

        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            # 'Cookie': "JSESSIONID=14b781f9b6c9683f4e5d84f8ba4a; BNES_JSESSIONID=DtoSHKwcCFCKyvSsiyvglGcotWnbtxhws1iTGQ+SzhyezvXs5Cfg8vz5DUWXylpN6eTDjTaKqOFF4a4PWDoFwgD7v+7IdWHCBi2IuYL7tfo=; _ga=GA1.1.407778976.1763169299; __exponea_etc__=204b77de-09de-46ad-ad83-3845d985f7a9; __kla_id=eyJjaWQiOiJNVFZqTURRNE1XRXRZbUppWWkwME9ETTNMVGt6WXpZdE9HTmpaV0UyWVRjM04yRXoifQ==; _pin_unauth=dWlkPVlqVmlZbVV3T1RNdE5XTTNOQzAwTmpVeExXSmhOV1F0TkRGaU1ERXhZak5tT1dRMg; __exponea_etc__=204b77de-09de-46ad-ad83-3845d985f7a9; _pin_unauth=dWlkPVlqVmlZbVV3T1RNdE5XTTNOQzAwTmpVeExXSmhOV1F0TkRGaU1ERXhZak5tT1dRMg; __exponea_time2__=1.8724076747894287; _fbp=fb.1.1763169309294.271086549155591275; addshoppers.com=2%7C1%3A0%7C10%3A1763169317%7C15%3Aaddshoppers.com%7C44%3AZDMzYTdmNzNlNmQxNDFiMDk0Yzc4OTAyOGVjNmI2YTg%3D%7Cb6e79244c073b88e22dc55ea65a50111cf1674f26fdb376ac0fab1b361301edc; _svsid=37067ce023062a9d873fdbf4454469a6; _svsid=37067ce023062a9d873fdbf4454469a6; SSID=CQBO8x0qAAAAAAAQ1Bdp_jCDJBDUF2kDAAAAAAAAAAAAmfQaaQCd6VRIAQNXnigAENQXaQMAlOgAA_WAIAAQ1BdpAwApJgEDfmIlABDUF2kDAA; SSSC=791.G7572754464243921150.3|59540.2130165:75305.2450046:84052.2661975; bo_pin=no_pin; BNES_bo_pin=D0eANSOsGOyWMNlm6oWVm5UoCDnfcZmzgdihBoMQhrmO/IFc7Pymb+gJa0QgzWXOn92PBvRYFIk=; __exponea_time2__=1.8724076747894287; _hp5_meta.978363606=%7B%22userId%22%3A%221132074270891361%22%2C%22sessionId%22%3A%221689160390787567%22%2C%22sessionProperties%22%3A%7B%22time%22%3A1763374246343%2C%22id%22%3A%221689160390787567%22%2C%22utm%22%3A%7B%22source%22%3A%22%22%2C%22medium%22%3A%22%22%2C%22term%22%3A%22%22%2C%22content%22%3A%22%22%2C%22campaign%22%3A%22%22%7D%2C%22initial_pageview_info%22%3A%7B%22time%22%3A1763374246343%2C%22id%22%3A%225992344453158199%22%2C%22title%22%3A%22New%20Men's%20Boots%20%7C%20New%20Boots%20for%20Men%20-%20Bogs%22%2C%22previous_page%22%3A%22%2Fshop%2Findex.html%22%2C%22url%22%3A%7B%22domain%22%3A%22www.bogsfootwear.com%22%2C%22path%22%3A%22%2Fshop%2Fnew-mens-boots-shoes%22%2C%22query%22%3A%22%3Fpt_asset%3DSubMenunewArrivals%22%2C%22hash%22%3A%22%22%7D%7D%2C%22search_keyword%22%3A%22%22%2C%22referrer%22%3A%22https%3A%2F%2Fwww.bogsfootwear.com%2Fshop%2Findex.html%22%7D%7D; SSRT=TfUaaQADAA; BNES__pin_unauth=QXMLhopq/HhZoVJFPohb7jvddL9kibIWvRj2Z4VMlsNVN2xsdbrAjET21oho5xolSAkuZ+zobXKxFz6srVN2D5mVixNgY22UK1vaVDABTd1EDBJCi3GG/c9dYjUQCFl+2pt2EBeBSbPOR9ukthAOLSfE8ryB1ZWb; BNES__svsid=gZ4qVTr7TPRMWBI+ImYKpnbWj+9nlnJ0BD8fiMGF0v9eiuC0nzdw05CRPZc006si6/pr/fjHv9dAB8QXvnVdMsfXabVcSFGzIXK6qzmQDks=; BNES___exponea_time2__=Em4duvLY8Gvnqs5S92Lk8yho4WgCVKuj3Clesb3VOA9sv0QrsxKU9E867bmFPm/srlqB7ddXDA8nFOytAA4SPu1NA3uaEMUVdmkmXJUJk6I=; BNES___exponea_etc__=NH+KTXy2tA04Z5qjqYGrawfBlNaA22UlYr0gEDD0UxMcjJ7Q3FANuVlkrQjKwu1dVl+22GvhquUCUklybklu9SVTBw18ApqBFuuJxA0Hwfjp0zuTu+YTxT5JKApExUsw; _hp5_event_props.978363606=%7B%22VariationID%22%3A%2259540%3A2130165%2C75305%3A2450046%2C84052%3A2661975%22%7D; cto_bundle=bJ6Vi19oeXl2NU95SnN2Wk9UNTIzalBGOExzR0dKM09vR0J2Mzltb1FFWEJsRVBGb2N3NVNmMXNCVG9qMDdzYjMyRWIyN3c5S0tHM2s2dGNlZ1ZUaWN2bm5EcVF6bFhvSklUSTJOcE14QiUyQlkzTUlBNlNIaHUyeUFpSWp6eWFyWEtNSWNWQVZlbXJYNFdPU3dXOVg1d1FWRDVvM0l6YVRqRWNPUUlsNG5OckE3RzNZTSUzRA; _hp5_let.978363606=1763374415792; SSOD=AKylAAAAEgBl7YAAMAAAAKL0GmlS9RppMAAAAA; _ga_2QRBYCWTWB=GS2.1.s1763374237$o6$g1$t1763374426$j60$l0$h0",
        }



    def get_product_url(self, url):
        page = 1
        url_list = []

        try:
            while True:
                # 构建当前页的URL
                # 构建API URL
                if page == 1:
                    products_url = url
                else:
                    products_url = f"{url}?page={page}"
                print(f"正在请求第 {page} 页: {products_url}")
                resp = requests.get(products_url, impersonate="chrome120")
                response = resp.text
                print(f"[DEBUG] 状态码: {resp.status_code}, HTML长度: {len(response)}")
                time.sleep(3)
                page_tree = etree.HTML(response)
                products = page_tree.xpath('//a/@href')

                seen = set()
                for product in products:
                    if not product:
                        continue

                    # 只要站内商品详情页，排除分类页、功能页、图片、邮件等
                    if not product.startswith('/'):
                        continue
                    if product.startswith(
                            ('/shop', '/myrtic', '/cart', '/help', '/about-us', '/authorized-retailers', '/terms',
                             '/privacy', '/accessibility', '/share', '/order', '/_', '/images', '/assets')):
                        continue
                    if product == '/':
                        continue
                    if 'design=true' in product:
                        continue

                    product_url = "https://rticoutdoors.com" + product

                    if product_url not in seen:
                        seen.add(product_url)
                        print(product_url)
                        url_list.append(product_url)


                if len(products) ==48:
                    page += 1
                else:
                    break
            return url_list
        except Exception as e:
            print(f'爬取出错: {e}')
            return url_list



    def main(self):
        try:
            # 确保文件存在
            input_file = r'/8-10到8-15/rticoutdoors_他人_更新数据/data.json'
            if not os.path.exists(input_file):
                print(f"输入文件不存在: {input_file}")
                return

            with open(input_file, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # 创建新字典来存储结果，而不是修改原始字典
            new_data = {}
            num = 1

            # 先收集所有键，然后遍历
            keys = list(data.keys())
            print(f"开始处理 {len(keys)} 个分类...")

            for category in keys:
                print(f"\n处理分类: {category}")
                url_list = self.get_product_url(data[category])
                # 将结果存储到新字典中
                new_data[category] = url_list
                print(f"{category} 保存成功 ({num}/{len(keys)}) - 获取了 {len(url_list)} 个URL")
                num += 1

            # 确保输出目录存在
            output_dir = os.path.dirname(r'/8-10到8-15/rticoutdoors_他人_更新数据/rticoutdoors_parse.json')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # 将新数据写入文件
            output_file = r'/8-10到8-15/rticoutdoors_他人_更新数据/rticoutdoors_parse.json'
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(new_data, file, indent=4, ensure_ascii=False)

            print(f"\n所有分类处理完成，结果已保存到: {output_file}")

            # 打印一些统计信息
            total_urls = sum(len(urls) for urls in new_data.values())
            print(f"总共获取了 {total_urls} 个产品URL")

        except Exception as e:
            print(f"主程序出错: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    obj = Product()
    obj.main()