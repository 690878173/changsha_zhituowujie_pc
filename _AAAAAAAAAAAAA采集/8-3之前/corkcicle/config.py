from pathlib import Path

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://www.journelle.com/collections/lingerie",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}
cookies = None

base_path = Path('data')

max_retry = 3
time_out = 30

base_url = 'https://corkcicle.com'
base_site = 'corkcicle'

images_split = 'l---ljp---p'
product_zdy_zd_name = 'l___ljp___p'
site_type = 'shopify'

from all_base_f import Base_tool, Tool_config, ProductSimple, ProductVariation, Fc, zs

Tool = Base_tool(Tool_config(
    base_url=base_url,
    site=base_site,
    site_type=site_type,
    max_retry=max_retry,
    time_out=time_out,
    headers=headers,
    cookies=cookies,
))
