import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lxml import etree

from config import Tool, images_split
from _ljp.mb.zj import Get_Product

# 测试数据条数 (None = 全部抓取)
ts_num = None
# 覆盖运行需要删除缓存文件

# 品牌名称
BRAND_NAME = Tool.site

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site("data/result.csv")
fail_file = Tool.File.path_add_site("data/fail.json")
catch_path = Tool.File.path_add_site('hc/3/data.json')
index_path = Tool.File.path_add_site('hc/3/index.json')

# 输出带url地址的res文件
output_ts_file = Tool.File.path_add_site('hc/3/result.csv')

no_url_ls = ['https://lumedeodorant.com/products/build-your-own-bundle']
fieldnames = None
headers = None
cookies = None
skip_input_url_ls = []
skip_output_url_ls = []
flush = False
catch_save_num = None
max_threads = 5


def _extract_remix_context(res_text: str) -> dict | None:
    """从 window.__remixContext 提取完整 JSON 数据"""
    start = res_text.find('window.__remixContext = {')
    if start < 0:
        return None
    start += len('window.__remixContext = ')
    try:
        # raw_decode understands braces inside quoted strings, unlike a
        # character-counting parser, and stops before the trailing semicolon.
        value, _ = json.JSONDecoder().raw_decode(res_text[start:])
        return value
    except (json.JSONDecodeError, TypeError):
        return None


def _portable_text_to_html(blocks: list[dict]) -> str:
    """将 Sanity Portable Text 块列表转换为保留格式的 HTML 字符串"""
    if not blocks:
        return ''

    html_parts = []
    pending_list = []   # 暂存连续的同类型列表块
    last_list_type = ''

    def _flush_list():
        nonlocal pending_list, last_list_type
        if not pending_list:
            return
        tag = 'ul' if last_list_type == 'bullet' else 'ol'
        items = ''.join(f'<li>{b}</li>' for b in pending_list)
        html_parts.append(f'<{tag}>{items}</{tag}>')
        pending_list = []
        last_list_type = ''

    def _render_children(children: list[dict]) -> str:
        """将 block 的 children（含 marks）渲染为 HTML 内联内容"""
        result = ''
        for child in children:
            text = child.get('text', '')
            marks = child.get('marks', [])
            if 'strong' in marks:
                text = f'<strong>{text}</strong>'
            if 'em' in marks:
                text = f'<em>{text}</em>'
            # 保留换行符为 <br>
            text = text.replace('\n', '<br>')
            result += text
        return result

    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get('_type') != 'block':
            continue

        list_item = block.get('listItem', '')
        content = _render_children(block.get('children', []))

        if list_item:
            if list_item != last_list_type:
                _flush_list()
                last_list_type = list_item
            pending_list.append(content)
        else:
            _flush_list()
            style = block.get('style', 'normal')
            if style in ('h1', 'h2', 'h3', 'h4'):
                tag = style
            else:
                tag = 'p'
            html_parts.append(f'<{tag}>{content}</{tag}>')

    _flush_list()
    return '\n'.join(html_parts)


def _extract_accordion_sections(pdp_content: dict | None) -> dict[str, str]:
    """从 pdpContent 提取 accordion 各板块内容，返回 {title: html_string}"""
    result = {}
    if not isinstance(pdp_content, dict):
        return result
    groups = pdp_content.get('pdpAccordionGroups', [])
    if not groups:
        return result

    for group in groups:
        for item in group.get('items', []):
            title = item.get('title', '')
            gd = item.get('generalDescription', [])
            if not gd or not title:
                continue
            html = _portable_text_to_html(gd)

            # 如果还有 iconContent 子区块，也追加
            icons = item.get('iconContent', [])
            if icons:
                icon_parts = []
                for ic in icons:
                    ic_blocks = ic.get('content', [])
                    if ic_blocks:
                        ic_html = _portable_text_to_html(ic_blocks)
                        icon_parts.append(f'<div>{ic_html}</div>')
                if icon_parts:
                    html += '\n' + '\n'.join(icon_parts)

            result[title] = html

    return result
#


def _extract_json_ld(res_text: str) -> dict | None:
    """提取 Product 类型 JSON-LD"""
    for m in re.finditer(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        res_text, re.DOTALL
    ):
        try:
            ld = json.loads(m.group(1).strip())
            items = ld if isinstance(ld, list) else [ld]
            for item in items:
                if isinstance(item, dict) and item.get('@type') == 'Product':
                    return item
        except (json.JSONDecodeError, TypeError):
            continue

    Tool.print(f'提取类型失败')
    return None


def _get_props(json_ld: dict) -> dict[str, str]:
    """additionalProperty → {name: value}"""
    return {p['name']: p['value'] for p in json_ld.get('additionalProperty', [])
            if 'name' in p and 'value' in p}


