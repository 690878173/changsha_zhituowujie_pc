"""补全 Patagonia 已有变体缓存中的 Description 与 PDP 自定义字段。

只使用 curl_cffi 和下方维护的 Headers/Cookies；不导入、不启动、也不依赖
浏览器或旧的 CDP 采集脚本。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections.abc import Mapping
from html import escape as escape_html
from pathlib import Path
import tempfile
import threading
from urllib.parse import urljoin, urlsplit

from curl_cffi import requests as curl_requests
from lxml import html


ROOT = Path(__file__).resolve().parent

cookies = {
    'dwanonymous_aa4135988320dfd11a2574fc0fe760c4': 'bcKCjxG2W3S0lHXAD8AK9a6AsW',
    'pat_web_scope_id': 'patagonia',
    '__kla_id': 'eyJjaWQiOiJabVF4TVRJMU4ySXROell3TWkwMFl6UXhMVGc0T0dFdFpEUTVZelJrTkdWaU1XUmwifQ==',
    '_gcl_au': '1.1.1102640572.1787377186',
    '_ga': 'GA1.1.1739459406.1787377186',
    '_pin_unauth': 'dWlkPVpUY3pZVE16TWpJdFl6YzJZaTAwWXpBM0xXRXlNRGN0TURObU9EUTNOelJsTlRjMA',
    'bm': '5936f3bf-f7c2-4758-9dc1-47eb73576763',
    'OptanonAlertBoxClosed': '2026-08-22T05:39:48.402Z',
    'dwsid': 'WgtxVoAX5zQGrY-fdn3FZ0kvGU78Ikv4yoZHlJiiJdrhDVo_BLVFwWZteCNSQTq-NniYl7jI9kdp9X-nI7lheA==',
    'dwac_8cd9b022d7269f392c1ffcd8ea': 'M_64ilOAUoQIDbVsZGCJiiDa0JIvtf5IxCY%3D|dw-only|||USD|false|US%2FPacific|true',
    'cqcid': 'bcKCjxG2W3S0lHXAD8AK9a6AsW',
    'cquid': '||',
    'sid': 'M_64ilOAUoQIDbVsZGCJiiDa0JIvtf5IxCY',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    'ak_bmsc': '24D42D5BECE83FC23BF8E6CE5DE8A7AC~000000000000000000000000000000~YAAQbQ7SFx09RSOgAQAAa5XFWwEX2oPk9/zZmtK1w1iIXWK7nQJJsIB9/P4uSp1RuBXQgBuIXBY4+M32X/JKhIAqSzbqhNftmYETv41u7qfs789QWfoa7GwXAMAd/rTPZ+3o06CirV0mditFkf2oP8RMqNVWvli010d/3KRrgCQcQin9EsmrcK/h0jg4NyLh4eIM4L03guV8Dhjn565bFWbO//7fiLI1DP+MbL8zkH/DbbAB+scUFl+U6C9h+SKCrVM8YnNkcVJU72EyQdYC6e0XeP1cVcfL0etgFgEtb6ytsufphPz2PIyXV4RK9GcsZ1wPw8gids6Z/5CsAwCJU+1yV1ezzL+ztBb1K8JKx+VIBM1BogM712wZG7OjL+4sPSYt9QBJiO5DRc+Uikf9',
    '__kla_off': 'false',
    'bm_so': 'AAE1F0E2012F6858BAC1107E2C2BE07A4E2AC36CF4A969CBFE556AC71ECF4F50~YAAQbQ7SF3UhSyOgAQAA+sUgXAgx98GyKBzv7WiAphW6gZmMUCkVZ/wQeCM8baiBdEO7nowasWfanVkwOIEnsQY346B0Ua2mq1sNm3QHkEHWezsjGLYpNOpF2uaOmbVeDixgfZ2mdLokG4u9vErEQndZoc6KkF82p8CGoZ2TWki4/4GuwCFDjlVeVNiE7gY/YSJraQLRc3Y5Nn890TQPN/94vfLE0ktrNrTC++v8y2ZwOyFL6G3QmFh0pBCoNi1dOdeU75kaOp1IfTU0b1wQL7L4+Lba3jO+n9DutV7zGF+1R2JqfOqV8zTFD9RJA/QIVE8TK2yoCAYsyXm8yF6Xr6WVa+SA4IKJIVEXxeqYYnUkaXEkLYjawuFoDBGpGRgqGGS58gRnJ0uoD/e1lBCHqu71hbCcBknOOTPAW7pyMdBEyTTnF56fZfoiff4EDVVSVn6HefEgpg3G34yPMt1t4PmMLV6Z',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Tue+Sep+01+2026+16%3A40%3A46+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=1c723ea2-05dc-46fc-8988-3839798d4840&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1%2CC0005%3A1&intType=3&geolocation=US%3BCA&AwaitingReconsent=false',
    '_br_uid_2': 'uid%3D9083764294322%3Av%3D17.0%3Ats%3D1787377185280%3Ahc%3D37',
    '_ga_1SYPSJZYJ5': 'GS2.1.s1788252016$o9$g1$t1788252047$j29$l0$h0',
    'bm_lso': 'AAE1F0E2012F6858BAC1107E2C2BE07A4E2AC36CF4A969CBFE556AC71ECF4F50~YAAQbQ7SF3UhSyOgAQAA+sUgXAgx98GyKBzv7WiAphW6gZmMUCkVZ/wQeCM8baiBdEO7nowasWfanVkwOIEnsQY346B0Ua2mq1sNm3QHkEHWezsjGLYpNOpF2uaOmbVeDixgfZ2mdLokG4u9vErEQndZoc6KkF82p8CGoZ2TWki4/4GuwCFDjlVeVNiE7gY/YSJraQLRc3Y5Nn890TQPN/94vfLE0ktrNrTC++v8y2ZwOyFL6G3QmFh0pBCoNi1dOdeU75kaOp1IfTU0b1wQL7L4+Lba3jO+n9DutV7zGF+1R2JqfOqV8zTFD9RJA/QIVE8TK2yoCAYsyXm8yF6Xr6WVa+SA4IKJIVEXxeqYYnUkaXEkLYjawuFoDBGpGRgqGGS58gRnJ0uoD/e1lBCHqu71hbCcBknOOTPAW7pyMdBEyTTnF56fZfoiff4EDVVSVn6HefEgpg3G34yPMt1t4PmMLV6Z~1788252050874',
    'bm_s': 'YAAQbQ7SFyUjSyOgAQAAzeggXAbQrsnS0X7mTGR552yYy9/gbvnfy7SMrCA94LWHKpxH8QyyMpgIyI8Iqc4PfEs8Qdz7tmHdqXuZ9AIeKZK1b22Tc9ApP4ERlq8S3ZbVM7Ak6sKFds7UNtc0EO8Q6cfWBu4eqdlaX/PmZcWhVFcktF0QS+eUmE9Fe89DW3tyA+qR5TvexDmwQQd5ezsySIAdIYF/sB9tr5jMvIiSCjGoFqpx7HVILtvuFAKvPLBSkX5W7WhiLH5Bkx5dvWUdpVMM5lnz0FDrmslhe+rTXo4KTGp6rBzX1NRP1L1FVaSojDFXr/DZckwg42C8mP1ioIhEm4cD06WtiSiVW9IqqYRwEUfuqfbXU8zJXgH2UqiAxkC99ogc67N/mfiL25to3oaBBJQ6zLkodhd09M1TWKAyOKvsVjd09ZOvhco1SspB0ZWQkRfGiYXfyMWnh9Fu27hVnvp7XiKzqVcIA66m9zyjrMkRoR+WtCxuCF6ztpUl5WqrfTz1POeLW7G9CRMt23QdFG9IQ5MDhDpVbNfgfSUhahgj5Ud3FQgs2M0gTNB7nnEDNxkQvIZsGCEpjlvthL786CubfLwzkq4wCmz9mpISqfuWAtG9w9eTJyff0c+eRnAdxJUaWWu+DvNjrVF+X+i1T7Ya97zHtY8Gz9l8l8l/X9v17O3l+KUGVjsJ+tJu3U2/3BmrH9df+1OhQxBYmfbbGEJEfXqEMEb6AXygNldQXJkLSbkGZG0KVmq/tyyEfcSv3ejHh1iEMoetcn+mgaNXHDOW/KefAaxXRVk+Oxgs4jpwER4xstBsjvOsU/18ikf3fn9LZn1ygUgC/uR+mMmsjMtpxToNunW0hDd2TsmXhIB3CRSO+xdGjRqVtOViVU2nh1yibsgh/Eno+65w2g+ZruxNFJkbgKfJmGX7ADl6XnYsTA5td9dW1bNYCrpu9nuVPWXIuJHkrKebJUC6nNCWi/aFhSwNPJq9ekMKlwbVD3kFFCSJTz+d7bB1L9pIPtrog1KPu/vAgeH7bIurKvVraUFkop/WvAKe3dARlegkQH98AUvd0fM5KDuFZLIZeOQ3sYe8RPINaaRsW5N1FpS/aEuFZjRCF4cOq9jpuDg=',
    'bm_sv': '4B8689604118D553EF3392C6D42BB930~YAAQbQ7SFyYjSyOgAQAAzeggXAFZbATkR2AIeVkReK3eiBHFVf4l0bvR5XBMMrY12i7NAq7P1yi7ICYsRJBtHr1Vwx8Zy9sb4kxQ2aFypG9qEGj3CFASMSbhP8/1+qTYuxWgZBoxsuYfKrZSZ4frwECbhTO+L2Vnrzh+ZVNsz6wdRSvBP9BOVhvg14dH3DjxYwys0luP56+f+WYYAQRFzqy0IrBRmu3U+cPUSTJCoXvbkQ7OeaOjMX63L4/lNmPPQfy7VA==~1',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.patagonia.com/shop/gear/bags/black-hole',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'dwanonymous_aa4135988320dfd11a2574fc0fe760c4=bcKCjxG2W3S0lHXAD8AK9a6AsW; pat_web_scope_id=patagonia; __kla_id=eyJjaWQiOiJabVF4TVRJMU4ySXROell3TWkwMFl6UXhMVGc0T0dFdFpEUTVZelJrTkdWaU1XUmwifQ==; _gcl_au=1.1.1102640572.1787377186; _ga=GA1.1.1739459406.1787377186; _pin_unauth=dWlkPVpUY3pZVE16TWpJdFl6YzJZaTAwWXpBM0xXRXlNRGN0TURObU9EUTNOelJsTlRjMA; bm=5936f3bf-f7c2-4758-9dc1-47eb73576763; OptanonAlertBoxClosed=2026-08-22T05:39:48.402Z; dwsid=WgtxVoAX5zQGrY-fdn3FZ0kvGU78Ikv4yoZHlJiiJdrhDVo_BLVFwWZteCNSQTq-NniYl7jI9kdp9X-nI7lheA==; dwac_8cd9b022d7269f392c1ffcd8ea=M_64ilOAUoQIDbVsZGCJiiDa0JIvtf5IxCY%3D|dw-only|||USD|false|US%2FPacific|true; cqcid=bcKCjxG2W3S0lHXAD8AK9a6AsW; cquid=||; sid=M_64ilOAUoQIDbVsZGCJiiDa0JIvtf5IxCY; __cq_dnt=0; dw_dnt=0; ak_bmsc=24D42D5BECE83FC23BF8E6CE5DE8A7AC~000000000000000000000000000000~YAAQbQ7SFx09RSOgAQAAa5XFWwEX2oPk9/zZmtK1w1iIXWK7nQJJsIB9/P4uSp1RuBXQgBuIXBY4+M32X/JKhIAqSzbqhNftmYETv41u7qfs789QWfoa7GwXAMAd/rTPZ+3o06CirV0mditFkf2oP8RMqNVWvli010d/3KRrgCQcQin9EsmrcK/h0jg4NyLh4eIM4L03guV8Dhjn565bFWbO//7fiLI1DP+MbL8zkH/DbbAB+scUFl+U6C9h+SKCrVM8YnNkcVJU72EyQdYC6e0XeP1cVcfL0etgFgEtb6ytsufphPz2PIyXV4RK9GcsZ1wPw8gids6Z/5CsAwCJU+1yV1ezzL+ztBb1K8JKx+VIBM1BogM712wZG7OjL+4sPSYt9QBJiO5DRc+Uikf9; __kla_off=false; bm_so=AAE1F0E2012F6858BAC1107E2C2BE07A4E2AC36CF4A969CBFE556AC71ECF4F50~YAAQbQ7SF3UhSyOgAQAA+sUgXAgx98GyKBzv7WiAphW6gZmMUCkVZ/wQeCM8baiBdEO7nowasWfanVkwOIEnsQY346B0Ua2mq1sNm3QHkEHWezsjGLYpNOpF2uaOmbVeDixgfZ2mdLokG4u9vErEQndZoc6KkF82p8CGoZ2TWki4/4GuwCFDjlVeVNiE7gY/YSJraQLRc3Y5Nn890TQPN/94vfLE0ktrNrTC++v8y2ZwOyFL6G3QmFh0pBCoNi1dOdeU75kaOp1IfTU0b1wQL7L4+Lba3jO+n9DutV7zGF+1R2JqfOqV8zTFD9RJA/QIVE8TK2yoCAYsyXm8yF6Xr6WVa+SA4IKJIVEXxeqYYnUkaXEkLYjawuFoDBGpGRgqGGS58gRnJ0uoD/e1lBCHqu71hbCcBknOOTPAW7pyMdBEyTTnF56fZfoiff4EDVVSVn6HefEgpg3G34yPMt1t4PmMLV6Z; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Sep+01+2026+16%3A40%3A46+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202405.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=1c723ea2-05dc-46fc-8988-3839798d4840&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1%2CC0005%3A1&intType=3&geolocation=US%3BCA&AwaitingReconsent=false; _br_uid_2=uid%3D9083764294322%3Av%3D17.0%3Ats%3D1787377185280%3Ahc%3D37; _ga_1SYPSJZYJ5=GS2.1.s1788252016$o9$g1$t1788252047$j29$l0$h0; bm_lso=AAE1F0E2012F6858BAC1107E2C2BE07A4E2AC36CF4A969CBFE556AC71ECF4F50~YAAQbQ7SF3UhSyOgAQAA+sUgXAgx98GyKBzv7WiAphW6gZmMUCkVZ/wQeCM8baiBdEO7nowasWfanVkwOIEnsQY346B0Ua2mq1sNm3QHkEHWezsjGLYpNOpF2uaOmbVeDixgfZ2mdLokG4u9vErEQndZoc6KkF82p8CGoZ2TWki4/4GuwCFDjlVeVNiE7gY/YSJraQLRc3Y5Nn890TQPN/94vfLE0ktrNrTC++v8y2ZwOyFL6G3QmFh0pBCoNi1dOdeU75kaOp1IfTU0b1wQL7L4+Lba3jO+n9DutV7zGF+1R2JqfOqV8zTFD9RJA/QIVE8TK2yoCAYsyXm8yF6Xr6WVa+SA4IKJIVEXxeqYYnUkaXEkLYjawuFoDBGpGRgqGGS58gRnJ0uoD/e1lBCHqu71hbCcBknOOTPAW7pyMdBEyTTnF56fZfoiff4EDVVSVn6HefEgpg3G34yPMt1t4PmMLV6Z~1788252050874; bm_s=YAAQbQ7SFyUjSyOgAQAAzeggXAbQrsnS0X7mTGR552yYy9/gbvnfy7SMrCA94LWHKpxH8QyyMpgIyI8Iqc4PfEs8Qdz7tmHdqXuZ9AIeKZK1b22Tc9ApP4ERlq8S3ZbVM7Ak6sKFds7UNtc0EO8Q6cfWBu4eqdlaX/PmZcWhVFcktF0QS+eUmE9Fe89DW3tyA+qR5TvexDmwQQd5ezsySIAdIYF/sB9tr5jMvIiSCjGoFqpx7HVILtvuFAKvPLBSkX5W7WhiLH5Bkx5dvWUdpVMM5lnz0FDrmslhe+rTXo4KTGp6rBzX1NRP1L1FVaSojDFXr/DZckwg42C8mP1ioIhEm4cD06WtiSiVW9IqqYRwEUfuqfbXU8zJXgH2UqiAxkC99ogc67N/mfiL25to3oaBBJQ6zLkodhd09M1TWKAyOKvsVjd09ZOvhco1SspB0ZWQkRfGiYXfyMWnh9Fu27hVnvp7XiKzqVcIA66m9zyjrMkRoR+WtCxuCF6ztpUl5WqrfTz1POeLW7G9CRMt23QdFG9IQ5MDhDpVbNfgfSUhahgj5Ud3FQgs2M0gTNB7nnEDNxkQvIZsGCEpjlvthL786CubfLwzkq4wCmz9mpISqfuWAtG9w9eTJyff0c+eRnAdxJUaWWu+DvNjrVF+X+i1T7Ya97zHtY8Gz9l8l8l/X9v17O3l+KUGVjsJ+tJu3U2/3BmrH9df+1OhQxBYmfbbGEJEfXqEMEb6AXygNldQXJkLSbkGZG0KVmq/tyyEfcSv3ejHh1iEMoetcn+mgaNXHDOW/KefAaxXRVk+Oxgs4jpwER4xstBsjvOsU/18ikf3fn9LZn1ygUgC/uR+mMmsjMtpxToNunW0hDd2TsmXhIB3CRSO+xdGjRqVtOViVU2nh1yibsgh/Eno+65w2g+ZruxNFJkbgKfJmGX7ADl6XnYsTA5td9dW1bNYCrpu9nuVPWXIuJHkrKebJUC6nNCWi/aFhSwNPJq9ekMKlwbVD3kFFCSJTz+d7bB1L9pIPtrog1KPu/vAgeH7bIurKvVraUFkop/WvAKe3dARlegkQH98AUvd0fM5KDuFZLIZeOQ3sYe8RPINaaRsW5N1FpS/aEuFZjRCF4cOq9jpuDg=; bm_sv=4B8689604118D553EF3392C6D42BB930~YAAQbQ7SFyYjSyOgAQAAzeggXAFZbATkR2AIeVkReK3eiBHFVf4l0bvR5XBMMrY12i7NAq7P1yi7ICYsRJBtHr1Vwx8Zy9sb4kxQ2aFypG9qEGj3CFASMSbhP8/1+qTYuxWgZBoxsuYfKrZSZ4frwECbhTO+L2Vnrzh+ZVNsz6wdRSvBP9BOVhvg14dH3DjxYwys0luP56+f+WYYAQRFzqy0IrBRmu3U+cPUSTJCoXvbkQ7OeaOjMX63L4/lNmPPQfy7VA==~1',
}


BASE_URL = 'https://www.patagonia.com/'
SOURCE_INDEX_PATH = ROOT / 'hc' / '3' / 'patagonia_index.json'
DETAILS_CACHE_PATH = ROOT / 'hc' / '3' / 'patagonia_pdp_details.json'
MERGED_INDEX_PATH = ROOT / 'hc' / '3' / 'patagonia_index_with_details.json'
CATCH_PATH = ROOT / 'hc' / '3' / 'patagonia_data.json'
OUTPUT_FILE = ROOT / 'res' / 'patagonia_result_with_details.csv'
OUTPUT_TS_FILE = ROOT / 'hc' / '3' / 'patagonia_result_with_details.csv'
BLOCKED_BODY_MAX_BYTES = 128
CUSTOM_FIELD_NAMES = (
    'Fit(product.metafields.c_f.fit)',
    'Specs Features(product.metafields.c_f.specs_features)',
    'Materials Care(product.metafields.c_f.materials_care)',
    'Country of Origin(product.metafields.c_f.country_of_origin)',
    'Weight(product.metafields.c_f.weight)',
)
FIELDNAMES = [
    'Type', 'SKU', 'Name', 'Description', 'Sale price', 'Regular price',
    'Categories', 'Tags', 'Images', 'Parent', 'Attribute 1 name',
    'Attribute 1 value(s)', 'Attribute 2 name', 'Attribute 2 value(s)',
    'brand', 'Stock', *CUSTOM_FIELD_NAMES,
]


def _text(nodes):
    return ' '.join(
        ' '.join(' '.join(node.itertext()).split())
        for node in nodes
        if ' '.join(node.itertext()).strip()
    )


def _as_html_paragraph(value):
    value = ' '.join(str(value or '').split())
    return f'<p>{escape_html(value)}</p>' if value else ''


def _accordion_entries(tree, name):
    groups = tree.xpath(f'//div[@data-pdp-accordion-{name}]')
    if not groups:
        return []
    entries = []
    for item in groups[0].xpath('.//li[./h3 or ./p]'):
        if 'init-fit-reviews' in item.get('class', ''):
            continue
        heading = _text(item.xpath('./h3'))
        content = _text(item.xpath('./p'))
        if content:
            entries.append((heading, content))
    return entries


def _entries_as_html(entries):
    parts = []
    for heading, content in entries:
        if heading:
            parts.append(
                f'<p><strong>{escape_html(heading)}</strong><br>'
                f'{escape_html(content)}</p>'
            )
        else:
            parts.append(_as_html_paragraph(content))
    return ''.join(parts)


def _entry_value(entries, heading):
    wanted = heading.casefold()
    for title, value in entries:
        if title.casefold() == wanted:
            return value
    return ''


def _json_ld_items(tree):
    for source in tree.xpath('//script[@type="application/ld+json"]/text()'):
        try:
            payload = json.loads(source)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            yield from (item for item in payload if isinstance(item, Mapping))
        elif isinstance(payload, Mapping):
            yield payload


def _pdp_details(source):
    """Extract the customer-facing description and PDP accordion fields."""
    try:
        tree = html.fromstring(source)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'Could not parse Patagonia PDP HTML: {exc}') from exc

    product_group = next(
        (
            item for item in _json_ld_items(tree)
            if 'ProductGroup' in (
                item.get('@type', []) if isinstance(item.get('@type'), list)
                else [item.get('@type')]
            )
        ),
        {},
    )
    description = _as_html_paragraph(product_group.get('description'))
    if not description:
        description = _as_html_paragraph(_text(tree.xpath(
            '//*[contains(concat(" ", normalize-space(@class), " "), '
            '" pdp-intro__description ")]'
        )))
    if not description:
        raise ValueError('Patagonia PDP has no product description')

    fit = _accordion_entries(tree, 'fit')
    specs = _accordion_entries(tree, 'specs')
    materials = _accordion_entries(tree, 'materials')
    return {
        'description': description,
        CUSTOM_FIELD_NAMES[0]: _entries_as_html(fit[:1]),
        CUSTOM_FIELD_NAMES[1]: _entries_as_html(specs),
        CUSTOM_FIELD_NAMES[2]: _entries_as_html(materials),
        CUSTOM_FIELD_NAMES[3]: _entry_value(specs, 'Country of Origin'),
        CUSTOM_FIELD_NAMES[4]: _entry_value(specs, 'Weight'),
    }


def _is_blocked(response, source_text, max_bytes):
    return (
        len(response.content or b'') <= max_bytes
        and 'not found' in source_text.strip().casefold()
    )


def _fetch_details(url, *, timeout, blocked_body_max_bytes):
    """Use a fresh curl_cffi session for this single PDP request."""
    session = curl_requests.Session(headers=headers, cookies=cookies)
    full_url = urljoin(BASE_URL, url)
    try:
        response = session.get(full_url, timeout=timeout, allow_redirects=True)
        source_text = response.text
        if _is_blocked(response, source_text, blocked_body_max_bytes):
            raise RuntimeError(
                f'blocked short Not found response ({len(response.content or b"")} bytes)'
            )
        try:
            return _pdp_details(source_text)
        except Exception as exc:
            status = int(response.status_code)
            if not 200 <= status < 300:
                raise RuntimeError(f'HTTP {status}; PDP parse failed: {exc}') from exc
            raise
    finally:
        session.close()


def _has_details(rows):
    return bool(rows) and all(
        isinstance(row, dict)
        and bool(str(row.get('Description') or '').strip())
        and all(field in row for field in CUSTOM_FIELD_NAMES)
        for row in rows
    )


def _has_detail_payload(details):
    return (
        isinstance(details, dict)
        and bool(str(details.get('description') or '').strip())
        and all(field in details for field in CUSTOM_FIELD_NAMES)
    )


def _detail_key(url):
    """描述在产品级共享，移除颜色/尺寸查询参数作为缓存键。"""
    parts = urlsplit(str(url or ''))
    return parts.path or str(url).split('?', 1)[0]


def _merge_rows(rows, details):
    return [
        {
            **row,
            'Description': details['description'],
            **{field: details[field] for field in CUSTOM_FIELD_NAMES},
        }
        for row in rows
    ]


def _iter_urls(index_data, details_cache):
    seen = set()
    for url, task_rows in index_data.items():
        if not isinstance(task_rows, dict):
            continue
        rows = next(
            (value for value in task_rows.values() if isinstance(value, list) and value),
            [],
        )
        key = _detail_key(url)
        if (
            rows
            and not _has_details(rows)
            and not _has_detail_payload(details_cache.get(key))
            and key not in seen
        ):
            seen.add(key)
            yield key


def _load_json(path):
    if not path.exists():
        return {}
    with path.open('r', encoding='utf-8') as file:
        return json.load(file)


def _save_json_atomic(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode='w', encoding='utf-8', dir=path.parent, delete=False,
    ) as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        temp_path = Path(file.name)
    os.replace(temp_path, path)


def _save_csv(rows, path, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode='w', encoding='utf-8-sig', newline='', dir=path.parent, delete=False,
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
        temp_path = Path(file.name)
    os.replace(temp_path, path)


def _export_rows(index_data, catch_data):
    rows = []
    for category, tasks in (catch_data or {}).items():
        if not isinstance(tasks, dict):
            continue
        for task in tasks.values():
            if not isinstance(task, dict) or not task.get('url'):
                continue
            entries = index_data.get(task['url'], {})
            if not isinstance(entries, dict):
                continue
            cached = next(
                (value for value in entries.values() if isinstance(value, list) and value),
                [],
            )
            for row in cached:
                output_row = dict(row)
                output_row['Categories'] = category
                rows.append(output_row)
    return rows


def main():
    parser = argparse.ArgumentParser(description='补全 Patagonia 缓存详情字段')
    parser.add_argument('--workers', type=int, default=2, help='curl 并发数，默认 2')
    parser.add_argument('--limit', type=int, default=0, help='只处理前 N 个缺失 URL，0 表示全部')
    parser.add_argument('--timeout', type=int, default=60, help='单个请求超时秒数，默认 60')
    parser.add_argument(
        '--checkpoint-every', type=int, default=25,
        help='每完成多少个 URL 保存一次缓存，默认 25；设为 0 仅结束时保存',
    )
    parser.add_argument(
        '--blocked-body-max-bytes', type=int, default=BLOCKED_BODY_MAX_BYTES,
        help='短 Not found 反爬响应的最大字节数，默认 128',
    )
    parser.add_argument('--no-export', action='store_true', help='只更新 JSON 缓存，不重写 CSV')
    args = parser.parse_args()
    if (
        args.workers < 1 or args.limit < 0 or args.timeout < 1
        or args.blocked_body_max_bytes < 0 or args.checkpoint_every < 0
    ):
        raise ValueError('workers/timeout must be positive; limit/checkpoint/max bytes cannot be negative')

    index_data = _load_json(SOURCE_INDEX_PATH)
    if not isinstance(index_data, dict):
        raise TypeError(f'Invalid index cache: {SOURCE_INDEX_PATH}')
    details_cache = _load_json(DETAILS_CACHE_PATH)
    if not isinstance(details_cache, dict):
        details_cache = {}
    # Normalize older detail-cache entries that used color-specific URLs.
    normalized_details = {}
    for url, details in details_cache.items():
        key = _detail_key(url)
        if _has_detail_payload(details):
            normalized_details[key] = details
    details_cache = normalized_details
    pending = list(_iter_urls(index_data, details_cache))
    if args.limit:
        pending = pending[:args.limit]
    print(f'主缓存（只读）：{SOURCE_INDEX_PATH}')
    print(f'详情缓存（增量写入）：{DETAILS_CACHE_PATH}')
    print(f'需要补全 PDP 字段的 URL：{len(pending)} 个')

    success = failed = 0
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                _fetch_details, url, timeout=args.timeout,
                blocked_body_max_bytes=args.blocked_body_max_bytes,
            ): url
            for url in pending
        }
        for future in as_completed(futures):
            url = futures[future]
            try:
                details = future.result()
                details_cache[url] = details
                with lock:
                    success += 1
                    if success % 25 == 0 or success == len(pending):
                        print(f'已补全 {success}/{len(pending)} 个 URL')
                    if args.checkpoint_every and success % args.checkpoint_every == 0:
                        _save_json_atomic(details_cache, DETAILS_CACHE_PATH)
                        print(f'已保存详情断点：{success}/{len(pending)}')
            except Exception as exc:
                with lock:
                    failed += 1
                print(f'[DETAIL FAILED] {url} | {exc}')

    # Merge the small durable details cache into the large variation cache once.
    for url, entries in index_data.items():
        details = details_cache.get(_detail_key(url))
        if not isinstance(entries, dict) or not _has_detail_payload(details):
            continue
        for task_id, rows in list(entries.items()):
            if isinstance(rows, list) and rows:
                entries[task_id] = _merge_rows(rows, details)
    _save_json_atomic(details_cache, DETAILS_CACHE_PATH)
    _save_json_atomic(index_data, MERGED_INDEX_PATH)
    print(f'合并缓存已输出：{MERGED_INDEX_PATH}')
    print(f'缓存更新完成：成功 {success}，失败 {failed}')

    if not args.no_export:
        catch_data = _load_json(CATCH_PATH)
        rows = _export_rows(index_data, catch_data)
        _save_csv(rows, OUTPUT_TS_FILE, FIELDNAMES)
        _save_csv([{key: value for key, value in row.items() if key != 'url'} for row in rows], OUTPUT_FILE, FIELDNAMES)
        print(f'CSV 已同步：{len(rows)} 行')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
