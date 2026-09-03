"""Small Storefront GraphQL client shared by the mg_shopify Steps."""

from __future__ import annotations

import html
import re
import threading


HEALTH_QUERY = """
query Health @inContext(country: COUNTRY_CODE, language: LANGUAGE_CODE) {
  shop { primaryDomain { url } }
}
"""


def clean_text(value: object) -> str:
    text = html.unescape(str(value or "")).replace("\\/", "/")
    text = text.replace("\u200b", "").replace("\ufeff", "")
    return re.sub(r"\s+", " ", text).strip()


class MgShopifySite:
    """Site-specific configuration interface for the mg Shopify Steps."""

    def storefront_settings(self) -> dict:
        """Return only values owned by the concrete Shopify site."""
        return {}


class StorefrontClient:
    """Discover and call a public Shopify Storefront GraphQL endpoint."""

    def __init__(
        self,
        tool,
        *,
        storefront_token: str | None = None,
        store_domain: str | None = None,
        api_version: str = "2023-07",
        country: str = "US",
        language: str = "EN",
    ):
        self.tool = tool
        self.storefront_token = clean_text(storefront_token)
        self.store_domain = clean_text(store_domain).lower()
        self.api_version = clean_text(api_version) or "2023-07"
        self.country = re.sub(r"[^A-Z]", "", clean_text(country).upper()) or "US"
        self.language = re.sub(r"[^A-Z]", "", clean_text(language).upper()) or "EN"
        self.api_url = ""
        self._lock = threading.Lock()

    @staticmethod
    def _extract_public_config(source: str) -> tuple[str, str]:
        decoded = html.unescape(source or "")
        domain_patterns = (
            r"Shopify\.shop\s*=\s*['\"]([^'\"]+\.myshopify\.com)['\"]",
            r"([A-Za-z0-9][A-Za-z0-9-]*\.myshopify\.com)",
        )
        token_patterns = (
            r"(?:window\.)?STOREFRONT_ACCESS_TOKEN\s*=\s*['\"]([^'\"]+)",
            r"PUBLIC_STOREFRONT_API_TOKEN.{0,100}?([A-Za-z0-9_-]{16,})",
            r"storefrontAccessToken.{0,120}?([A-Za-z0-9_-]{16,})",
            r"X-Shopify-Storefront-Access-Token.{0,100}?([A-Za-z0-9_-]{16,})",
        )
        domain = ""
        token = ""
        for pattern in domain_patterns:
            match = re.search(pattern, decoded, re.I | re.S)
            if match:
                domain = clean_text(match.group(1)).lower()
                break
        for pattern in token_patterns:
            match = re.search(pattern, decoded, re.I | re.S)
            if match:
                token = clean_text(match.group(1)).replace("\\", "")
                break
        return domain, token

    def context_query(self, query: str) -> str:
        return query.replace("COUNTRY_CODE", self.country).replace("LANGUAGE_CODE", self.language)

    def headers(self) -> dict[str, str]:
        return {
            "content-type": "application/json",
            "accept": "application/json",
            "x-shopify-storefront-access-token": self.storefront_token,
        }

    def _discover_credentials(self) -> None:
        # Discovery is only a fallback for sites that expose public values in
        # their HTML. Site-specific values should come from the Step hook.
        if self.storefront_token and self.store_domain:
            return
        response = self.tool.get(self.tool.config.base_url)
        if getattr(response, "status_code", 0) == 200:
            domain, token = self._extract_public_config(response.text)
            self.store_domain = self.store_domain or domain
            self.storefront_token = self.storefront_token or token

    def ensure_api(self) -> str:
        if self.api_url:
            return self.api_url
        with self._lock:
            if self.api_url:
                return self.api_url
            self._discover_credentials()
            if not self.storefront_token:
                raise RuntimeError("storefront_access_token_not_found")

            base_url = self.tool.config.base_url.rstrip("/")
            candidates = [f"{base_url}/api/{self.api_version}/graphql.json"]
            if self.store_domain:
                candidates.append(f"https://{self.store_domain}/api/{self.api_version}/graphql.json")
            payload = {"query": self.context_query(HEALTH_QUERY), "variables": {}}
            for candidate in dict.fromkeys(candidates):
                try:
                    response = self.tool.post(candidate, headers=self.headers(), json=payload)
                    if not 200 <= response.status_code < 300:
                        continue
                    body = response.json()
                    if not body.get("errors"):
                        self.api_url = candidate
                        return self.api_url
                except Exception:
                    continue
            raise RuntimeError("graphql_endpoint_not_found")

    def graphql(self, query: str, variables: dict | None = None) -> dict:
        response = self.tool.post(
            self.ensure_api(),
            headers=self.headers(),
            json={"query": self.context_query(query), "variables": variables or {}},
        )
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f"graphql_http_status:{response.status_code}")
        try:
            payload = response.json()
        except Exception as exc:
            raise RuntimeError("graphql_non_json") from exc
        if payload.get("errors"):
            raise RuntimeError(f"graphql_errors:{payload['errors']}")
        return payload.get("data") or {}
