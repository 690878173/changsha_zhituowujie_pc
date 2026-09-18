import json
import re

from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')


cookies = {
    'guest_token': 'eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaEpJaHRIYTFKTmMzaFBSbGhyUzNKVVQwa3hkM2Q0Y1dSM0Jqb0dSVVk9IiwiZXhwIjpudWxsLCJwdXIiOiJjb29raWUuZ3Vlc3RfdG9rZW4ifX0%3D--12aaacad48e2c95f54576a6315888a44cb2ac78e',
    '_session_id': '0d7090400ad1aee07a5cb97124fbb701',
    'FPC': 'f76a1684-4d46-4c2e-b62a-2794f8111675',
    '__attn_eat_id': '92fde8ec7b15475f8fb23c87fbeddaf5',
    '_gcl_au': '1.1.1469880196.1787535861.-.-.1787535862.1524398406.1787535863.1787535862',
    '_ga': 'GA1.1.1096728710.1787535863',
    '_ga_59L0QDKBLT': 'GS2.1.s1787535862$o1$g0$t1787535862$j60$l0$h0$drRf_qjtD2W9L-DVRQliP34KnXJ4yjsB0_A',
    'has_visited_before': 'true',
    'suppress_gate_for_visit': 'true',
    '_ga_KDVZE23CS0': 'GS2.1.s1787535862$o1$g0$t1787535863$j59$l0$h806380685$dlDwBIeriiiGSKzj37IIN7lEa2pa1yJaNHw',
    'polaris_consent_settings': '{"clientId":"20551361-0179-4fd3-cd46-2fa8423bbcde","implicit":true,"analyticsPermitted":true,"personalizationPermitted":true,"adsPermitted":true,"notOptedOut":true,"essentialPermitted":true}',
    'sms_prompt_last_viewed': '1787535863193',
    'cf_clearance': 'aiy3yFrNeneRJP8KiruBi9oOgtW7I.yuyxYucl6C10A-1787535864-1.2.1.1-FMe_oa_PEqt4ybFBXbPmPARjHURmwOCUbefjq_KWzgenCM91iYTXEg29BkZ85W5Rb2ruSjesk5_sHMzhojG5tTkU774SwWjzjbE6DoDNLdr9XBQh9kBrrihtPBTB4BZliYJD3uL.EAW.BFgKJhKC2SyP0USWTUntVGxWWIJ2EqyaLw3nPn_JNH2DvuAIOsnUFpWFKWuKCjb.vKLg5eVTCa0.lOzMck4.Tz9B64wynilrhPxPyulFSxJytNxaSQ6ouLFTCITcCGBJ3kXpyXmRHUhog9xz7DKEQ2hLdOHdtcRSEieMUgjiaDnCfCBGyHTGlnjLeYUXo06zzVMEbMNsNkUR7OgoOVarj9z9WEV7yTA',
    '__cf_bm': 'xOuJKA2Gu1tI6drnxErMWXPLZIR2V1FTYc3SJrUz_7w-1787535863.9940724-1.0.1.1-R2olrIrFICxXmeaaejG42upXX44bnASxL13Iit2NUbRYL_ADKOgofdWie2QKZ791XM0rH60ZQcoK36x5wNAKvUB48jmOslNA.OeMzaaEZYDtth1dzplUnU85jtZNEfZL',
    'tatari-cookie-test': '29887013',
    'tatari-session-cookie': '7e5fcc21-1c0f-f870-b169-7bfef17ddd9e',
    '__attentive_id': '6a7572e18b8546859c24b07513719b2c',
    '__attentive_session_id': 'f34ea2e81dc847f5b4cee8408e61e019',
    '_attn_': 'eyJ1Ijoie1wiY29cIjoxNzg3NTM1ODYzNTQwLFwidW9cIjoxNzg3NTM1ODYzNTQwLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjZhNzU3MmUxOGI4NTQ2ODU5YzI0YjA3NTEzNzE5YjJjXCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg3NTM1ODYzNTM3LFwidW9cIjoxNzg3NTM1ODYzNTM3LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL3NtYXpuLmh1Y2tiZXJyeS5jb21cIn0ifQ==',
    '__attentive_cco': '1787535863540',
    '_attn_bopd_': 'browser',
    '__attentive_dv': '1',
    '__attentive_pv': '1',
    '__attentive_ss_referrer': 'ORGANIC',
    'us_privacy': '1YNN',
    'fingerprint-uuid': '6a3c4b5c-f3dd-4be0-9a65-7849a744aaed',
    'gleen-faq-fingerprint-uuid': '6a3c4b5c-f3dd-4be0-9a65-7849a744aaed',
    '_swb': '9d30ae23-bd28-4240-b0ee-4f77135497a3',
    '__ssid': '3ea71818-a04c-4e8e-b603-a6495ca5441d',
    '_ketch_consent_v1_': 'eyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIl19LCJhbmFseXRpY3MiOnsic3RhdHVzIjoiZ3JhbnRlZCIsImNhbm9uaWNhbFB1cnBvc2VzIjpbImFuYWx5dGljcyJdfSwiZXNzZW50aWFsX3NlcnZpY2VzIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJlc3NlbnRpYWxfc2VydmljZXMiXX19',
    '_swb_consent_': 'eyJjb2xsZWN0ZWRBdCI6MTc4NzUzNTg2NSwiY29udGV4dCI6eyJjb25maWd1cmF0aW9uSWQiOiJhSFZqYTJKbGNuSjVMMmgxWTJ0aVpYSnllUzl3Y205a2RXTjBhVzl1TDJOd2NtRXZaVzR2TVRjNE5EVTJNekF4T0E9PSIsImlzc3VlZEF0IjowLCJzb3VyY2UiOiJsZWdhbEJhc2lzRGVmYXVsdCJ9LCJjb250cm9sbGVyQ29kZSI6IiIsImVudmlyb25tZW50Q29kZSI6InByb2R1Y3Rpb24iLCJpZGVudGl0aWVzIjp7InN3Yl9odWNrYmVycnkiOiI5ZDMwYWUyMy1iZDI4LTQyNDAtYjBlZS00Zjc3MTM1NDk3YTMifSwianVyaXNkaWN0aW9uQ29kZSI6ImNwcmEiLCJwcm9wZXJ0eUNvZGUiOiJodWNrYmVycnkiLCJwdXJwb3NlcyI6eyJhbmFseXRpY3MiOnsiYWxsb3dlZCI6InRydWUiLCJjb2xsZWN0ZWRBdCI6MCwiaXNzdWVkQXQiOjAsImxlZ2FsQmFzaXNDb2RlIjoiY29uc2VudF9vcHRvdXQiLCJzb3VyY2UiOiIifSwiYmVoYXZpb3JhbF9hZHZlcnRpc2luZyI6eyJhbGxvd2VkIjoidHJ1ZSIsImNvbGxlY3RlZEF0IjowLCJpc3N1ZWRBdCI6MCwibGVnYWxCYXNpc0NvZGUiOiJjb25zZW50X29wdG91dCIsInNvdXJjZSI6IiJ9LCJlc3NlbnRpYWxfc2VydmljZXMiOnsiYWxsb3dlZCI6InRydWUiLCJjb2xsZWN0ZWRBdCI6MCwiaXNzdWVkQXQiOjAsImxlZ2FsQmFzaXNDb2RlIjoiZGlzY2xvc3VyZSIsInNvdXJjZSI6IiJ9fSwiaW50ZXJhY3RpdmUiOmZhbHNlLCJjYWNoZWRBdCI6MTc4NzUzNTg2Nn0%3D',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    # 'cookie': 'guest_token=eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaEpJaHRIYTFKTmMzaFBSbGhyUzNKVVQwa3hkM2Q0Y1dSM0Jqb0dSVVk9IiwiZXhwIjpudWxsLCJwdXIiOiJjb29raWUuZ3Vlc3RfdG9rZW4ifX0%3D--12aaacad48e2c95f54576a6315888a44cb2ac78e; _session_id=0d7090400ad1aee07a5cb97124fbb701; FPC=f76a1684-4d46-4c2e-b62a-2794f8111675; __attn_eat_id=92fde8ec7b15475f8fb23c87fbeddaf5; _gcl_au=1.1.1469880196.1787535861.-.-.1787535862.1524398406.1787535863.1787535862; _ga=GA1.1.1096728710.1787535863; _ga_59L0QDKBLT=GS2.1.s1787535862$o1$g0$t1787535862$j60$l0$h0$drRf_qjtD2W9L-DVRQliP34KnXJ4yjsB0_A; has_visited_before=true; suppress_gate_for_visit=true; _ga_KDVZE23CS0=GS2.1.s1787535862$o1$g0$t1787535863$j59$l0$h806380685$dlDwBIeriiiGSKzj37IIN7lEa2pa1yJaNHw; polaris_consent_settings={"clientId":"20551361-0179-4fd3-cd46-2fa8423bbcde","implicit":true,"analyticsPermitted":true,"personalizationPermitted":true,"adsPermitted":true,"notOptedOut":true,"essentialPermitted":true}; sms_prompt_last_viewed=1787535863193; cf_clearance=aiy3yFrNeneRJP8KiruBi9oOgtW7I.yuyxYucl6C10A-1787535864-1.2.1.1-FMe_oa_PEqt4ybFBXbPmPARjHURmwOCUbefjq_KWzgenCM91iYTXEg29BkZ85W5Rb2ruSjesk5_sHMzhojG5tTkU774SwWjzjbE6DoDNLdr9XBQh9kBrrihtPBTB4BZliYJD3uL.EAW.BFgKJhKC2SyP0USWTUntVGxWWIJ2EqyaLw3nPn_JNH2DvuAIOsnUFpWFKWuKCjb.vKLg5eVTCa0.lOzMck4.Tz9B64wynilrhPxPyulFSxJytNxaSQ6ouLFTCITcCGBJ3kXpyXmRHUhog9xz7DKEQ2hLdOHdtcRSEieMUgjiaDnCfCBGyHTGlnjLeYUXo06zzVMEbMNsNkUR7OgoOVarj9z9WEV7yTA; __cf_bm=xOuJKA2Gu1tI6drnxErMWXPLZIR2V1FTYc3SJrUz_7w-1787535863.9940724-1.0.1.1-R2olrIrFICxXmeaaejG42upXX44bnASxL13Iit2NUbRYL_ADKOgofdWie2QKZ791XM0rH60ZQcoK36x5wNAKvUB48jmOslNA.OeMzaaEZYDtth1dzplUnU85jtZNEfZL; tatari-cookie-test=29887013; tatari-session-cookie=7e5fcc21-1c0f-f870-b169-7bfef17ddd9e; __attentive_id=6a7572e18b8546859c24b07513719b2c; __attentive_session_id=f34ea2e81dc847f5b4cee8408e61e019; _attn_=eyJ1Ijoie1wiY29cIjoxNzg3NTM1ODYzNTQwLFwidW9cIjoxNzg3NTM1ODYzNTQwLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjZhNzU3MmUxOGI4NTQ2ODU5YzI0YjA3NTEzNzE5YjJjXCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg3NTM1ODYzNTM3LFwidW9cIjoxNzg3NTM1ODYzNTM3LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL3NtYXpuLmh1Y2tiZXJyeS5jb21cIn0ifQ==; __attentive_cco=1787535863540; _attn_bopd_=browser; __attentive_dv=1; __attentive_pv=1; __attentive_ss_referrer=ORGANIC; us_privacy=1YNN; fingerprint-uuid=6a3c4b5c-f3dd-4be0-9a65-7849a744aaed; gleen-faq-fingerprint-uuid=6a3c4b5c-f3dd-4be0-9a65-7849a744aaed; _swb=9d30ae23-bd28-4240-b0ee-4f77135497a3; __ssid=3ea71818-a04c-4e8e-b603-a6495ca5441d; _ketch_consent_v1_=eyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIl19LCJhbmFseXRpY3MiOnsic3RhdHVzIjoiZ3JhbnRlZCIsImNhbm9uaWNhbFB1cnBvc2VzIjpbImFuYWx5dGljcyJdfSwiZXNzZW50aWFsX3NlcnZpY2VzIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJlc3NlbnRpYWxfc2VydmljZXMiXX19; _swb_consent_=eyJjb2xsZWN0ZWRBdCI6MTc4NzUzNTg2NSwiY29udGV4dCI6eyJjb25maWd1cmF0aW9uSWQiOiJhSFZqYTJKbGNuSjVMMmgxWTJ0aVpYSnllUzl3Y205a2RXTjBhVzl1TDJOd2NtRXZaVzR2TVRjNE5EVTJNekF4T0E9PSIsImlzc3VlZEF0IjowLCJzb3VyY2UiOiJsZWdhbEJhc2lzRGVmYXVsdCJ9LCJjb250cm9sbGVyQ29kZSI6IiIsImVudmlyb25tZW50Q29kZSI6InByb2R1Y3Rpb24iLCJpZGVudGl0aWVzIjp7InN3Yl9odWNrYmVycnkiOiI5ZDMwYWUyMy1iZDI4LTQyNDAtYjBlZS00Zjc3MTM1NDk3YTMifSwianVyaXNkaWN0aW9uQ29kZSI6ImNwcmEiLCJwcm9wZXJ0eUNvZGUiOiJodWNrYmVycnkiLCJwdXJwb3NlcyI6eyJhbmFseXRpY3MiOnsiYWxsb3dlZCI6InRydWUiLCJjb2xsZWN0ZWRBdCI6MCwiaXNzdWVkQXQiOjAsImxlZ2FsQmFzaXNDb2RlIjoiY29uc2VudF9vcHRvdXQiLCJzb3VyY2UiOiIifSwiYmVoYXZpb3JhbF9hZHZlcnRpc2luZyI6eyJhbGxvd2VkIjoidHJ1ZSIsImNvbGxlY3RlZEF0IjowLCJpc3N1ZWRBdCI6MCwibGVnYWxCYXNpc0NvZGUiOiJjb25zZW50X29wdG91dCIsInNvdXJjZSI6IiJ9LCJlc3NlbnRpYWxfc2VydmljZXMiOnsiYWxsb3dlZCI6InRydWUiLCJjb2xsZWN0ZWRBdCI6MCwiaXNzdWVkQXQiOjAsImxlZ2FsQmFzaXNDb2RlIjoiZGlzY2xvc3VyZSIsInNvdXJjZSI6IiJ9fSwiaW50ZXJhY3RpdmUiOmZhbHNlLCJjYWNoZWRBdCI6MTc4NzUzNTg2Nn0%3D',
}