def _is_combo(html: etree._Element, json_ld: dict, url: str) -> bool:
    """检测组合/捆绑商品（需用户选择多个不同产品）"""
    # 1. URL 关键词
    combo_kw = ['build-your-own-bundle', 'mix-match', '-item', '-duo',
                'starter-pack', 'pits-bits']
    if any(kw in url.lower() for kw in combo_kw):
        return True

    # 2. JSON-LD Product Type == Bundle
    if _get_props(json_ld).get('Product Type') == 'Bundle':
        return True

    # 3. 页面有多个不同 "Choose a XXX!"（如 Stick + Spray）
    choose_types = {m.group(1).lower() for node in html.xpath(
        '//*[contains(text(),"Choose a")]')
        for m in [re.search(r'Choose a (\w+)', ''.join(node.xpath('.//text()')))]
        if m}
    if len(choose_types) >= 2:
        return True

    # 4. "Choose N XXX" 模式（如 Choose 3 sticks）
    if not choose_types:
        body = ' '.join(html.xpath('//body//text()'))
        if re.search(r'Choose\s+\d+\s+\w+', body, re.IGNORECASE):
            return True

    return False


def _parse_pack_sizes(html: etree._Element) -> dict[str, str]:
    """解析 pack_size radio → {label: price_str}，如 {'Single': '$15/EA'}"""
    result = {}
    for radio in html.xpath('//input[@type="radio" and @name="pack_size"]'):
        label_el = radio.xpath('./ancestor::label[1]')
        if not label_el:
            continue
        label_el = label_el[0]
        p_tags = label_el.xpath('.//p')
        if len(p_tags) >= 2:
            label = ''.join(p_tags[0].xpath('.//text()')).strip()
            price = ''.join(p_tags[1].xpath('.//text()')).strip()
        else:
            text = ''.join(label_el.xpath('.//text()')).strip()
            m = re.search(r'\$[\d.]+/EA|\$[\d.]+', text)
            price = m.group() if m else ''
            label = text.replace(price, '').strip() if price else text
        if label and price:
            result[label] = price
    return result


def _extract_images(html: etree._Element, main_img: str, url: str) -> list[str]:
    """提取产品图片：主图 + 页面匹配产品handle的cdn图"""
    def _key(img_url: str):  # 去掉query参数用于去重
        return img_url.split('?')[0]
    seen = {_key(main_img)} if main_img else set()
    images = [main_img] if main_img else []
    handle = url.rstrip('/').split('/')[-1]
    core = re.sub(r'-\d+-pack$', '', handle).replace('-', '')

    for img in html.xpath('//img[@src]'):
        src = img.get('src', '')
        if 'cdn.shopify.com' not in src:
            continue
        sl = src.lower()
        al = (img.get('alt', '') or '').lower()
        skip = ['nav', 'logo', 'icon', 'testimonial', 'thumb_',
                'byobcrosssell', 'splitblock', 'pdpmediatile', 'footer',
                'l1-', 'l3-', 'featured-nav']
        if any(p in sl for p in skip):
            continue
        if any(p in al for p in ['testimonial']):
            continue

        src_c = sl.replace('-', '')
        if core.lower() in src_c and _key(src) not in seen:
            seen.add(_key(src))
            seen.add(src)  # 也记录完整URL
            images.append(src)

    return images


