from .html_utils import HTML
from .url_utils import URL
from .simtool import SimTool
from .config import _IMAGE_SPLIT




class Product:


    def __init__(self, config):
        self.config = config

    @property
    def simple(self):
        return ProductSimple

    @property
    def variation(self):
        return ProductVariation

    def Simple(self, *, sku, name, desc, price, cat, imgs, url,
               brand=None, stock=None, is_upload=None, parent=None, tags=None, **exc):
        return ProductSimple(
            product=self,
            sku=sku, name=name, desc=desc, price=price, cat=cat,
            imgs=imgs, url=url, brand=brand, stock=stock,
            is_upload=is_upload, parent=parent, tags=tags, **exc,
        )

    def Variation(self, *, name, desc, price, cat, imgs, url, att, parent,
                  sku=None, brand=None, stock=None, is_upload=None, tags=None, **exc):
        return ProductVariation(
            product=self,
            name=name, desc=desc, price=price, cat=cat,
            imgs=imgs, url=url, attr=att, parent=parent,
            sku=sku, brand=brand, stock=stock,
            is_upload=is_upload, tags=tags, **exc,
        )

    def clean_imgs(self, imgs, base_url=None):
        if imgs is None:
            return []
        if isinstance(imgs, tuple):
            imgs = list(imgs)
        if not isinstance(imgs, list):
            SimTool.print(f'imgs 类型错误: {type(imgs)}')
            imgs = [imgs]
        base = base_url or self.config.base_url
        result = []
        for img in imgs:
            img = (img or "").strip()
            if not img:
                continue
            if img.startswith(('http://', 'https://')):
                full = img
            else:
                full = URL.site_add(base, img)
            if "," in full:
                msg = f'逗号存在于原始链接中，请使用 {_IMAGE_SPLIT} 分割'
                if SimTool._msg != msg:
                    SimTool._msg = msg
                    SimTool.print(msg)
            result.append(full)
        return result

    @staticmethod
    def build_custom_field_name(field: str) -> str:
        if '(product.metafields.c_f.' in field:
            return field
        field = field.replace('&','').replace('  ','')
        return f"{field}(product.metafields.c_f.{field.replace(' ', '_').lower()})"


class ProductSimple:

    def __init__(self, product:Product, *, sku, name, desc, price, cat, imgs, url,
                 brand=None, stock=None, is_upload=None, parent=None, tags=None,
                 tye='simple', **exc):
        self.product = product            # 回引用 Product，取 config / 调方法
        self.config = product.config      # 快捷引用
        self.tye = tye
        self.sku = sku
        self.name = name
        self.desc = desc
        self.price = price
        self.imgs = imgs
        self.cat = cat
        self.tags = tags
        self.brand = brand
        self.stock = 1000.0 if stock is None else stock
        self.is_upload = is_upload or 0
        self.parent = parent
        self.exc = exc
        self.url = url
        self.clean()


    def _build_custom_field_name(self,field: str) -> str:
        return self.product.build_custom_field_name(field)

    def clean(self):
        if isinstance(self.imgs, str):
            SimTool.print(f"imgs 转列表: {self.url}")
            self.imgs = [self.imgs]
        elif not isinstance(self.imgs, list):
            raise TypeError(f"imgs 类型错误: {type(self.imgs)}, {self.url}")

        self.imgs = self.config.images_split.join(self.product.clean_imgs(self.imgs))

        self.exc = {
            self._build_custom_field_name(key): (
                HTML.clean_text_field(value) if HTML.is_text_field(key) else value
            )
            for key, value in self.exc.items()
        }
        self.desc = HTML.clean_product_desc_str(self.desc)
        if isinstance(self.price, str):
            self.price = self.price.replace("$", "").replace("/ea", "").replace("/EA", "")
        elif not isinstance(self.price, (float, int)):
            SimTool.print(f"price 类型错误: {type(self.price)}, {self.url}")

    def _make_row_1(self):
        return {
            "Type": self.tye, "SKU": self.sku, "Name": self.name,
            "Description": self.desc, "Sale price": self.price,
            "Regular price": self.price, "Categories": self.cat,
            "Tags": self.tags, "Images": self.imgs,
            "Parent": self.parent,
        }

    def _make_row_2(self):
        return {"brand": self.brand, "Stock": self.stock,
                "is_upload": self.is_upload, 'url': self.url}

    def to_dic(self) -> dict:
        d = self._make_row_1()
        d.update(self._make_row_2())
        d.update(self.exc)
        return d


class ProductVariation(ProductSimple):
    """变体产品（多 SKU 子产品）"""

    def __init__(self, product, *, sku=None, attr=None, **kwargs):
        self.attr = attr
        super().__init__(product=product, sku=sku, tye='variation', **kwargs)

    def _make_sku_suffix(self) -> str:
        return "".join(f"_{v.upper().replace(' ', '_')}" for v in self.attr.values())

    def clean(self):
        super().clean()
        if not isinstance(self.attr, dict):
            raise TypeError(f"att 类型错误: {type(self.attr)},{self.attr} {self.url}")

        if self.sku is None:
            self.sku = self.name + self._make_sku_suffix()

    def to_dic(self) -> dict:
        d = self._make_row_1()
        if self.attr:
            for i, (k, v) in enumerate(
                self.attr.items() if isinstance(self.attr, dict) else self.attr,
                start=1,
            ):
                d[f"Attribute {i} name"] = k
                d[f"Attribute {i} value(s)"] = v
        d.update(self._make_row_2())
        d.update(self.exc)
        return d




