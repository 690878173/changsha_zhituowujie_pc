from __future__ import annotations

import os
from pathlib import Path
import subprocess

import threading
import time
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from curl_cffi import requests as curl_requests
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from A_3_get_product_data import (
    CUSTOM_FIELD_NAMES,
    Pc,
    Tool,
    input_file,
    output_file,
    fail_file,
    catch_path,
    index_path,
    output_ts_file,
    skip_input_url_ls,
    skip_output_url_ls,
    ts_num,
    fieldnames,
)


_FETCH_SCRIPT = """async ({url, timeout}) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(url, {credentials: 'include', signal: controller.signal});
        const headers = {};
        response.headers.forEach((value, key) => { headers[key] = value; });
        return {url: response.url, status: response.status, headers, body: await response.text()};
    } finally {
        clearTimeout(timer);
    }
}"""



cookies = {
    'dwanonymous_aa4135988320dfd11a2574fc0fe760c4': 'bcKCjxG2W3S0lHXAD8AK9a6AsW',
    'pat_web_scope_id': 'patagonia',
    '__kla_id': 'eyJjaWQiOiJabVF4TVRJMU4ySXROell3TWkwMFl6UXhMVGc0T0dFdFpEUTVZelJrTkdWaU1XUmwifQ==',
    '_gcl_au': '1.1.1102640572.1787377186',
    '_ga': 'GA1.1.1739459406.1787377186',
    '_pin_unauth': 'dWlkPVpUY3pZVE16TWpJdFl6YzJZaTAwWXpBM0xXRXlNRGN0TURObU9EUTNOelJsTlRjMA',
    'bm': '5936f3bf-f7c2-4758-9dc1-47eb73576763',
    'OptanonAlertBoxClosed': '2026-08-22T05:39:48.402Z',
    'dwsid': '_cJboxYNe_bApz-sRddDXrjQA_hCrII1F6qAAljHIRv4toxMENR-MStN1XHdlrIjEb9gC-ATr7oAomI70kU1sg==',
    'dwac_8cd9b022d7269f392c1ffcd8ea': 'wcS00mmdFYS_san7H7M-AYTW7Ik9POxHaLw%3D|dw-only|||USD|false|US%2FPacific|true',
    'cqcid': 'bcKCjxG2W3S0lHXAD8AK9a6AsW',
    'cquid': '||',
    'sid': 'wcS00mmdFYS_san7H7M-AYTW7Ik9POxHaLw',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    '__kla_off': 'false',
    'ak_bmsc': 'BF07DA2404656B618955B308F49B0C6B~000000000000000000000000000000~YAAQSQ7SF3M96jugAQAAFhdqVwGw40i1D6UieNuiT4+KOA1C9l+Rm3nLD0KgT2nKl8O2Ak7iC+6OuyB8RR9OIVlJK9U6ijkdAGLk4/JodKWO4AmIOUxsRZG6yQdToT7dthOwqBOOUzL11goCPp3aIwX/sl646hsF5nfFZiehoUpKA/C2N2rsqHA63R+KCsEbfvQtGO/TzV4hAioRDR2nhGIPHrKQ99nytgPstHZUdruTD64PJQ+n1kVJIf/ncHpLEhd8QPdcpyhiFFkdUh9h78Y1/S+AB3pYm8xbCnQsJwars5vqFXSgDUQS107eK1hT5+wJPzzjAkpGMy7fEfMr0wFv6YBP2J+ggvgFuFgWcrE7Hmnlz9aO8z/atX71NE22rOiOIHeL3YrMuGiTqEwB',
    'bm_lso': '15EF624A3774E21667F5EB5B4A60ADE9A71961C072AEAC1067B7556FCDAFA5BC~YAAQSQ7SF0pw6jugAQAAfMBrVwh8vHmROF6iivGRw3gg6M42Q7tXrj2x6FhhicGo2Z3GiSWf4JxxiNNpm1mLl21s9g2k5GYsFZKxFS3DAKmmlARsP8M7qkUUV5cIuE2lTYIwEY9CWwotF6AX51Q1hQaTyQ//owQ2E3te7pM+7NLYA0NAXpuDv7q7v1TlUY2x8gGazb8JLatco0X7bjBlm9PKMjOfk6p3sT5kdRcPbPCkaj4JwM99ReI8mdWgB1FsG+o+1J06QQ+XKmqV7B4w2APFfDuwsuGlyblH8ZJJwuUlfYEwXO7eZM2lzDJAHQ143XIFmlcSyp1SFUOCDTW72YhvEf27Z6TSn3ZK/dNnGr9Lfz+1Je8XdNU+9V44q1HytS6F4q+x/KbwMgEkTHk3TYPqd3z8HEzhiTx1yjOrMkpM+RDuyDLgTm2pmMGnrM+QuNIK2bSKTihcWTvyI8hcN0m97BjI~1788173078621',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Mon+Aug+31+2026+18%3A44%3A55+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=1c723ea2-05dc-46fc-8988-3839798d4840&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1%2CC0005%3A1&intType=3&geolocation=US%3BCA&AwaitingReconsent=false',
    'bm_so': 'F67031050D00909B9866E7B3EDA37F2CD45C69C4564025DFD9A0CF061DBBC344~YAAQSQ7SF8ZY7DugAQAAPZV7VwjB+DOefV7AyRsF36SCgp3zPWp5NKP4cd/7+nNh8kTaStz2ylEyzKRkCG2aCEDwvzT1Xmn2jcfOyLkU3C2agceYtcZA8j933errzj8oeYqiLkLLyUZhrJQR1XaN/pnKB7IiM2ifJ5bthczJiN1cCBImAl2VsG3ZZsTYgQMUbd1Hvygq9koKMwMWLs2wXIbCL8maidGD9EfjLFQWM9ndvj0dDXAe6JGwcXbGLMy7EpTqigeb4+R72xudKeeffAHWU2hBhE49X3/0z69x5LGdXtVCpgUxjXbjtK+q77VKFn7BaLHBTDMaLeaepGGJuLZy1FcTJrdiFT8hp/LgyjSgMI2oKH+NGPJ5YoED2FC9RZgXqvVWaQfjpz2tgz+KUCZLzqOIz9wtKYWHa8h1JuxUB0+AX9fEJarPwmqaL0OAW4NiGl02gQWtAWqezV80C95UB/Yu',
    '_ga_1SYPSJZYJ5': 'GS2.1.s1788172965$o7$g1$t1788174111$j60$l0$h0',
    'bm_s': 'YAAQbQ7SF43MpSKgAQAAUON7VwbYSwO3B4YQIrS8fEuKNfYvAVOQspLqwsSiLMXw2BdNmMrC/unJ/t/Vl3tVWpVNRSoK+DY9+4nqVIeXoUnok4acrhPSAc3ehMApz0XAch5vSpAcALAVYqR4ciPiem4TOHQvrSYZkW3E3TqjDIPRPSHTn4+KxczzTWQH6JE0K1S9VzP2u8dinjoD6R1hTCA+hWTBXx97kVpzBCSLV2w67X5PeXe6fyZPI0CVXtEmrU4tPL/I0R5PSXFuTw49/7AWXVt4LyC61cNJcnKSex+PJutoBNrSMTgoNM9xTTg221qjoEukP2YbO17buxWIsJd8I0HB9zXdMX6TgiLT16YYrYrp+3BuYwlUNxMav7U0TO9+AseAIAU+vnHujc7+ix4Bj/tO5AD2T9pzu40AmE8DnABucfCoOkxzSlkL63vV3bwMeXhZKdULylP6C91jueSKabtiadX8B8Iljh49jyIFDB9hECzgLEXDTamElziu0jJuOHToD129psybMYtc9hXbKGGV89R5Z/b873uLTERxYLEefWNr8efmmOBDNDgjH506L0k9t78ZLjED4I/8XDQVNrfkiTBx8RIrUiP7ojQ1rOvVcgBOPzNhutqS6bxdqUEU3EP3zajHa/P1KHJV+fCiokG6VafqtTtFlwMIl2JFQNS5Lfp8hU7lOIGQnmZczhqPeQSS1Z8KpFyZ+h9f0su5wsFnN9yPCdWAmo/+R+DIDZ0VZLaFtlnAc64vTcHTrmc0SYdsu0vTsovcLT5v1JJJPG0wwkWoIlGmQN296HbRL5ZQJfQ/gT4PSfxTBCP9V7F2tAeAS7OyPT349sN2Ndh1t64xiuretnbse1YIq0UfgDdnMCQGf8jspozGdqUFAP3PpLdg7F3bazzoDOV+FRZC75Qljl3d9/CrnyrtXoen7iJINGWPGXDweMIC7y52Tn3neDYCMo7uFlwee2SPULNXOiKYiOLWGJjzIOKeLf24qkdf2k9Y45lA66HwQntnpZNCH9wEUcK9X3VXkP8n+f7ZL4okXFk6KEDpGFH0o7VB3gDNVS8h5t4EvZ+kInBgFneFFSLYv2XhiPuZ/CEHN9tRFmV5HaI9fBTfvlYe2Lc=',
    'bm_sv': '2136C728D895F5754DD3BBAA30F07A57~YAAQbQ7SF5jMpSKgAQAAXOV7VwHDJdwW0qdNMxpIm6XenIAz8Zwk/liza17U5VXnpi1LgWc9Aw63tFZ8jz85s4djB6wbBWzRv47d5gTR3h6MXKKojRneoo9vZQtv+BtiUnB0DCTQVakzX6CseF//kF8D90QPkQDWvjn7XL/SDOpy50uvSg2zHgFyUrvKVQH64A66MAHW6omI8F0DPqFmHcJIAm+EwzkVnuyymLSPdU0EJUoca4jg8ziOGfKxG7bCUauF+g==~1',
    '_br_uid_2': 'uid%3D9083764294322%3Av%3D17.0%3Ats%3D1787377185280%3Ahc%3D28',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'dwanonymous_aa4135988320dfd11a2574fc0fe760c4=bcKCjxG2W3S0lHXAD8AK9a6AsW; pat_web_scope_id=patagonia; __kla_id=eyJjaWQiOiJabVF4TVRJMU4ySXROell3TWkwMFl6UXhMVGc0T0dFdFpEUTVZelJrTkdWaU1XUmwifQ==; _gcl_au=1.1.1102640572.1787377186; _ga=GA1.1.1739459406.1787377186; _pin_unauth=dWlkPVpUY3pZVE16TWpJdFl6YzJZaTAwWXpBM0xXRXlNRGN0TURObU9EUTNOelJsTlRjMA; bm=5936f3bf-f7c2-4758-9dc1-47eb73576763; OptanonAlertBoxClosed=2026-08-22T05:39:48.402Z; dwsid=_cJboxYNe_bApz-sRddDXrjQA_hCrII1F6qAAljHIRv4toxMENR-MStN1XHdlrIjEb9gC-ATr7oAomI70kU1sg==; dwac_8cd9b022d7269f392c1ffcd8ea=wcS00mmdFYS_san7H7M-AYTW7Ik9POxHaLw%3D|dw-only|||USD|false|US%2FPacific|true; cqcid=bcKCjxG2W3S0lHXAD8AK9a6AsW; cquid=||; sid=wcS00mmdFYS_san7H7M-AYTW7Ik9POxHaLw; __cq_dnt=0; dw_dnt=0; __kla_off=false; ak_bmsc=BF07DA2404656B618955B308F49B0C6B~000000000000000000000000000000~YAAQSQ7SF3M96jugAQAAFhdqVwGw40i1D6UieNuiT4+KOA1C9l+Rm3nLD0KgT2nKl8O2Ak7iC+6OuyB8RR9OIVlJK9U6ijkdAGLk4/JodKWO4AmIOUxsRZG6yQdToT7dthOwqBOOUzL11goCPp3aIwX/sl646hsF5nfFZiehoUpKA/C2N2rsqHA63R+KCsEbfvQtGO/TzV4hAioRDR2nhGIPHrKQ99nytgPstHZUdruTD64PJQ+n1kVJIf/ncHpLEhd8QPdcpyhiFFkdUh9h78Y1/S+AB3pYm8xbCnQsJwars5vqFXSgDUQS107eK1hT5+wJPzzjAkpGMy7fEfMr0wFv6YBP2J+ggvgFuFgWcrE7Hmnlz9aO8z/atX71NE22rOiOIHeL3YrMuGiTqEwB; bm_lso=15EF624A3774E21667F5EB5B4A60ADE9A71961C072AEAC1067B7556FCDAFA5BC~YAAQSQ7SF0pw6jugAQAAfMBrVwh8vHmROF6iivGRw3gg6M42Q7tXrj2x6FhhicGo2Z3GiSWf4JxxiNNpm1mLl21s9g2k5GYsFZKxFS3DAKmmlARsP8M7qkUUV5cIuE2lTYIwEY9CWwotF6AX51Q1hQaTyQ//owQ2E3te7pM+7NLYA0NAXpuDv7q7v1TlUY2x8gGazb8JLatco0X7bjBlm9PKMjOfk6p3sT5kdRcPbPCkaj4JwM99ReI8mdWgB1FsG+o+1J06QQ+XKmqV7B4w2APFfDuwsuGlyblH8ZJJwuUlfYEwXO7eZM2lzDJAHQ143XIFmlcSyp1SFUOCDTW72YhvEf27Z6TSn3ZK/dNnGr9Lfz+1Je8XdNU+9V44q1HytS6F4q+x/KbwMgEkTHk3TYPqd3z8HEzhiTx1yjOrMkpM+RDuyDLgTm2pmMGnrM+QuNIK2bSKTihcWTvyI8hcN0m97BjI~1788173078621; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Aug+31+2026+18%3A44%3A55+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=1c723ea2-05dc-46fc-8988-3839798d4840&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1%2CC0005%3A1&intType=3&geolocation=US%3BCA&AwaitingReconsent=false; bm_so=F67031050D00909B9866E7B3EDA37F2CD45C69C4564025DFD9A0CF061DBBC344~YAAQSQ7SF8ZY7DugAQAAPZV7VwjB+DOefV7AyRsF36SCgp3zPWp5NKP4cd/7+nNh8kTaStz2ylEyzKRkCG2aCEDwvzT1Xmn2jcfOyLkU3C2agceYtcZA8j933errzj8oeYqiLkLLyUZhrJQR1XaN/pnKB7IiM2ifJ5bthczJiN1cCBImAl2VsG3ZZsTYgQMUbd1Hvygq9koKMwMWLs2wXIbCL8maidGD9EfjLFQWM9ndvj0dDXAe6JGwcXbGLMy7EpTqigeb4+R72xudKeeffAHWU2hBhE49X3/0z69x5LGdXtVCpgUxjXbjtK+q77VKFn7BaLHBTDMaLeaepGGJuLZy1FcTJrdiFT8hp/LgyjSgMI2oKH+NGPJ5YoED2FC9RZgXqvVWaQfjpz2tgz+KUCZLzqOIz9wtKYWHa8h1JuxUB0+AX9fEJarPwmqaL0OAW4NiGl02gQWtAWqezV80C95UB/Yu; _ga_1SYPSJZYJ5=GS2.1.s1788172965$o7$g1$t1788174111$j60$l0$h0; bm_s=YAAQbQ7SF43MpSKgAQAAUON7VwbYSwO3B4YQIrS8fEuKNfYvAVOQspLqwsSiLMXw2BdNmMrC/unJ/t/Vl3tVWpVNRSoK+DY9+4nqVIeXoUnok4acrhPSAc3ehMApz0XAch5vSpAcALAVYqR4ciPiem4TOHQvrSYZkW3E3TqjDIPRPSHTn4+KxczzTWQH6JE0K1S9VzP2u8dinjoD6R1hTCA+hWTBXx97kVpzBCSLV2w67X5PeXe6fyZPI0CVXtEmrU4tPL/I0R5PSXFuTw49/7AWXVt4LyC61cNJcnKSex+PJutoBNrSMTgoNM9xTTg221qjoEukP2YbO17buxWIsJd8I0HB9zXdMX6TgiLT16YYrYrp+3BuYwlUNxMav7U0TO9+AseAIAU+vnHujc7+ix4Bj/tO5AD2T9pzu40AmE8DnABucfCoOkxzSlkL63vV3bwMeXhZKdULylP6C91jueSKabtiadX8B8Iljh49jyIFDB9hECzgLEXDTamElziu0jJuOHToD129psybMYtc9hXbKGGV89R5Z/b873uLTERxYLEefWNr8efmmOBDNDgjH506L0k9t78ZLjED4I/8XDQVNrfkiTBx8RIrUiP7ojQ1rOvVcgBOPzNhutqS6bxdqUEU3EP3zajHa/P1KHJV+fCiokG6VafqtTtFlwMIl2JFQNS5Lfp8hU7lOIGQnmZczhqPeQSS1Z8KpFyZ+h9f0su5wsFnN9yPCdWAmo/+R+DIDZ0VZLaFtlnAc64vTcHTrmc0SYdsu0vTsovcLT5v1JJJPG0wwkWoIlGmQN296HbRL5ZQJfQ/gT4PSfxTBCP9V7F2tAeAS7OyPT349sN2Ndh1t64xiuretnbse1YIq0UfgDdnMCQGf8jspozGdqUFAP3PpLdg7F3bazzoDOV+FRZC75Qljl3d9/CrnyrtXoen7iJINGWPGXDweMIC7y52Tn3neDYCMo7uFlwee2SPULNXOiKYiOLWGJjzIOKeLf24qkdf2k9Y45lA66HwQntnpZNCH9wEUcK9X3VXkP8n+f7ZL4okXFk6KEDpGFH0o7VB3gDNVS8h5t4EvZ+kInBgFneFFSLYv2XhiPuZ/CEHN9tRFmV5HaI9fBTfvlYe2Lc=; bm_sv=2136C728D895F5754DD3BBAA30F07A57~YAAQbQ7SF5jMpSKgAQAAXOV7VwHDJdwW0qdNMxpIm6XenIAz8Zwk/liza17U5VXnpi1LgWc9Aw63tFZ8jz85s4djB6wbBWzRv47d5gTR3h6MXKKojRneoo9vZQtv+BtiUnB0DCTQVakzX6CseF//kF8D90QPkQDWvjn7XL/SDOpy50uvSg2zHgFyUrvKVQH64A66MAHW6omI8F0DPqFmHcJIAm+EwzkVnuyymLSPdU0EJUoca4jg8ziOGfKxG7bCUauF+g==~1; _br_uid_2=uid%3D9083764294322%3Av%3D17.0%3Ats%3D1787377185280%3Ahc%3D28',
}


