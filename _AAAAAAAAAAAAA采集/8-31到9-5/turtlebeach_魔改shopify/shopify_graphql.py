import requests
import time
import traceback

def crawl(url):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "X-Shopify-Storefront-Access-Token": "ef1b9f624c705ea7623f3c2b31924b44"
    }
    query = """
    query ProductByHandle($handle: String!) {
      product(handle: $handle) {
        id
        title
        description
        handle
        availableForSale
        productType
        vendor
        tags
        updatedAt
        seo {
          title
          description
        }
        featuredImage {
          url
          altText
          width
          height
        }
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
          maxVariantPrice {
            amount
            currencyCode
          }
        }
        
        metafields(
            identifiers: [
              {namespace: "custom", key: "ingredients_description"},
              {namespace: "custom", key: "product_ingredients"}
            ]
          ) {
            key
            namespace
            type
            value
          }
      
        options {
          id
          name
          values
        }
        images(first: 100) {
          nodes {
            url
            altText
            width
            height
          }
        }
        variants(first: 100) {
          nodes {
            id
            sku
            title
            availableForSale
            selectedOptions {
              name
              value
            }
            price {
              amount
              currencyCode
            }
            compareAtPrice {
              amount
              currencyCode
            }
            image {
              url
              altText
              width
              height
            }
          }
        }
      }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "handle": url
        }
    }
    retries = 3
    delay = 2
    request_url = 'https://turtle-beach-usa.myshopify.com/api/2023-07/graphql.json'
    for attempt in range(retries):
        try:
            response = requests.post(request_url, headers=headers, json=payload, timeout=30)
            print(response.status_code)
            print(response.json())
            response.close()
            if response.status_code == 200:
                return response
            else:
                time.sleep(delay)
                continue
        except Exception as e:
            print(f"请求失败: {e}. 尝试次数: {attempt + 1}/{retries}")
            print(traceback.print_exc())
            time.sleep(delay)
    return None

if __name__ == '__main__':
    handle = 'stealth-600-headset'
    crawl(handle)