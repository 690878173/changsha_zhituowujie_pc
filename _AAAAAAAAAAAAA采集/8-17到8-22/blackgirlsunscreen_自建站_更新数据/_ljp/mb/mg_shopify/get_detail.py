"""Storefront GraphQL collection-to-product URL Step."""

from __future__ import annotations

import time
from urllib.parse import parse_qs, quote, unquote, urlencode, urlsplit

from _ljp.mb.base import GetDetail as BaseGetDetail
from _ljp.mb.model import PageModel

from .storefront import MgShopifySite, StorefrontClient, clean_text


COLLECTION_QUERY = """
query CollectionProducts($handle: String!, $first: Int!, $after: String)
@inContext(country: COUNTRY_CODE, language: LANGUAGE_CODE) {
  collection(handle: $handle) {
    products(first: $first, after: $after) {
      nodes { handle }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""


class GetDetail(MgShopifySite, BaseGetDetail):
    """Use Storefront GraphQL to paginate a standard Shopify collection URL.

    Site subclasses override ``storefront_settings()`` and return their own
    Storefront values. Override ``collection_query()`` for a non-standard API.
    """

    def __init__(self, *args, site_settings=None, **kwargs):
        super().__init__(*args, **kwargs)
        settings = dict(self.storefront_settings() or {})
        settings.update(site_settings or {})
        self.page_size = max(1, int(settings.pop("page_size", 250)))
        self.request_delay = max(0.0, float(settings.pop("request_delay", 0.5)))
        self.storefront = StorefrontClient(
            self.tool,
            **settings,
        )

    @staticmethod
    def collection_handle(url: object) -> str:
        parts = [unquote(part) for part in urlsplit(str(url or "")).path.split("/") if part]
        if len(parts) < 2 or parts[0].casefold() != "collections" or not parts[1]:
            return ""
        return clean_text(parts[1])

    @staticmethod
    def cursor_from_url(url: object) -> str:
        query = parse_qs(urlsplit(str(url or "")).query)
        return clean_text((query.get("after") or [""])[0])

    def collection_query(self) -> str:
        return COLLECTION_QUERY

    def before_request(self, page: PageModel):
        page.extra["collection_handle"] = self.collection_handle(page.url)

    def build_params(self, page: PageModel):
        return {
            "source": "mg-shopify-storefront-v1",
            "handle": page.extra.get("collection_handle") or self.collection_handle(page.url),
            "page": page.page,
            "first": self.page_size,
            "after": self.cursor_from_url(page.next_url),
        }

    def fetch_page(self, page: PageModel, params):
        handle = page.extra.get("collection_handle") or self.collection_handle(page.url)
        if not handle:
            page.set_end()
            return [], None
        try:
            connection = ((self.storefront.graphql(
                self.collection_query(),
                {"handle": handle, "first": self.page_size, "after": self.cursor_from_url(page.next_url) or None},
            ).get("collection") or {}).get("products") or {})
            product_urls = []
            seen = set()
            for product in connection.get("nodes") or []:
                handle_value = clean_text((product or {}).get("handle"))
                if not handle_value:
                    continue
                product_url = self.tool.URL.add_site(f"/products/{quote(handle_value)}")
                if product_url not in seen and product_url not in self.skip_output_url_ls:
                    seen.add(product_url)
                    product_urls.append(product_url)

            page_info = connection.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                page.set_end()
                return product_urls, None
            cursor = clean_text(page_info.get("endCursor"))
            if not cursor:
                page.set_fail()
                return [], None
            if self.request_delay:
                time.sleep(self.request_delay)
            return product_urls, f"{page.url.split('?', 1)[0]}?{urlencode({'after': cursor})}"
        except Exception as exc:
            self.tool.print(f"   [!] Storefront GraphQL 抓取失败: {page.url}: {exc}")
            page.set_fail()
            return [], None