def _get_detail_page(url, category, res_text) -> list[dict]:
    """lumedeodorant.com 产品页解析"""
    html = etree.HTML(res_text)

    # ===== 1. JSON-LD =====
    ld = _extract_json_ld(res_text)
    if not ld:
        Tool.print(f'没有jd字段')
        return []

    # ===== 2. 跳过组合商品 =====
    if _is_combo(html, ld, url):
        Tool.print(f'组合商品:{url}')
        return []

    # ===== 3. 解析基本字段 =====
    name = ld.get('name', '')
    desc_plain = ld.get('description', '')
    sku = ld.get('sku', '')
    main_img = ld.get('image', '')
    ld_price = str(ld.get('offers', {}).get('price', ''))

    # ===== 4. 从 Remix 上下文提取 accordion 板块 (Key Benefits / Ingredients / How to Apply) =====
    remix_ctx = _extract_remix_context(res_text)
    pdp_content = None
    if remix_ctx:
        try:
            ld_data = remix_ctx.get('state', {}).get('loaderData', {})
            # Remix route ids are generated by the build; match the stable
            # product-route suffix instead of one historical key.
            product_data = next(
                (
                    value for key, value in ld_data.items()
                    if isinstance(key, str)
                    and key.endswith('/products/$handle/index')
                    and isinstance(value, dict)
                ),
                {},
            )
            pdp_content = product_data.get('pdpContent')
        except Exception:
            pdp_content = None

    accordion_sections = _extract_accordion_sections(pdp_content)

    # 构建 HTML 描述：JSON-LD 描述 + accordion 各板块
    desc_html_parts = [f'<p>{desc_plain}</p>'] if desc_plain else []
    for section_title in ['Key Benefits', 'Ingredients']:
        section_html = accordion_sections.get(section_title, '')
        if section_html:
            desc_html_parts.append(f'<h3>{section_title}</h3>')
            desc_html_parts.append(section_html)

    desc = '\n'.join(desc_html_parts) if desc_html_parts else desc_plain

    # 构建自定义字段 extra：key_benefits / ingredients / how_to_apply（HTML 格式）
    ZDY_PREFIX = 'Product InformationProduct Information (product.metafields.c_f.'
    extra = {}
    key_benefits_html = accordion_sections.get('Key Benefits', '')
    ingredients_html = accordion_sections.get('Ingredients', '')
    how_to_apply_html = accordion_sections.get('How to Apply', '')
    # if key_benefits_html:
    #     extra[f'{ZDY_PREFIX}key_benefits)'] = key_benefits_html
    # if ingredients_html:
    #     extra[f'{ZDY_PREFIX}ingredients)'] = ingredients_html
    # if how_to_apply_html:
    #     extra[f'{ZDY_PREFIX}how_to_apply)'] = how_to_apply_html

    # ===== 5. 产品图片 =====
    common_images = _extract_images(html, main_img, url)

    # ===== 6. 解析 pack_size 变体 =====
    pack_variants = _parse_pack_sizes(html)

    # ===== 7. 缺失警告 =====
    WARN_RED, END = "\033[91m", "\033[0m"
    if not ld_price and not pack_variants:
        print(f"{WARN_RED}【价格缺失】URL: {url}{END}")
    if not desc_plain:
        print(f"{WARN_RED}【描述缺失】URL: {url}{END}")

    # ===== 8. 构建产品 =====
    if not pack_variants:
        # 无 pack_size 变体 → simple 商品
        price = Tool.clean_price(ld_price)
        return [Tool.Product.Simple(
            name=name,
            desc=desc,
            price=price,
            cat=category,
            url=url,
            sku=sku,
            imgs=common_images,
            brand=BRAND_NAME,
            **extra,
        ).to_dic()]

    # 有 pack_size 变体 → variation 商品
    rows = []
    for label, raw_price in pack_variants.items():
        clean_p = Tool.clean_price(raw_price.replace('/EA', '').strip())
        rows.append(Tool.Product.Variation(
            name=name,
            desc=desc,
            price=clean_p,
            cat=category,
            url=url,
            sku=f'{sku}_{label.upper().replace(" ", "_")}',
            imgs=common_images,
            att={"Size": label},
            parent=sku,
            brand=BRAND_NAME,
            **extra,
        ).to_dic())

    return rows

