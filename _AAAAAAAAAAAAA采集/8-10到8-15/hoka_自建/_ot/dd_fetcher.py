"""
DataDome 混合请求层。

思路：
  1. 用 DrissionPage 真实浏览器访问首页，让 DataDome 的 JS 跑完，拿到 `datadome` cookie；
  2. 把 cookie + UA + sec-ch-ua 交给 curl_cffi 会话（impersonate 伪装 TLS/HTTP2 指纹）批量请求；
  3. 一旦返回 403 / 挑战页，自动回到浏览器刷新凭证，再继续；
  4. 连续刷新仍失败的 URL，退回用浏览器直接导航（最慢但最稳）。

关键约束：
  - datadome cookie 与「出口 IP + UA + TLS 指纹」松绑定，所以浏览器和 curl_cffi
    必须走同一个代理/同一出口 IP，UA 也必须一致，否则 cookie 立刻失效。
  - impersonate 的 Chrome 版本应尽量贴近本机真实 Chrome 大版本号。
"""

import random
import re
import threading
import time

try:
    from curl_cffi import requests as cffi_requests
except ImportError:  # pragma: no cover
    cffi_requests = None

# 只在真正需要浏览器时才导入，避免没装 DrissionPage 也能用纯 cookie 模式
try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:  # pragma: no cover
    ChromiumPage = None
    ChromiumOptions = None


# -------------------- 拦截判定 --------------------

# DataDome 挑战页的窄标记。注意不要用裸的 "datadome"：
# 正常页面也内联了 DataDome 的 tag JS（js.datadome.co / ddjskey），会造成误判。
_BLOCK_MARKERS = (
    "captcha-delivery.com",
    "geo.captcha-delivery.com",
    "/interstitial/",
    "dd_cookie_test",
    "please enable js and disable any ad blocker",
)

# 正常 HOKA 产品详情页应当出现的标记（正向校验，比反向黑名单可靠）
_PRODUCT_MARKERS = (
    'property="og:title"',
    "data-pid=",
    '"longDescription"',
    "add-to-cart",
    'id="maincontent"',
)

# 请求 SFCC 的 XHR 控制器时应该用这套头，否则容易被判为异常导航
XHR_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def is_blocked(text, min_len=5000, hard_min=2000):
    """
    判断响应是否为 DataDome 挑战页 / 不完整页面。

    判定顺序：
      1. 空 -> 拦截；
      2. 命中窄标记 -> 拦截；
      3. 短于 hard_min -> 拦截（探测 JSON 端点时把 hard_min 调小）；
      4. 命中任一产品标记 -> 放行（正向校验优先于长度启发）；
      5. 其余按 min_len 兜底。
    """
    if not text:
        return True

    low = text.lower()

    for marker in _BLOCK_MARKERS:
        if marker in low:
            return True

    # DataDome 挑战页体积很小；正常 SFCC 详情页通常 >200KB。
    # 但 JSON 端点的正常响应也可能只有几百字节，所以 hard_min 要可调。
    if len(text) < hard_min:
        return True

    for marker in _PRODUCT_MARKERS:
        if marker.lower() in low:
            return False

    return len(text) < min_len


# -------------------- 指纹版本对齐 --------------------

# curl_cffi 提供的 Chrome 伪装档位（按版本升序）。
# 不同 curl_cffi 版本支持的档位不同，若所选档位不可用，
# DataDomeFetcher._new_session 会在建会话时捕获异常并退回通用 "chrome"。
_CHROME_TARGETS = [
    (99, "chrome99"), (100, "chrome100"), (101, "chrome101"), (104, "chrome104"),
    (107, "chrome107"), (110, "chrome110"), (116, "chrome116"), (119, "chrome119"),
    (120, "chrome120"), (123, "chrome123"), (124, "chrome124"), (131, "chrome131"),
    (133, "chrome133a"), (136, "chrome136"),
]


def pick_impersonate(user_agent, fallback="chrome124"):
    """
    根据真实浏览器 UA 的 Chrome 大版本，挑选最接近的 impersonate 档位。

    这一步很重要：impersonate 会自动生成 sec-ch-ua 头，如果它声明的是
    Chrome 131 而 UA 里写的是 Chrome 140，UA 与客户端提示就自相矛盾，
    是很明显的自动化特征。
    """
    m = re.search(r"Chrome/(\d+)", user_agent or "")
    if not m:
        return fallback

    major = int(m.group(1))
    chosen = fallback
    for ver, name in _CHROME_TARGETS:
        if ver <= major:
            chosen = name
        else:
            break
    return chosen


# -------------------- 浏览器凭证采集 --------------------

