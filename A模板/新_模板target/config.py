"""Target site configuration. Change values here; do not edit the runner."""

from _ljp import Base_tool, Tool_config


base_url = "https://www.target.com"
site = "target"
zk = 0.8
site_type = None
# Common request defaults used by all steps.
headers = {}
cookies = {}
max_retry = 3
time_out = 30
images_split = ","
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

# Controls only the runner's order. Step-specific settings live in numbered scripts.
pipeline_steps = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

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
