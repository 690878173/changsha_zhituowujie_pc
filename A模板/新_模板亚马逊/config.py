from _ljp import Base_tool, Tool_config
# 请求头
headers = None
# cookie
cookies = None
# 重试次数
max_retry = None
# 超时时间
time_out = None

# NOTE =========

base_url =
site =
zk = 0.3

# NOTE =========

# 图片链接自带逗号时，使用此分割
images_split = None

# 字典需要携带自定义字段时，使用字段
custom_key = None

# 'shopify'
site_type = 'amazon'


browser = {
    "enabled": True,
    "backend": "drissionpage",
    "headless": False,
        "context_count": 1,
    "timeout": 30000,
    "stable_wait_ms": 500,
    "drission_options": {
        "arguments": ["--disable-blink-features=AutomationControlled"],
        "no_imgs": True,
        "auto_port": True,
    },
}

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
    browser=browser,
)
Tool: Base_tool = Base_tool(config)