class BrowserCredentialSource:
    """
    用真实浏览器跑完 DataDome 的 JS 挑战，产出可复用的 cookie / 请求头。

    浏览器实例常驻：cookie 过期时只需重新导航一次，不必反复启停 Chrome。
    """

    def __init__(self, home_url="https://www.hoka.com/en/us/", headless=False,
                 proxy=None, warmup_wait=6.0):
        self.home_url = home_url
        self.headless = headless
        self.proxy = proxy
        self.warmup_wait = warmup_wait
        self.page = None
        self._lock = threading.Lock()

    def _ensure_page(self):
        if self.page is not None:
            return

        if ChromiumOptions is None:
            raise RuntimeError("未安装 DrissionPage，无法采集 cookie：pip install DrissionPage")

        co = ChromiumOptions()
        if self.headless:
            # 注意：DataDome 对 headless 检测较严，建议保持 False
            co.headless(True)
        else:
            co.headless(False)
        co.set_argument("--no-first-run")
        co.set_argument("--no-default-browser-check")
        co.set_argument("--disable-blink-features=AutomationControlled")
        if self.proxy:
            # 浏览器与 curl_cffi 必须同一出口 IP，否则 datadome cookie 立即失效
            co.set_proxy(self.proxy)

        self.page = ChromiumPage(co)

    def _collect_cookies(self):
        """
        兼容不同 DrissionPage 版本的 cookies() 返回值：
        4.x 返回 CookiesList（元素为 dict，另有 as_dict()），3.x 可能直接返回 dict。
        """
        raw = self.page.cookies()

        as_dict = getattr(raw, "as_dict", None)
        if callable(as_dict):
            try:
                return dict(as_dict())
            except Exception:
                pass

        if isinstance(raw, dict):
            return dict(raw)

        out = {}
        try:
            for c in raw:
                if isinstance(c, dict) and "name" in c:
                    out[c["name"]] = c.get("value", "")
        except TypeError:
            pass
        return out

    def refresh(self, url=None):
        """
        导航一次并等待 DataDome 通过，返回 (cookies dict, headers dict)。
        若页面仍是挑战页，会留时间给人工过验证码。
        """
        with self._lock:
            self._ensure_page()
            target = url or self.home_url
            self.page.get(target)
            time.sleep(self.warmup_wait)

            # 挑战页时给足人工/自动过验证的时间
            for i in range(20):
                html = self.page.html
                if not is_blocked(html):
                    break
                if i == 0:
                    print("[DD] 检测到挑战页，等待验证通过（可手动点选验证码）...")
                time.sleep(3)

            ua = self.page.run_js("return navigator.userAgent;")
            cookies = self._collect_cookies()

            headers = {
                "User-Agent": ua,
                "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
                           "image/avif,image/webp,image/apng,*/*;q=0.8"),
                "Accept-Language": "en-US,en;q=0.9",
                # 不设置 Accept-Encoding：交给 curl 自己协商，避免声明 br
                # 却无法解压导致 resp.text 变成乱码
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Referer": target,
            }
            return cookies, headers

    def get_html(self, url, wait=3.0):
        """兜底通道：直接用浏览器导航取 HTML。"""
        with self._lock:
            self._ensure_page()
            self.page.get(url)
            time.sleep(wait)
            html = self.page.run_js("return document.documentElement.outerHTML;")
            return html or self.page.html

    def close(self):
        if self.page is not None:
            try:
                self.page.quit()
            except Exception:
                pass
            self.page = None


# -------------------- 混合抓取器 --------------------

