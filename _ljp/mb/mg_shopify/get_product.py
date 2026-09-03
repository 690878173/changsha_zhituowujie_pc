"""Storefront GraphQL product Step for magic Shopify templates."""

from __future__ import annotations

import time

from _ljp.mb.shopify.get_product import Get_Product as ShopifyGetProduct

from .storefront import MgShopifySite, StorefrontClient


PRODUCT_QUERY = """
query ProductByHandle($handle: String!) @inContext(country: COUNTRY_CODE, language: LANGUAGE_CODE) {
  product(handle: $handle) {
    id title description handle availableForSale productType vendor tags updatedAt
    seo { title description }
    featuredImage { url altText width height }
    priceRange {
      minVariantPrice { amount currencyCode }
      maxVariantPrice { amount currencyCode }
    }
    options { id name values }
    images(first: 100) { nodes { url altText width height } }
    variants(first: 100) {
      nodes {
        id sku title availableForSale selectedOptions { name value }
        price { amount currencyCode }
        compareAtPrice { amount currencyCode }
        image { url altText width height }
        mediaGallery: metafield(namespace: "custom", key: "media_gallery") {
          references(first: 100) {
            nodes { ... on MediaImage { image { url altText width height } } }
          }
        }
      }
    }
  }
}
"""


class Get_Product(MgShopifySite, ShopifyGetProduct):

    def __init__(self, *args, site_settings=None, **kwargs):
        super().__init__(*args, **kwargs)
        settings = dict(self.storefront_settings() or {})
        settings.update(site_settings or {})
        self.request_delay = max(0.0, float(settings.pop("request_delay", 0.0)))
        settings.pop("page_size", None)
        self.storefront = StorefrontClient(
            self.tool,
            **settings,
        )

    def product_query(self) -> str:
        return PRODUCT_QUERY

    def zdy_zd(self, url: str, html_text: str | None = None) -> dict:
        """Return site-only extra fields. Override in the external template."""
        return {}

    def fetch_product(self, url, category) -> list[dict]:
        try:
            page_response = self.tool.get(url)
            if page_response.status_code == 404:
                return []
            if not 200 <= page_response.status_code < 400:
                raise RuntimeError(f"页面请求状态码: {page_response.status_code}")

            page_url = getattr(page_response, "url", None) or url
            handle = self.tool.URL.get_handle(page_url)
            product = self.storefront.graphql(self.product_query(), {"handle": handle}).get("product")
            if not product:
                return []

            extra = self.zdy_zd(page_url, page_response.text)
            if extra is None:
                extra = {}
            if not isinstance(extra, dict):
                raise TypeError("zdy_zd 必须返回字典或 None")
            product[self.tool.custom_key] = extra
            product["__url"] = page_url
            if self.request_delay:
                time.sleep(self.request_delay)

            woo_product = self.mg_shopify_to_woocommerce(
                product,
                brand=self.tool.site,
                custom_categories=category,
            )
            products = [woo_product]
            products.extend(self.mg_create_variation_products(product, woo_product))
            return products
        except Exception as exc:
            self.tool.print(f"[ERROR] 接口请求失败:{url} 未知异常: {exc}")
            return []
