from copy import deepcopy
from numbers import Real
from typing import Mapping
_DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.8,en;q=0.7",
    "cache-control": "no-cache", "pragma": "no-cache", "priority": "u=0, i",
    "referer": "https://www.journelle.com/collections/lingerie",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document", "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin", "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
}

_DEFAULT_COOKIES = {
    "localization": "US", "cart_currency": "USD",
    "_shopify_y": "dabb39cc-bc89-497c-b340-31b2ede021e3",
    "_shopify_analytics": ":AZp2O1QkAAEAHztC69G-yFNChK1vfflUWudV0AhpFiNR6FOoG0JYh1QIeFwE0AplJXKB:",
    "__kla_id": "eyJjaWQiOiJZelJsTnpnNFltSXRaV1ZqWlMwMFkyUTNMV0ppTW1FdFkyUTJNalUxTVdFNE5XWTMifQ==",
    "_dcid": "dcid.1.1762920201737.993685852", "_fbp": "fb.1.1762920201752.1616510929",
    "_gtmeec": "e30%3D", "_ga": "GA1.1.360526338.1762920202",
    "FPID": "FPID2.2.gkxOzZt5mIdu%2BjM%2FENk%2BINUWEC8WFAK8VJr7qv9DiMI%3D.1762920202",
    "FPAU": "1.2.1363690192.1762920202", "_clck": "8r5450%5E2%5Eg13%5E0%5E2142",
    "FPLC": "LgBR2ZulVErPIfYUSJlzshz28PHJYpcZjaf0ttgQ%2BOKvoX%2FTytpvBT1gw9f8w3Skoaoji%2FPT80R%2BxMChx7HVjW9Jmb0vQwpLwbP7lGJTdH2cpIAbSo3WEf43r4%2BDBA%3D%3D",
    "_shg_session_id": "ee3abf4f-7d71-4f24-b659-5c90de46503d",
    "_shg_user_id": "b36c7c32-f288-42a9-b521-223b4178e2b3",
    "wishlist_id": "165828310s5ibxs5m1i", "bookmarkeditems": "{\"items\":[]}",
    "wishlist_customer_id": "0", "lantern": "34e4017a-dcd0-44ea-86cc-510f559707fd",
    "_ks_scriptVersionChecked": "true", "_ks_userCountryUnit": "0",
    "_ks_countryCodeFromIP": "US",
    "_shopify_essential": ":AZp2O1QXAAEAvyFsaVJ70tJgji5ZeWCZ_YjgxwRXjGxAB3b5N-WHhSnud69tQW0MrpYjCka6b3GqbBhR9Uz4BhF9KODipC_2NFZRmCTQFTmhAMAjGv-jGy4tjy0FmTHMickaBcTQYB9gyNeGMX1T3ZL2JQ1P2sZLYPZwXL-juXGHSYiFqr2Gmc3jlKNMgPuEzv0pxSUVdolOYxCzcSwmJ_JEgKtrg_dwrLM_tp1SdVStXGVGDxfT27-4a1Fn6pKOttW0ZLW4JluB7XDeVv2VuUk-0l_ZIXlIrOu1450YtgeUvAjU3fGxv8SJbsptfgcU-GQ7NmT1Nravs3DmiiAUo2_zvYu9sk8dE3QuA-QodGbtyvFwsh4qzVoX5oLuEgUKhsFrxGP3Le-BVpm8PXsJjtIp7D18HUY:",
    "_clsk": "z0wknv%5E1763344068385%5E8%5E1%5Es.clarity.ms%2Fcollect",
    "_shopify_s": "73b24c0d-a8d4-4416-9886-da6ff48b97ce",
    "_uetsid": "94037020c35611f0b6b471d9a3ac75ef",
    "_uetvid": "8406dea0bf7c11f089889339b77b1953",
    "FPGSID": "1.1763343715.1763344093.G-QSD4N22KEF.mFsL74_ybyYhfff-E83nSQ",
    "_ga_QSD4N22KEF": "GS2.1.s1763343714$o2$g1$t1763344100$j51$l0$h694839178",
    "kiwi-sizing-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI4YTliMTk0ZC1iZmY3LTQ3OTktYjMwYS01Zjc1ZWZjMGVjMjIiLCJpYXQiOjE3NjMzNDQxNDYsImV4cCI6MTc2MzM0Nzc0Nn0.6kThd-lf6VF4L_1otBoH8nlTuH0z9Nw5nF0akbIs4UU",
    "keep_alive": "eyJ2IjoyLCJ0cyI6MTc2MzM0NDE5NDYzOSwiZW52Ijp7IndkIjowLCJ1YSI6MSwiY3YiOjEsImJyIjoxfSwiYmh2Ijp7Im1hIjo2NCwiY2EiOjAsImthIjowLCJzYSI6Mywia2JhIjowLCJ0YSI6MCwidCI6MTEyLCJubSI6MSwibXMiOjAuNjMsIm1qIjowLjMyLCJtc3AiOjAuMzUsInZjIjowLCJjcCI6MCwicmMiOjAsImtqIjowLCJraSI6MCwic3MiOjAuMDEsInNqIjowLjAxLCJzc20iOjEsInNwIjoxLCJ0cyI6MCwidGoiOjAsInRwIjowLCJ0c20iOjB9LCJzZXMiOnsicCI6NSwicyI6MTc2MzM0MzcwNDY0MSwiZCI6NDgzfX0%3D",
}

