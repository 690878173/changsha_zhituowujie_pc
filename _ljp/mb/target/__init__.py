"""Target direct-API/direct-product crawler mode."""


from _ljp.mb.base import (Quchong,
                          Detail_QuChong,
                          Variable,
                          Replace_imgs,
                          WpToShopify,
                          Shopify_dz,
                          Collection,
                          download_new)
from .detail import GetDetail
from .product import Get_Product
__all__ = [
    "Detail_QuChong", "Quchong", "Variable", "Replace_imgs",
    "WpToShopify", "Shopify_dz", "Collection", "download_new",
    'GetDetail','Get_Product'
]
