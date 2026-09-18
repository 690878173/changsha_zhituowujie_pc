import os


# 请求头
headers = None
# cookie
cookies = None
# 重试次数
max_retry = None
# 超时时间
time_out = None

# NOTE =========

base_url = 'https://www.patagonia.com/'

site = 'patagonia'

zk = 0.3

# NOTE =========

# 图片链接自带逗号时，使用此分割
images_split = None

# 字典需要携带自定义字段时，使用字段
custom_key = None

# 'shopify'
site_type = None

# Patagonia 当前对直连/新建出口返回 Akamai 404；本机 Chrome 使用 Clash
# 的 HTTP 代理。可通过环境变量覆盖，避免把代理地址写死在采集逻辑中。
# browser_proxy = os.getenv('PATAGONIA_BROWSER_PROXY', 'http://127.0.0.1:7897').strip()
browser_proxy = None

from _ljp.base_tool import Base_tool,Tool_config


config = Tool_config(
    base_url=base_url,
    site=site,
    zk=zk,
    site_type=site_type,
    max_retry=max_retry,
    time_out=time_out,
    headers=headers,
    cookies=cookies,
    custom_key=custom_key,
    images_split=images_split,
    browser={
        'enabled': True,
        'backend': 'playwright',
        'headless': False,
        'context_count': 1,
        'timeout': 60000,
        'wait_until': 'domcontentloaded',
        'network_idle_timeout': 5000,
        'stable_wait_ms': 800,
        'launch_options': {
            'proxy': {'server': browser_proxy},
        } if browser_proxy else {},
    },
)

Tool = Base_tool(config)









