"""Magic Shopify Storefront GraphQL template Steps."""

from .get_detail import GetDetail
from .get_product import Get_Product
from .merge_link_variants import MergeLinkVariants
from .storefront import MgShopifySite
from .catalog import (
    ByltStreamParser,
    CatCol,
    HeaderInlineMenuParser,
    HydrogenHeaderParser,
    NextNavigationParser,
    StandardStreamParser,
    BaseCatalogParser,
    CatalogParser
)
from _ljp.mb.base import Collection, Replace_imgs, Shopify_dz, WpToShopify

__all__ = [
    "GetDetail",
    "Get_Product",
    "MergeLinkVariants",
    "MgShopifySite",
    "Replace_imgs",
    "WpToShopify",
    "Shopify_dz",
    "Collection",
    "CatCol",
    "HeaderInlineMenuParser",
    "HydrogenHeaderParser",
    "NextNavigationParser",
    "ByltStreamParser",
    "StandardStreamParser",
    'BaseCatalogParser',
    'CatalogParser'
]