class ProfileBlockedError(RuntimeError):
    """The current Chrome profile has been rejected by the target site."""


class AllProfilesBlockedError(RuntimeError):
    """Every configured Chrome profile has been rejected in this run."""


class AttachedChrome:
    """Connect to Chrome over CDP and rotate among independent profiles."""

    def __init__(
        self,
        endpoint: str = 'http://127.0.0.1:9222',
        executable_path: str = r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        user_data_dir: str | None = None,
        user_data_dirs: tuple[str, ...] | list[str] | None = None,
        profile_port_offsets: tuple[int, ...] | list[int] | None = None,
        cycle_profiles: bool = True,
        cycle_cooldown_seconds: float = 300.0,
        max_failed_profile_cycles: int = 2,
    ) -> None:
        profile_dirs = tuple(
            str(Path(path)) for path in (user_data_dirs or ()) if str(path).strip()
        )
        if not profile_dirs:
            if not user_data_dir:
                raise ValueError('At least one Chrome user-data directory is required.')
            profile_dirs = (str(Path(user_data_dir)),)
        if profile_port_offsets is not None:
            profile_port_offsets = tuple(int(offset) for offset in profile_port_offsets)
            if len(profile_port_offsets) != len(profile_dirs):
                raise ValueError('profile_port_offsets must match user_data_dirs length.')
        self.endpoint = endpoint
        self._base_endpoint = endpoint
        self.executable_path = executable_path
        self.user_data_dirs = profile_dirs
        self.profile_port_offsets = profile_port_offsets
        self.cycle_profiles = cycle_profiles
        self.cycle_cooldown_seconds = max(0.0, cycle_cooldown_seconds)
        self.max_failed_profile_cycles = max(0, max_failed_profile_cycles)
        self._profile_index = 0
        self._blocked_profile_indexes: set[int] = set()
        self.profile_cycles = 0
        self.last_rotation_wrapped = False
        self.failed_profile_cycles = 0
        self._cycle_had_success = False
        self.last_completed_cycle_had_success: bool | None = None
        self.playwright: Any | None = None
        self.browser: Any | None = None
        self.context: Any | None = None
        self.page: Any | None = None
        self.chrome_process: subprocess.Popen[Any] | None = None

    @property
    def user_data_dir(self) -> str:
        return self.user_data_dirs[self._profile_index]

    @property
    def profile_label(self) -> str:
        return Path(self.user_data_dir).name

    def _debug_port(self) -> int:
        parsed = urlsplit(self.endpoint)
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
            raise ValueError(
                'PATAGONIA_CDP_ENDPOINT must be an HTTP URL such as '
                'http://127.0.0.1:9222.'
            )
        return parsed.port or 9222

    def _endpoint_for_profile(self, profile_index: int) -> str:
        """Give automatically launched replacement browsers their own CDP port."""
        parsed = urlsplit(self._base_endpoint)
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
            raise ValueError(
                'PATAGONIA_CDP_ENDPOINT must be an HTTP URL such as '
                'http://127.0.0.1:9222.'
            )
        offset = (
            self.profile_port_offsets[profile_index]
            if self.profile_port_offsets is not None
            else profile_index
        )
        port = (parsed.port or 9222) + offset
        host = parsed.hostname or '127.0.0.1'
        if ':' in host and not host.startswith('['):
            host = f'[{host}]'
        return urlunsplit(parsed._replace(netloc=f'{host}:{port}'))

    def _start_chrome(self) -> None:
        if not Path(self.executable_path).is_file():
            raise RuntimeError(f'Chrome executable does not exist: {self.executable_path}')
        command = [
            self.executable_path,
            f'--remote-debugging-port={self._debug_port()}',
            f'--user-data-dir={self.user_data_dir}',
        ]
        proxy = os.getenv('PATAGONIA_BROWSER_PROXY', '').strip()
        if proxy:
            command.append(f'--proxy-server={proxy}')
        self.chrome_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _connect_with_retry(self) -> None:
        deadline = time.monotonic() + 30
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                self.browser = self.playwright.chromium.connect_over_cdp(self.endpoint)
                return
            except Exception as exc:
                last_error = exc
                time.sleep(0.5)
        raise RuntimeError(f'Chrome did not expose CDP at {self.endpoint}: {last_error}')

    def connect(self, *, force_start: bool = False) -> None:
        self.playwright = sync_playwright().start()
        try:
            if force_start:
                self._start_chrome()
                self._connect_with_retry()
            else:
                try:
                    self.browser = self.playwright.chromium.connect_over_cdp(self.endpoint)
                except Exception:
                    self._start_chrome()
                    self._connect_with_retry()
            contexts = list(self.browser.contexts)
            if not contexts:
                raise RuntimeError(
                    'Connected Chrome has no browser context. Keep one normal tab open '
                    'before starting Step3.'
                )
            self.context = contexts[0]
            # Reuse an existing blank/new-tab page when possible. Creating a
            # page for every endpoint makes Chrome activate a foreground tab
            # and steal focus from the user.
            self.page = next(
                (
                    page for page in self.context.pages
                    if page.url in {'about:blank', 'chrome://new-tab-page/'}
                    and not page.is_closed()
                ),
                None,
            )
            if self.page is None:
                self.page = self.context.new_page()
        except Exception as exc:
            self.close()
            self._stop_owned_chrome()
            raise RuntimeError(
                f'Cannot connect to Chrome at {self.endpoint} or start '
                f'{self.executable_path}: {exc}'
            ) from exc

    def new_page(self) -> Any:
        if self.context is None or self.page is None or self.page.is_closed():
            raise RuntimeError('Chrome CDP session is not connected.')
        return self.page

    def restart(self) -> None:
        """Reconnect this profile, starting Chrome again when necessary."""
        self.close()
        # Only terminate a process started by this object. A manually started
        # Chrome is left alone and will simply be re-attached below.
        self._stop_owned_chrome()
        self.connect(force_start=False)

    def mark_profile_success(self) -> None:
        """Record progress so a completed rotation is not treated as all-blocked."""
        self._cycle_had_success = True

    def _finish_profile_cycle(self) -> None:
        self.profile_cycles += 1
        self.last_completed_cycle_had_success = self._cycle_had_success
        if self._cycle_had_success:
            self.failed_profile_cycles = 0
        else:
            if self.failed_profile_cycles >= self.max_failed_profile_cycles:
                raise AllProfilesBlockedError(
                    'Every profile was blocked for another full rotation after '
                    f'{self.failed_profile_cycles} cooldowns.'
                )
            self.failed_profile_cycles += 1
        self._cycle_had_success = False
        if self.cycle_cooldown_seconds:
            time.sleep(self.cycle_cooldown_seconds)

    def rotate_profile(self) -> str:
        """Discard the rejected profile and attach a fresh Chrome process."""
        start_index = self._profile_index
        self._blocked_profile_indexes.add(start_index)
        last_error: Exception | None = None
        self.last_rotation_wrapped = False

        if self.cycle_profiles:
            # A profile is retried in the next full round.  Do not retain a
            # permanent blocklist during a long-running collection.
            offsets = range(1, len(self.user_data_dirs))
        else:
            offsets = range(1, len(self.user_data_dirs) + 1)

        wrapped_this_rotation = False
        for offset in offsets:
            candidate = (start_index + offset) % len(self.user_data_dirs)
            if not self.cycle_profiles and candidate in self._blocked_profile_indexes:
                continue
            if candidate <= start_index and not wrapped_this_rotation:
                wrapped_this_rotation = True
                self.last_rotation_wrapped = True
                self._finish_profile_cycle()

            self.close()
            self._stop_owned_chrome()
            self._profile_index = candidate
            self.endpoint = self._endpoint_for_profile(candidate)
            try:
                # Profile 0 may be the user-started initial Chrome at the
                # base CDP port; attach to it when it is still available.
                self.connect(force_start=candidate != 0)
                return self.profile_label
            except Exception as exc:
                last_error = exc
                if not self.cycle_profiles:
                    self._blocked_profile_indexes.add(candidate)
        profiles = ', '.join(Path(path).name for path in self.user_data_dirs)
        detail = f'; last replacement error: {last_error}' if last_error else ''
        raise AllProfilesBlockedError(f'All Chrome profiles were blocked: {profiles}{detail}')

    def _stop_owned_chrome(self) -> None:
        process = self.chrome_process
        self.chrome_process = None
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)

    def close(self) -> None:
        # Disconnect only. A user-started Chrome is never closed; replacement
        # processes started by this class are stopped only during rotation.
        self.browser = None
        self.context = None
        self.page = None
        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None