class DataDomeFetcher:
    """
    对外只暴露 fetch(url) -> (html, error)。

    内部策略：curl_cffi 主通道 -> 凭证刷新 -> 浏览器兜底。
    """

    def __init__(self, home_url="https://www.hoka.com/en/us/", impersonate="auto",
                 proxy=None, headless=False, timeout=30, max_retries=3,
                 delay_range=(0.8, 2.2), browser_fallback=True):
        # "auto" = 从真实浏览器 UA 自动对齐 Chrome 版本档位
        self.impersonate = impersonate
        self.proxy = proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_range = delay_range
        self.browser_fallback = browser_fallback

        self.source = BrowserCredentialSource(home_url=home_url, headless=headless,
                                             proxy=proxy)
        self.session = None
        self.active_impersonate = None
        self.refresh_count = 0
        self.cffi_ok = 0
        self.browser_ok = 0

    def _proxies(self):
        if not self.proxy:
            return None
        return {"http": self.proxy, "https": self.proxy}

    def _new_session(self, impersonate):
        """创建会话；若该 impersonate 档位不被当前 curl_cffi 支持，退回默认档位。"""
        if cffi_requests is None:
            raise RuntimeError("未安装 curl_cffi：pip install curl_cffi")
        try:
            return cffi_requests.Session(
                impersonate=impersonate,
                proxies=self._proxies(),
                timeout=self.timeout,
            ), impersonate
        except Exception as e:
            print(f"[DD] impersonate='{impersonate}' 不可用({e})，退回 'chrome'")
            return cffi_requests.Session(
                impersonate="chrome",
                proxies=self._proxies(),
                timeout=self.timeout,
            ), "chrome"

    def refresh_session(self, url=None):
        """重新拿一份 cookie，重建 curl_cffi 会话。"""
        cookies, headers = self.source.refresh(url)
        dd = cookies.get("datadome")

        # 让 TLS 指纹的 Chrome 版本与真实 UA 对齐，避免 UA / sec-ch-ua 自相矛盾
        target = self.impersonate
        if target == "auto":
            target = pick_impersonate(headers.get("User-Agent", ""))

        print(f"[DD] 凭证已刷新，datadome cookie: {'有' if dd else '无'}"
              f"（共 {len(cookies)} 个 cookie），impersonate={target}")

        if self.session is not None:
            try:
                self.session.close()
            except Exception:
                pass

        self.session, self.active_impersonate = self._new_session(target)
        self.session.headers.update(headers)
        for k, v in cookies.items():
            self.session.cookies.set(k, v, domain=".hoka.com")

        self.refresh_count += 1

    def _sync_cookie_from_response(self, resp):
        """DataDome 会在响应里轮换 cookie，取回来写入会话。"""
        try:
            new_dd = resp.cookies.get("datadome")
            if new_dd:
                self.session.cookies.set("datadome", new_dd, domain=".hoka.com")
        except Exception:
            pass

    def fetch(self, url, referer=None, hard_min=2000, min_len=5000,
              browser_fallback=None, extra_headers=None):
        """
        返回 (html, error)。成功时 error 为 None。

        hard_min / min_len: 传给 is_blocked 的长度阈值。抓整页 HTML 用默认值；
            探测 JSON 端点时两者都要调小（如 hard_min=40, min_len=60），
            否则正常的小体积 JSON 响应会被误判为拦截。
        extra_headers: 覆盖/追加请求头。请求 XHR 端点时传 XHR_HEADERS。
        """
        if self.session is None:
            self.refresh_session()

        use_fallback = self.browser_fallback if browser_fallback is None else browser_fallback

        for attempt in range(self.max_retries):
            time.sleep(random.uniform(*self.delay_range))
            try:
                headers = {}
                if referer:
                    headers["Referer"] = referer
                if extra_headers:
                    headers.update(extra_headers)
                resp = self.session.get(url, headers=headers or None,
                                        allow_redirects=True, timeout=self.timeout)
                self._sync_cookie_from_response(resp)

                blocked = is_blocked(resp.text, min_len=min_len, hard_min=hard_min)
                if resp.status_code in (403, 429) or blocked:
                    print(f"[DD] 主通道被拦截 (HTTP {resp.status_code}, "
                          f"{len(resp.text or '')} bytes)，第 {attempt + 1} 次")
                    if attempt < self.max_retries - 1:
                        # 凭证很可能已失效，回浏览器重新过一遍挑战
                        self.refresh_session(url)
                        continue
                    break

                self.cffi_ok += 1
                return resp.text, None

            except Exception as e:
                print(f"[DD] 请求异常: {type(e).__name__}: {e}（第 {attempt + 1} 次）")
                if attempt < self.max_retries - 1:
                    time.sleep(random.uniform(2, 5) * (attempt + 1))
                    continue

        # 兜底：浏览器直接导航
        if use_fallback:
            try:
                html = self.source.get_html(url)
                if html and not is_blocked(html, min_len=min_len, hard_min=hard_min):
                    self.browser_ok += 1
                    # 顺便把浏览器新拿到的 cookie 同步回会话
                    try:
                        self.refresh_session()
                    except Exception:
                        pass
                    return html, None
                return None, "DataDome 拦截（浏览器兜底也未通过）"
            except Exception as e:
                return None, f"浏览器兜底失败: {e}"

        return None, "DataDome 拦截（已达最大重试次数）"

    def stats(self):
        return (f"curl_cffi 成功={self.cffi_ok}, 浏览器兜底成功={self.browser_ok}, "
                f"凭证刷新={self.refresh_count}, impersonate={self.active_impersonate}")

    def close(self):
        if self.session is not None:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None
        self.source.close()
