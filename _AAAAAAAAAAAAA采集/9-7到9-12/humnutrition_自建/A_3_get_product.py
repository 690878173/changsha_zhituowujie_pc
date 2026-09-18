import json
import re
from html import escape

from lxml import etree
from config import Tool

# 文件路径配置
input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site("res/result.csv")
fail_file = Tool.File.path_add_site('data/fail.json')

catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')
# 携带原始url输出文件
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

# 测试数据条数 (None = 全部抓取)
ts_num = None

catch_save_num = None
# URL黑名单
skip_input_url_ls = []
# 未实现字段
skip_output_url_ls = []

headers = None
cookies = None

flush = False

# CSV输出表头,默认就应该为None，表头后续会处理
fieldnames = None

max_threads = 2

from _ljp.mb.zj import Get_Product

class Pc(Get_Product):


    def fetch_product(self, url, category):
        """请求并解析单个商品。

        返回标准化产品字典列表（每个元素为 Product.to_dic() 结果）。
        """
        res = Tool.get(url,headers=headers,cookies=cookies)




        tx = res.text
        T = _T(url,category,tx)

        ls = T.run()


        return ls

class _T:
    def __init__(self, url, category, res_text):
        self.url = url
        self.category = category
        self.res_text = res_text
        self.typ = 'simple'
        self.html = etree.HTML(res_text)

    def get_main_name(self, html):
        try:
            # Product pages and bundle pages use different title markers.
            node = html.xpath(
                '//h1[@data-pdp-title]/text() | '
                '//h1[contains(concat(" ", normalize-space(@class), " "), " pdp-h1 ")]/text()'
            )

            if not node:
                raise ValueError('页面未找到商品标题')
            return ''.join(node[0]).strip()
        except Exception as e:
            raise ValueError(f'获取主名称失败:{e}') from e


    def get_main_price(self, html):
        """Extract the current product price from the server-rendered page.

        HUM now exposes the price in metadata and JSON-LD rather than the old
        sr-only span. Keep a few fallbacks because bundle/product variants do
        not all render the same markup.
        """
        price_candidates = html.xpath(
            '//meta[@name="product:price:amount" or '
            '@name="og:price:amount"]/@content'
        )

        for script in html.xpath('//script[@type="application/ld+json"]/text()'):
            try:
                payload = json.loads(script)
            except (TypeError, ValueError):
                continue
            nodes = payload if isinstance(payload, list) else [payload]
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                offers = node.get('offers')
                offers = offers if isinstance(offers, list) else [offers]
                for offer in offers:
                    if isinstance(offer, dict) and offer.get('price') is not None:
                        price_candidates.append(str(offer['price']))

        # Astro's data layer is present even when the price component is
        # hydrated client-side and therefore absent from the static DOM.
        page_text = etree.tostring(html, encoding='unicode', method='html')
        price_candidates.extend(
            re.findall(r'productPrice\s*=\s*["\']([0-9]+(?:\.[0-9]+)?)', page_text)
        )

        for value in price_candidates:
            match = re.search(r'\d+(?:\.\d+)?', str(value).replace(',', ''))
            if match:
                return Tool.clean_price(match.group(0))

        raise ValueError('获取价格失败:页面未找到商品价格')

    def get_main_sku(self, html):
        try:
            # TODO 业务xpath
            node = html.xpath('//div[@class="xxx"]')
            return self.url.split('/')[-1]
        except Exception as e:
            Tool.print(f'获取sku失败:{e}')
            return ""

    def get_main_desc(self, html):
        try:
            # TODO 业务xpath
            node = html.xpath('//div[@data-pdp-variant-description]')
            if not node:
                node = html.xpath('//div[@class="bundles-details"]/h2[@class]')

            return node[0]
        except Exception as e:
            Tool.print(f'获取描述失败:{e}')
            return ""

    def get_main_imgs(self, html):
        try:
            # TODO 业务xpath，返回图片列表
            node = html.xpath('//div[@id="gallery"]/div/a/@href')
            node = [i for i in node if '.mp4' not in i]
            return node
        except Exception as e:
            Tool.print(f'获取图片失败:{e}')
            return []

    @staticmethod
    def _unwrap_astro_props(value):
        """Decode Astro's [type, value] serialization wrappers."""
        if isinstance(value, list):
            if len(value) == 2 and value[0] in (0, 1):
                return _T._unwrap_astro_props(value[1])
            return [_T._unwrap_astro_props(item) for item in value]
        if isinstance(value, dict):
            return {key: _T._unwrap_astro_props(item) for key, item in value.items()}
        return value

    @staticmethod
    def _portable_text_to_html(content):
        """Convert the product-detail Portable Text blocks to safe rich text."""
        blocks = _T._unwrap_astro_props(content)
        if not isinstance(blocks, list):
            return ''

        paragraphs = []
        for block in blocks:
            if not isinstance(block, dict) or block.get('_type') != 'block':
                continue
            fragments = []
            for span in block.get('children', []):
                if not isinstance(span, dict):
                    continue
                text = str(span.get('text', ''))
                if not text:
                    continue
                fragment = escape(text, quote=False).replace('\n', '<br>')
                marks = span.get('marks', [])
                marks = marks if isinstance(marks, list) else [marks]
                if 'strong' in marks:
                    fragment = f'<strong>{fragment}</strong>'
                if 'em' in marks:
                    fragment = f'<em>{fragment}</em>'
                fragments.append(fragment)
            if fragments:
                paragraphs.append(f'<p>{"".join(fragments)}</p>')

        return Tool.HTML.clean_text_field(''.join(paragraphs))

    def get_att(self, html):
        """Extract PDP detail accordions from Astro props or legacy markup."""
        wanted_fields = ('Key Ingredients', 'The Ick List', 'Clinically Tested', 'How to use')
        details = {}

        for island in html.xpath('//astro-island[contains(@component-url, "ProductDetails")]'):
            try:
                props = self._unwrap_astro_props(json.loads(island.get('props', '{}')))
            except (TypeError, ValueError):
                continue
            product_details = props.get('productDetails', {})
            for item in product_details.get('items', []):
                if not isinstance(item, dict):
                    continue
                title = str(item.get('title', '')).strip()
                if title not in wanted_fields:
                    continue
                content = self._portable_text_to_html(item.get('content', []))
                if content:
                    details[title] = content

        # Preserve compatibility with older server-rendered accordion markup.
        for node in html.xpath('//div[@data-headlessui-state]'):
            title = ''.join(node.xpath('./h3/button/span//text()')).strip()
            if title not in wanted_fields or title in details:
                continue
            content_nodes = node.xpath('./div')
            if content_nodes:
                details[title] = Tool.HTML.clean_product_desc(content_nodes[0])

        return details

    def check_cob(self, html):
        """判断是否存在变体商品"""
        try:
            # TODO 业务逻辑，返回 True/False
            return False
        except Exception as e:
            Tool.print(f'检测变体失败:{e}')
            return False

    def get_cobs(self, html):
        """抓取所有变体数据"""
        try:
            node = html.xpath('//div[@class="xxx"]')
            cobs = []
            s_ls = []  # TODO 变体节点列表xpath
            for _ in s_ls:
                # TODO 提取变体字段
                cob_imgs_ls = []
                cob_name = ""
                cob_price = ""
                cob_sku = None
                cob_att = {}

                cob_desc = Tool.HTML.clean_product_desc(cob_desc)
                cob_price = Tool.clean_price(cob_price)
                cob_imgs = Tool.Product.clean_imgs(cob_imgs_ls)
                cob = Tool.Product.Variation(
                    url=self.url, cat=self.category, imgs=cob_imgs,
                    name=cob_name, desc=cob_desc, price=cob_price,
                    sku=cob_sku, att=cob_att
                ).to_dic()
                cobs.append(cob)
            return cobs
        except Exception as e:
            Tool.print(f'获取变体数据失败:{e}')
            return []

    def run(self) -> list:
        try:
            """统一入口：执行解析，返回标准化产品字典列表"""
            main_name = self.get_main_name(self.html)
            main_price = self.get_main_price(self.html)
            main_sku = self.get_main_sku(self.html)
            main_desc = self.get_main_desc(self.html)
            main_imgs_ls = self.get_main_imgs(self.html)
            main_att = self.get_att(self.html)



            main_desc = Tool.HTML.clean_product_desc(main_desc)
            main_price = Tool.clean_price(main_price)
            main_img = Tool.Product.clean_imgs(main_imgs_ls)

            if self.check_cob(self.html):
                self.typ = 'variation'

            if self.typ == 'simple':
                product = Tool.Product.Simple(
                    url=self.url, cat=self.category, imgs=main_img,
                    name=main_name, sku=main_sku, price=main_price,
                    desc=main_desc,**main_att
                ).to_dic()
                return [product]

            return self.get_cobs(self.html)
        except Exception as e:
            Tool.print(f'run 解析失败:{e}')

            Tool.HTML.save(self.res_text,f'html/3/{self.url.split('/')[-1]}.html')
            return []






if __name__ == '__main__':
    pc = Pc(tool=Tool,
            input_path=input_file,
            output_path=output_file,
            fail_file=fail_file,
            skip_input_url_ls=skip_input_url_ls,
            skip_output_url_ls=skip_output_url_ls,
            ts_num=ts_num,
            fieldnames=fieldnames,
            catch_path=catch_path,
            index_path=index_path,
            output_ts_file=output_ts_file,
            flush=flush,
            max_threads=max_threads,
            catch_save_num=catch_save_num
            )
    pc.run()
