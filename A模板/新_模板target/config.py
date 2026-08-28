from _ljp import Base_tool, Tool_config

base_url =
site =
zk = 0.3
site_type = 'target'
# Common request defaults used by all steps.
headers = {}
cookies = {}
max_retry = 3
time_out = 30
images_split = None
custom_key = None

browser = {
    "enabled": True,
    "backend": "drissionpage",
    "headless": False,
    "context_count": 3,
    "timeout": 30000,
    "stable_wait_ms": 500,
    "drission_options": {
        "arguments": ["--disable-blink-features=AutomationControlled", "--no-first-run"],
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
