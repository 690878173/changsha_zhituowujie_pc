from _ljp.base_tool import Base_tool, Tool_config


base_url = 'https://www.asics.com/us/en-us/'
site = 'asics'
zk = 0.3

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'user-agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/151.0.0.0 Safari/537.36'
    ),
}

# 验证 Cookie 只对当前浏览器会话有效，由可见浏览器完成验证后自动生成。
# 不要把上一次运行中已过期的 Cookie 写入配置。
cookies = {'user_country': 'US'}

config = Tool_config(
    base_url=base_url,
    site=site,
    zk=zk,
    max_retry=3,
    time_out=60,
    headers=headers,
    cookies=cookies,
    browser={
        'enabled': True,
        'headless': False,
        'context_count': 1,
        # FingerprintKit injects a Mac platform into this Windows Chrome
        # session while leaving its Windows UA intact; ASICS rejects it.
        'fingerprint_enabled': False,
        'context_options': {
            'locale': 'en-US',
        },
        'launch_options': {
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--no-default-browser-check',
            ],
        },
        'wait_until': 'domcontentloaded',
        'timeout': 60000,
        'network_idle_timeout': 8000,
        'stable_wait_ms': 1200,
    },
)

Tool = Base_tool(config)
