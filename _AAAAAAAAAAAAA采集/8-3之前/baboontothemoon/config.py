

headers = None
cookies = None

max_retry = 3
time_out = 30

base_url = 'https://baboontothemoon.com'
base_site = 'baboontothemoon'

images_split = 'l---ljp---p'
zdy_zd_name = 'l__ljp__p'
zk = 0.3
site_type = 'shopify'

from _ljp.base_tool import Base_tool, Tool_config

Tool = Base_tool(Tool_config(
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
))