class CdpPc(Pc):
    """Patagonia Step4 implementation backed by the attached Chrome context."""

    # The default collector previously sent endpoint requests back-to-back.
    # Keep these values configurable so a slower, legitimate browsing pace can
    # be used without changing the parser.
    request_delay_seconds = max(
        0.0, float(os.getenv('PATAGONIA_REQUEST_DELAY_SECONDS', '0.75')),
    )
    profile_switch_cooldown_seconds = max(
        0.0, float(os.getenv('PATAGONIA_PROFILE_SWITCH_COOLDOWN_SECONDS', '8')),
    )
    max_consecutive_profile_blocks = max(
        1, int(os.getenv('PATAGONIA_MAX_CONSECUTIVE_PROFILE_BLOCKS', '3')),
    )
    block_markers = (
        'access denied',
        'verify you are human',
        'security check',
        'checking your browser',
        'captcha',
        'you don\'t have permission to access',
    )

    def __init__(
        self,
        *args: Any,
        cdp: AttachedChrome,
        details_transport: str = 'curl_cffi',
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        details_transport = details_transport.strip().lower()
        if details_transport not in {'browser', 'curl_cffi'}:
            raise ValueError("details_transport must be 'browser' or 'curl_cffi'.")
        # ``cdp`` is the template for worker 0. Every request worker gets its
        # own AttachedChrome instance, port, profile and Playwright connection.
        self.cdp = cdp
        self.details_transport = details_transport
        self._worker_cdp = threading.local()
        self._worker_errors: list[BaseException] = []
        self._worker_errors_lock = threading.Lock()
        self._last_request_at = threading.local()
        self._fetch_page = threading.local()
        self._profile_block_count = threading.local()
        self._detail_session = threading.local()
        self._stop_requested = threading.Event()
        self._detail_only_urls: list[str] = []

    def _current_cdp(self) -> AttachedChrome:
        cdp = getattr(self._worker_cdp, 'value', None)
        if cdp is None:
            raise RuntimeError('CDP browser is not initialized for this worker.')
        return cdp

    def _make_worker_cdp(self, worker_index: int) -> AttachedChrome:
        """Build one isolated browser assignment for a worker.

        A profile directory is never assigned to two workers. The first
        worker may attach to the user-started browser on the base port; all
        other workers are launched on adjacent ports.
        """
        profiles = self.cdp.user_data_dirs
        worker_profiles = tuple(
            (index, path)
            for index, path in enumerate(profiles)
            if index % self.max_threads == worker_index
        )
        if not worker_profiles:
            raise ValueError(
                f'worker {worker_index + 1} has no Chrome profile assigned; '
                f'max_threads={self.max_threads}, profiles={len(profiles)}.'
            )
        profile_indexes, profile_dirs = zip(*worker_profiles)
        endpoint = self.cdp._endpoint_for_profile(profile_indexes[0])
        return AttachedChrome(
            endpoint=endpoint,
            executable_path=self.cdp.executable_path,
            user_data_dirs=profile_dirs,
            profile_port_offsets=profile_indexes,
            cycle_profiles=self.cdp.cycle_profiles,
            cycle_cooldown_seconds=self.cdp.cycle_cooldown_seconds,
            max_failed_profile_cycles=self.cdp.max_failed_profile_cycles,
        )

    def close_playwright(self) -> None:
        self._discard_fetch_page()
        session = getattr(self._detail_session, 'value', None)
        if session is not None:
            try:
                session.close()
            finally:
                self._detail_session.value = None
        cdp = getattr(self._worker_cdp, 'value', None)
        if cdp is not None:
            cdp.close()
            self._worker_cdp.value = None

    def _discard_fetch_page(self) -> None:
        """Forget the native page before its CDP/Playwright owner is closed.

        ``AttachedChrome.rotate_profile()`` stops the previous Playwright
        driver. Calling methods such as ``is_closed()`` on a Page from that
        driver raises "Event loop is closed", so the reference must be
        removed without touching the old Page object.
        """
        self._fetch_page.value = None

    def _wait_before_request(self) -> None:
        now = time.monotonic()
        last_request_at = getattr(self._last_request_at, 'value', 0.0)
        wait_for = last_request_at + self.request_delay_seconds - now
        if wait_for > 0:
            time.sleep(wait_for)
        self._last_request_at.value = time.monotonic()

    def _block_reason(
        self,
        status: int,
        headers: dict[str, str] | None = None,
        source: str = '',
    ) -> str | None:
        headers = headers or {}
        server = headers.get('server', '').lower()
        body = source.lower()
        if status in {403, 429}:
            return f'HTTP {status}'
        if status == 404 and 'akamai' in server:
            return 'Akamai soft 404'
        if any(marker in body for marker in self.block_markers):
            return 'verification or access-denied response body'
        if source and self._is_not_found_html(source):
            return 'Not found response body'
        return None

    @staticmethod
    def _is_connection_error(exc: BaseException) -> bool:
        text = str(exc).lower()
        return isinstance(exc, PlaywrightError) or any(
            marker in text for marker in (
                'cdp session is not connected',
                'target page, context or browser has been closed',
                'browser has been closed',
                'connection closed',
                'transport is closed',
            )
        )

    def _restart_current_browser(self, reason: BaseException) -> None:
        cdp = self._current_cdp()
        self.Tool.print(
            f'CDP connection lost on profile {cdp.profile_label}; '
            f'restarting browser and retrying: {reason}',
            color='yellow',
        )
        self._discard_fetch_page()
        cdp.restart()
        self._last_request_at.value = 0.0

    def _current_fetch_page(self):
        """Create one same-origin page per worker and reuse it for all fetches."""
        page = getattr(self._fetch_page, 'value', None)
        if page is not None:
            try:
                if not page.is_closed():
                    return page
            except Exception:
                # The profile may already have stopped its Playwright driver.
                pass
            self._discard_fetch_page()
        page = self._current_cdp().new_page()
        page.goto(self.Tool.config.base_url, wait_until='domcontentloaded', timeout=60000)
        self._fetch_page.value = page
        return page

    def _current_detail_session(self):
        """Create an independent curl_cffi session for the current worker."""
        session = getattr(self._detail_session, 'value', None)
        if session is None:
            session = curl_requests.Session()
            session.headers.update(dict(headers))
            session.cookies.update(dict(cookies))
            self._detail_session.value = session
        return session

    def _endpoint_body(self, endpoint: str, *, allow_empty: bool = False) -> str:
        self._wait_before_request()
        page = self._current_fetch_page()
        try:
            payload = page.evaluate(_FETCH_SCRIPT, {'url': endpoint, 'timeout': 60000})
            status = int(payload.get('status') or 0)
            headers = dict(payload.get('headers') or {})
            source = str(payload.get('body') or '')
            if not 200 <= status < 300:
                reason = self._block_reason(status, headers)
                if reason:
                    raise ProfileBlockedError(f'{reason}: {endpoint}')
                raise RuntimeError(f'Browser endpoint returned HTTP {status}: {endpoint}')
            if not source.strip() and not allow_empty:
                raise RuntimeError(f'Browser endpoint returned an empty response: {endpoint}')
            reason = self._block_reason(status, headers, source)
            if reason:
                raise ProfileBlockedError(f'{reason}: {endpoint}')
            return source
        except PlaywrightError as exc:
            try:
                source = page.content()
            except Exception:
                source = ''
            reason = self._block_reason(0, source=source)
            if reason:
                raise ProfileBlockedError(f'{reason}: {endpoint}') from exc
            raise

    def _product_details(self, url: str):
        if self.details_transport == 'curl_cffi':
            return self._product_details_curl(url)
        return self._product_details_browser(url)

    def _product_details_curl(self, url: str):
        """Fetch PDP HTML through the worker's standalone curl_cffi session."""
        self._wait_before_request()
        response = self._current_detail_session().get(
            url,
            timeout=60,
            allow_redirects=True,
            impersonate=os.getenv('PATAGONIA_CURL_IMPERSONATE', 'chrome'),
            headers=headers,
            cookies=cookies,
        )
        response_headers = {
            str(key).lower(): str(value)
            for key, value in response.headers.items()
        }
        source = response.text
        status = int(response.status_code)
        reason = self._block_reason(status, response_headers, source)
        if reason:
            raise ProfileBlockedError(f'{reason}: {url}')
        if not 200 <= status < 300:
            raise RuntimeError(f'curl_cffi PDP request returned HTTP {status}: {url}')
        return self._pdp_details(source)

    def _product_details_browser(self, url: str):
        """Read PDP-only fields through a normal document navigation.

        Patagonia's Product-Variation response contains SKU state but no
        customer-facing description or accordion data. Product-Show redirects
        to the same PDP, so navigate to the canonical product URL instead of
        issuing a JavaScript fetch for the HTML document. This preserves the
        browser request context that the previous collector used successfully.
        """
        self._wait_before_request()
        page = self._current_fetch_page()
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
            status = response.status if response is not None else 0
            headers = dict(response.headers) if response is not None else {}
            source = page.content()
            reason = self._block_reason(status, headers, source)
            if reason:
                raise ProfileBlockedError(f'{reason}: {url}')
            if not 200 <= status < 300:
                raise RuntimeError(f'PDP navigation returned HTTP {status}: {url}')
            return self._pdp_details(source)
        except PlaywrightError as exc:
            try:
                source = page.content()
            except Exception:
                source = ''
            reason = self._block_reason(0, source=source)
            if reason:
                raise ProfileBlockedError(f'{reason}: {url}') from exc
            raise

    def fetch_product(self, url: str, category: str):
        """Reuse the base parser, but retry the attached context instead of
        launching a separate Playwright browser after an endpoint failure.
        """
        url = self.Tool.URL.add_site(url)
        product_id = self._product_id(url)
        requested_color = self._color_id(url, product_id)
        last_error: Exception | None = None

        attempt = 0
        while True:
            try:
                details = self._product_details(url)
                if requested_color:
                    color_products = [self._variation(product_id, requested_color)]
                else:
                    master = self._variation(product_id)
                    colors = self._color_values(master)
                    color_products = [
                        self._variation(product_id, str(color['id'])) for color in colors
                    ] or [master]

                rows = []
                for product in color_products:
                    color = str((product.get('selectedColor') or {}).get('colorCode') or '').strip()
                    images = self._color_images(product_id, color) if color else []
                    rows.extend(
                        self._rows_for_color(url, category, product_id, product, images, details)
                    )
                if not rows:
                    raise ValueError('Product-Variation returned no SKU rows.')
                self._current_cdp().mark_profile_success()
                self._profile_block_count.value = 0
                return rows
            except ProfileBlockedError as exc:
                last_error = exc
                if self.details_transport == 'curl_cffi':
                    raise RuntimeError(f'curl_cffi PDP request was blocked: {exc}') from exc
                cdp = self._current_cdp()
                previous_profile = cdp.profile_label
                block_count = getattr(self._profile_block_count, 'value', 0) + 1
                self._profile_block_count.value = block_count
                if block_count >= self.max_consecutive_profile_blocks:
                    self._stop_requested.set()
                    raise AllProfilesBlockedError(
                        f'{block_count} consecutive profiles were blocked; collection stopped to '
                        'avoid repeatedly launching Chrome. Wait before trying again.'
                    ) from exc
                self._discard_fetch_page()
                if self.profile_switch_cooldown_seconds:
                    time.sleep(self.profile_switch_cooldown_seconds)
                next_profile = cdp.rotate_profile()
                self._last_request_at.value = 0.0
                self.Tool.print(
                    f'Profile {previous_profile} was blocked ({exc}); switched to '
                    f'{next_profile} and retrying the current product.',
                    color='yellow',
                )
                if cdp.last_rotation_wrapped:
                    if cdp.last_completed_cycle_had_success:
                        cycle_status = 'had successful products; failure counter reset'
                    else:
                        cycle_status = (
                            'had no successful products; cooldown '
                            f'{cdp.failed_profile_cycles}/'
                            f'{cdp.max_failed_profile_cycles}'
                        )
                    self.Tool.print(
                        f'Completed profile round {cdp.profile_cycles}: {cycle_status}; '
                        f'restarted from {next_profile}.',
                        color='yellow',
                    )
            except Exception as exc:
                last_error = exc
                if self._is_connection_error(exc):
                    try:
                        self._restart_current_browser(exc)
                    except Exception as restart_error:
                        last_error = restart_error
                        self.Tool.print(
                            f'CDP browser restart failed: {restart_error}',
                            color='red',
                        )
                attempt += 1
                if attempt >= self.max_attempts:
                    raise RuntimeError(str(last_error))
                self.Tool.print(
                    f'Attached Chrome request failed; retrying ({attempt}/{self.max_attempts}): {exc}',
                    color='yellow',
                )

    @staticmethod
    def _has_current_product_fields(rows) -> bool:
        return bool(rows) and all(
            isinstance(row, dict)
            and bool(row.get('Description'))
            and all(field in row for field in CUSTOM_FIELD_NAMES)
            for row in rows
        )

    @staticmethod
    def _merge_pdp_details(rows, details):
        """Add PDP fields without changing cached SKU/price/image data."""
        return [
            {
                **row,
                'Description': details['description'],
                **{field: details[field] for field in CUSTOM_FIELD_NAMES},
            }
            for row in rows
        ]

    def _cached_rows_for_url(self, url, task_id=None):
        """Read current or legacy index entries for a URL.

        Older Patagonia runs used a different task-id hash. The URL remains
        the stable cache key, so fall back to the first normalized row list
        under that URL instead of treating existing variant data as missing.
        """
        if task_id is not None:
            rows = self.index.check(url, task_id)
            if isinstance(rows, list) and rows:
                return rows
        entries = self.index.data.get(url, {})
        if isinstance(entries, dict):
            for rows in entries.values():
                if isinstance(rows, list) and rows:
                    return rows
        return []

    def _load_tasks_from_mapping(self, data) -> None:
        """Reuse normal Step4 task IDs, while re-fetching legacy empty descriptions."""
        if not isinstance(data, dict):
            raise TypeError('Step4 input must be a category-to-URL mapping')
        seq_num = 0
        for category, urls in data.items():
            if not isinstance(urls, (list, tuple)):
                raise TypeError(f'Step4 URLs for category {category!r} must be a list')
            for url in urls:
                if url in self.skip_input_url_ls:
                    continue
                seq_num += 1
                task_id = self._generate_task_id(url)
                cached_rows = self._cached_rows_for_url(url, task_id)
                if cached_rows and not self.index.check(url, task_id):
                    # Alias the legacy entry under the current task id so the
                    # standard writer/cache flow can find it.
                    self.index.append(task_id, url, cached_rows)
                if self._has_current_product_fields(cached_rows):
                    with self.global_lock:
                        if task_id not in self.catch.check(category):
                            self.catch.append(category, task_id, url)
                            self._mark_cache_changed()
                    self.result_queue.put((task_id, category, url, [], False))
                else:
                    self.task_queue.put((str(task_id), category, url))
                if isinstance(self.ts_num, int) and seq_num >= self.ts_num:
                    self.Tool.print(f'Enabled test mode; task limit: {self.ts_num}')
                    self.total_tasks = seq_num
                    return
        self.total_tasks = seq_num

    def request_worker(self):
        """Keep the normal Step4 cache flow, but propagate profile exhaustion."""
        from queue import Empty

        try:
            while not self._stop_requested.is_set():
                try:
                    seq_id, category, url = self.task_queue.get_nowait()
                except Empty:
                    break

                with self._get_url_lock(url):
                    cached_data = self._cached_rows_for_url(url, seq_id)
                    if self._has_current_product_fields(cached_data):
                        with self.global_lock:
                            if seq_id not in self.catch.check(category):
                                self.catch.append(category, seq_id, url)
                                self._mark_cache_changed()
                        self.result_queue.put((seq_id, category, url, [], False))
                        continue

                    data = []
                    is_failed = False
                    try:
                        if cached_data:
                            # Existing rows already contain all variant data.
                            # Only request the PDP fields and enrich the cache.
                            details = self._product_details(self.Tool.URL.add_site(url))
                            data = self._merge_pdp_details(cached_data, details)
                            if self.details_transport == 'browser':
                                self._current_cdp().mark_profile_success()
                                self._profile_block_count.value = 0
                            detail_only = True
                        elif self.details_transport == 'curl_cffi':
                            raise RuntimeError(
                                'No cached variant rows for this URL; curl_cffi detail-only '
                                'mode will not start Chrome. Run the original browser collector '
                                'first to populate the variant cache.'
                            )
                        else:
                            parse_result = self.fetch_product(url, category)
                            data = self._normalize_products(parse_result)
                            detail_only = False
                        if not data:
                            raise ValueError('Product parsing returned no rows.')
                        with self.global_lock:
                            self.index.append(seq_id, url, data)
                            if detail_only:
                                self._detail_only_urls.append(url)
                            else:
                                self.fetched_urls.append(url)
                            self._mark_cache_changed()
                    except AllProfilesBlockedError:
                        self._stop_requested.set()
                        raise
                    except Exception as exc:
                        is_failed = True
                        self.Tool.print(f'【Task failed】seq:{seq_id} url:{url} error:{exc}')
                        with self.global_lock:
                            self.failures.setdefault(category, []).append(url)

                    self.result_queue.put((seq_id, category, url, data, is_failed))
        finally:
            self.close_playwright()

    def _run_worker(self, worker_index: int) -> None:
        cdp: AttachedChrome | None = None
        try:
            if self.details_transport == 'curl_cffi':
                self.Tool.print(
                    'PDP detail mode: curl_cffi only; Chrome startup skipped.',
                    color='cyan',
                )
                self.request_worker()
                return
            cdp = self._make_worker_cdp(worker_index)
            self._worker_cdp.value = cdp
            # Playwright's sync API must be created and used in the same
            # thread, so connection setup belongs inside the worker.
            self.Tool.print(
                f'Worker {worker_index + 1}: starting Chrome profile '
                f'{cdp.profile_label} on {cdp.endpoint}',
                color='cyan',
            )
            # Attach when a worker browser is already running; otherwise
            # AttachedChrome starts it on the worker's assigned port/profile.
            cdp.connect(force_start=False)
            self.request_worker()
        except BaseException as exc:
            if isinstance(exc, AllProfilesBlockedError):
                self._stop_requested.set()
            with self._worker_errors_lock:
                self._worker_errors.append(exc)
            self.Tool.print(
                f'Worker {worker_index + 1} stopped: {exc}',
                color='red',
            )
        finally:
            if cdp is not None:
                self.close_playwright()

    def run(self):
        if not isinstance(self.max_threads, int) or isinstance(self.max_threads, bool) or self.max_threads < 1:
            raise ValueError('max_threads must be a positive integer.')
        if self.max_threads > len(self.cdp.user_data_dirs):
            raise ValueError(
                f'max_threads={self.max_threads} exceeds configured Chrome profiles '
                f'({len(self.cdp.user_data_dirs)}).'
            )
        try:
            self.load_tasks()
            self.Tool.print(f'Total tasks to process: {self.total_tasks}')
            writer_thread = threading.Thread(target=self.writer_worker)
            writer_thread.start()
            workers = [
                threading.Thread(
                    target=self._run_worker,
                    args=(worker_index,),
                    name=f'patagonia-cdp-{worker_index + 1}',
                )
                for worker_index in range(self.max_threads)
            ]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join()
            self.result_queue.put(None)
            writer_thread.join()

            if self._worker_errors:
                raise RuntimeError(
                    f'{len(self._worker_errors)} CDP worker(s) failed; '
                    f'first error: {self._worker_errors[0]}'
                ) from self._worker_errors[0]

            all_rows = list(self._iter_all_product_rows())
            self.tool.File.save_csv(all_rows, self.output_ts_file, columns=self.fieldnames)
            clean_rows = self.tool.json_del_url(all_rows)
            self.tool.File.save_csv(clean_rows, self.output_file, columns=self.fieldnames)
            self.tool.File.save_json(self.failures, self.fail_file)
            self.Tool.print(f'Browser-fetched cache misses: {len(self.fetched_urls)}')
            self.Tool.print(f'PDP detail-only cache updates: {len(self._detail_only_urls)}')
            self.Tool.print('==================== Done ====================')
            return all_rows
        finally:
            # Worker-owned connections are closed by _run_worker. This also
            # closes a template connection if a caller supplied one already.
            self.cdp.close()


def _profile_dirs_from_env() -> tuple[str, ...]:
    configured = os.getenv('PATAGONIA_CHROME_USER_DATA_DIRS', '').strip()
    if configured:
        dirs = tuple(part.strip() for part in configured.split(os.pathsep) if part.strip())
        if dirs:
            return dirs

    default_dirs = tuple(
        rf'C:\Users\69087\AppData\Local\Chrome-patagonia-debug{i}'
        for i in range(1, 100)
    )
    preferred = os.getenv('PATAGONIA_CHROME_USER_DATA_DIR', '').strip()
    if not preferred:
        return default_dirs
    return (preferred,) + tuple(path for path in default_dirs if path != preferred)


if __name__ == '__main__':
    cdp = AttachedChrome(
        endpoint=os.getenv('PATAGONIA_CDP_ENDPOINT', 'http://127.0.0.1:9223'),
        executable_path=os.getenv(
            'PATAGONIA_CHROME_PATH',
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        ),
        user_data_dirs=_profile_dirs_from_env(),
        cycle_profiles=(
            os.getenv('PATAGONIA_PROFILE_CYCLE', 'true').strip().lower()
            not in {'0', 'false', 'no', 'off'}
        ),
        cycle_cooldown_seconds=max(
            0.0,
            float(os.getenv('PATAGONIA_PROFILE_CYCLE_COOLDOWN_SECONDS', '300')),
        ),
        max_failed_profile_cycles=max(
            0,
            int(os.getenv('PATAGONIA_MAX_FAILED_PROFILE_CYCLES', '2')),
        ),
    )
    CdpPc(
        tool=Tool,
        input_path=input_file,
        output_path=output_file,
        fail_file=fail_file,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        ts_num=ts_num,
        fieldnames=fieldnames,
        catch_path=catch_path,
        index_path=index_path,
        output_ts_file=output_ts_file,
        max_threads=5,
        cdp=cdp,
        details_transport=os.getenv('PATAGONIA_DETAILS_TRANSPORT', 'curl_cffi'),
    ).run()


    # max_threads=2 uses the base port and the next port (9223/9224 by default),
    # with separate user-data directories. Additional workers continue on the
    # following ports. The first browser may be started manually; other worker
    # browsers are launched by this script.