_CUSTOM_KEY = "j__ljp__p"

_IMAGE_SPLIT = "l__|__p"

_MAX_RETRY = 3

_TIMEOUT = 30

_IMPERSONATE_TARGET = "chrome120"

from .simtool import SimTool


class Tool_config:
    """Shared configuration for a crawler site with isolated mutable values."""

    def __init__(self, base_url, site, zk, site_type=None,
                 *, max_retry=None, time_out=None, headers=None, cookies=None,
                 custom_key=None, images_split=None, browser=None,
                 retry_statuses=None, retry_backoff=None):
        self.max_retry = _MAX_RETRY if max_retry is None else max_retry
        self.time_out = _TIMEOUT if time_out is None else time_out
        self.headers = self._copy_mapping(headers, _DEFAULT_HEADERS, 'headers')
        self.cookies = self._copy_mapping(cookies, _DEFAULT_COOKIES, 'cookies')
        self.custom_key = _CUSTOM_KEY if custom_key is None else custom_key
        self.images_split = _IMAGE_SPLIT if images_split is None else images_split
        self.browser = self._copy_mapping(browser, {}, 'browser')
        self.retry_statuses = tuple((429, 500, 502, 503, 504) if retry_statuses is None else retry_statuses)
        self.retry_backoff = {'base_seconds': 1.0, 'max_seconds': 30.0, 'jitter_seconds': 1.0}
        self.retry_backoff.update(self._copy_mapping(retry_backoff, {}, 'retry_backoff'))
        self.site_type = site_type
        self.zk = zk
        if not isinstance(base_url, str):
            raise TypeError('base_url must be a string.')
        base_url = base_url.strip().rstrip('/')
        self.base_url = base_url
        if not isinstance(site, str):
            raise TypeError('site must be a string.')
        site = site.strip()
        if site:
            site = site.replace("www.", "")
            if "." in site:
                site = site.split(".")[0]
        self.site = site
        self._validate()
        self.print()

    @staticmethod
    def _copy_mapping(value, default, name):
        if value is None:
            return deepcopy(default)
        if not isinstance(value, Mapping):
            raise TypeError(f'{name} must be a mapping.')
        return deepcopy(dict(value))

    def _validate(self):
        if not isinstance(self.max_retry, int) or isinstance(self.max_retry, bool) or self.max_retry < 1:
            raise ValueError('max_retry must be a positive integer.')
        if not isinstance(self.time_out, Real) or isinstance(self.time_out, bool) or self.time_out <= 0:
            raise ValueError('time_out must be greater than zero.')
        if not isinstance(self.zk, Real) or isinstance(self.zk, bool) or not 0 <= self.zk <= 1:
            raise ValueError('zk must be a number between 0 and 1.')
        if not self.retry_statuses or not all(
            isinstance(code, int) and not isinstance(code, bool) and 100 <= code <= 599
            for code in self.retry_statuses
        ):
            raise ValueError('retry_statuses must contain HTTP status integers.')
        for key in ('base_seconds', 'max_seconds', 'jitter_seconds'):
            value = self.retry_backoff.get(key)
            if not isinstance(value, Real) or isinstance(value, bool) or value < 0:
                raise ValueError(f'retry_backoff.{key} must be a non-negative number.')

    def print(self):
        SimTool.print(f'''
                ===================================
                使用的自定义字段:  {self.custom_key}
                使用的图片分隔符号:  {self.images_split}
                使用折扣: {self.zk}
                站点信息:{self.base_url} | {self.site_type}
                ===================================
                ''', color='green')