def _legacy_get_detail_page(url, category, res_text):
    if url in no_url_ls:
        return
    _ck = url.split('?')[-1]
    for i in ['-pack']:
        if i in url:
            return
    html = etree.HTML(res_text)

    if 'Love It or Leave It: 60-Day Return Window (U.S.)' in res_text:
        Tool.print(f'组合品:{url}')
        return
    ts_url = ['https://lumedeodorant.com/products/summer-peach-solid-stick-deodorant']
    if url in ts_url:
        return

    Tool.HTML.save(res_text)

    title = html.xpath('//title')[0].xpath('.//text()')

    name = ''.join(title).strip()
    if not name:
        Tool.HTML.save(res_text)
        Tool.print(f'名字为空:{url}')

    data = Tool.HTML.script_text(res_text,r'window\.__remixContext')
    data = json.loads(data)
    Tool.File.save_json(data,'hc/product_info.json')

    data = data['state']['loaderData']

    Tool.File.save_json(data, 'hc/product_info.json')

    _p1_data = data['./routes/products/$handle/index']


    # 获取描述等消息
    pdp_content  = _p1_data.get('pdpContent')
    if not pdp_content:
        Tool.print(f'缺失pdp_content:{url}')
        return
    accordion_sections = _extract_accordion_sections(pdp_content)
    if not accordion_sections:
        Tool.print(f'pdp_content里面缺失groups,url:{url}')
        return
    need_zd_ls = ['Key Benefits','Ingredients']

    #>>>>>>>=======================
    # NOTE: 自定义字段
    need_zd_dic = {}
    for _zd in need_zd_ls:
        need_zd_dic[_zd] = accordion_sections.get(_zd, '')

    #>>>>>>>=======================

    # >>>>>>>=======================
    # NOTE: 标题，id，描述，图片链接=====》主体的

    _p1_title = _p1_data['title']
    _p1_id = _p1_data['id'].split('/')[-1]
    _p1_descriptionHtml = _p1_data['descriptionHtml']
    _p1_featuredImage = _p1_data['featuredImage']['url']
    _p1_edge_image_ls = _p1_data['images']['edges']

    _p1_edge_image = [_d['node']['url'] for _d in _p1_edge_image_ls]

    main_imgs = [_p1_featuredImage] + _p1_edge_image

    # >>>>>>>=======================

    _pack_size_dict = _parse_pack_sizes(html)
    if not _pack_size_dict:
        # NOTE: 单品
        Tool.print(f'单品:{url}')
        exit()
        return

    # >>>>>>>=======================
    # NOTE: 提取变体属性价格
    pack_size_dict = {}
    for _k,_v in _pack_size_dict.items():
        _v = Tool.clean_price(_v)
        try:
            _v = float(_v)

        except Exception as e:
            Tool.print(f'价格无法转换:e:{e},{_v}')

        if _k == 'Single':
            pack_size_dict[_k] = _v
        else:
            _k_num = re.search(r'(\d+)-Pack', _k)
            if _k_num:
                _k_num = _k_num.group(1)
            else:
                Tool.print(f'无法提取-Pack')
            pack_size_dict[_k] = _v * int(_k_num)

    # >>>>>>>=======================
    _node_imgs = {}
    for _node in _p1_data['prebuilts']['references']['nodes']:
        _title = _node['title']
        _imgs = [_['url'] for _ in _node['images']['nodes']]
        _node_imgs[_title] = _imgs


    combos = []
    for label, price in pack_size_dict.items():
        _attrs = {'Size':label} # Pack Size
        _price = price
        for _label in list(_node_imgs.keys()):
            if label in _label:
                _imgs = _node_imgs[_label]
                # print(f'写入URl:{_imgs}')
                break
            else:
                # print(f'写入URl:{_p1_featuredImage}')
                _imgs = [_p1_featuredImage]

        _combo = Tool.Product.VariantCombo(attrs=_attrs,price=_price,images=_imgs)

        combos.append(_combo)

    res = Tool.Product.build_products(name=name,desc=_p1_descriptionHtml,price=price,category=category,url=url,sku=_p1_id,combos=combos,common_images=main_imgs)
    return res

    print(res)

    print(
        title,_p1_title,_p1_id
    )


    print(url)
    exit()





def get_detail_page(url, category, res_text):
    """Parse a PDP using the current JSON-LD/Remix parser."""
    # A ``-3-pack``/``-5-pack`` URL is often a normal single-SKU product
    # page, not a bundle.  Let the page parser decide from its JSON-LD and
    # pack-size controls; filtering it here turns valid products into errors.
    if url in no_url_ls:
        return []
    if 'Love It or Leave It: 60-Day Return Window (U.S.)' in res_text:
        Tool.print(f'组合品:{url}')
        return []
    return _get_detail_page(url, category, res_text)




class Pc(Get_Product):
    """Lume Step 3 adapter using the shared cached product workflow."""

    @staticmethod
    def _is_bundle_url(url):
        """The collection feed exposes bundle-only URLs as product links."""
        value = str(url).lower().rstrip('/')
        return (
            value.endswith('build-your-own-bundle')
            or '-pack' in value
            or '-item' in value
            or '-duo' in value
            or 'starter-pack' in value
            or value.endswith('travel-kit')
        )

    def load_tasks(self):
        # Filter intentional bundle exclusions before Get_Product queues them;
        # an empty parser result otherwise becomes a misleading failure.
        data = self.Tool.File.load_json(self.input_path)
        filtered = {
            category: [url for url in urls if not self._is_bundle_url(url)]
            for category, urls in data.items()
        }
        self._load_tasks_from_mapping(filtered)

    def fetch_product(self, url, category):
        response = self.Tool.get(url, headers=headers, cookies=cookies)
        if not response or response.status_code >= 400:
            raise RuntimeError(
                f'商品页请求失败: status={getattr(response, "status_code", 0)} url={url}'
            )
        return get_detail_page(url, category, response.text)


def main():
    Pc(
        tool=Tool,
        input_path=input_file,
        output_path=output_file,
        fail_file=fail_file,
        catch_path=catch_path,
        index_path=index_path,
        output_ts_file=output_ts_file,
        catch_save_num=catch_save_num,
        ts_num=ts_num,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        fieldnames=fieldnames,
        flush=flush,
        max_threads=max_threads,
    ).run()


if __name__ == '__main__':
    main()
