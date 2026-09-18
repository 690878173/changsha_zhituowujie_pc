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

max_retry = None

time_out = None

# 去除尾部/
base_url = 'https://getcasely.com'

# 去除www和.com
base_site = 'getcasely'

zk =0.3
# 图片链接自带逗号时，使用此分割
images_split = ','

# 字典需要携带自定义字段时，使用字段
zdy_zd_name = 'l__ljp__p'

# 'shopify'
site_type = 'shopify'


from all_base_f import Base_tool,Tool_config,ProductSimple,ProductVariation,zs


config = Tool_config(
    base_url=base_url,
    site=base_site,
    zk=zk,
    site_type=site_type,
    max_retry=max_retry,
    time_out=time_out,
    headers=headers,
    cookies=cookies,
    custom_key=zdy_zd_name,
    images_split=images_split,
)

Tool = Base_tool(config)