@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url,headers=headers,cookies=cookies)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    match = re.search(r'__PRELOADED_STATE__\.navigation\s*=\s*({.*?});', res.text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            print(data)  # 输出字典
            Tool.File.save_json(data,'hc/1.json')
        except json.JSONDecodeError:
            print("不是合法 JSON，请尝试方案二")



    data = data['headings']


    header_node = data


    for node in header_node:
        payload = node['payload']
        _name = payload['title']
        _url = payload['url']
        _url = Tool.URL.add_site(_url)

        url_dic[_name] = {'url':_url,'child':{}}

        childs1 = node['elements']
        discover = payload.get('discover',None)

        childs = {'childs':childs1,'discover':discover}

        f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):



    for child in childs['childs']:
        payload = child['payload']
        _name = payload['title']
        _url = payload['url']
        _url = Tool.URL.add_site(_url)


        dic[_name] = {'url': _url, 'child': {}}

        n_childs_ls = child['elements']
        f3(dic[_name]['child'],n_childs_ls)

    if childs['discover']:
        title = childs['discover']['title']
        dic[title] = {'child':{}}
        for i in childs['discover']['items']:
            _title = i['title']
            _url = i['url']
            _url = Tool.URL.add_site(_url)
            dic[title]['child'][_title] = {'url':_url,'child':{}}


    return dic


def f3(dic,childs):
    for child in childs:
        payload = child['payload']
        _name = payload['title']
        _url = payload['url']
        _url = Tool.URL.add_site(_url)

        dic[_name] = {'url': _url, 'child': {}}

        n_childs_ls = child['elements']

        dic[_name] = {'url': _url, 'child': {}}


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



