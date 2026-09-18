import re

from lxml import etree

from config import Tool

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')

catch_path = Tool.File.path_add_site('hc/2/data.json')
index_path = Tool.File.path_add_site('hc/2/index.json')

# 测试数据条数,以初始url数量计数
ts_num = None

# 排除某些 URL（输入分类黑名单）
skip_input_url_ls = ['https://huckberry.com']
# 输出商品链接黑名单
skip_output_url_ls = []

# 覆盖缓存：True=无视本地缓存强制重新请求
flush = False

catch_save_num = None


cookies = {
    'guest_token': 'eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaEpJaHRzUVhSbVkxQndVblV3Wkc5WWFFTnVja0UyU0ROM0Jqb0dSVVk9IiwiZXhwIjpudWxsLCJwdXIiOiJjb29raWUuZ3Vlc3RfdG9rZW4ifX0%3D--571360ee22d9232356ef8abd492c09023e38db66',
    '_session_id': '03a2cb4087ae612106e55052a4f0d880',
    'has_visited_before': 'true',
    'suppress_gate_for_visit': 'true',
    'sms_prompt_last_viewed': '1787553247639',
    'cf_clearance': 'ZnGM_iBTdq6wkPfBVPpvbAZpOEsSWbhn2oiGW4gOkeM-1787553248-1.2.1.1-QkbB8CS_2r9Hoy54Q_5dFOsW14F7Y3R5m7ZwOTsKh4s8UOhE6FGrTRmMMiN3xHoJp_6FQG4cebry2aMOvsY7Q0VxfuXnnS2HYBwCa6MGr90GOSoCJQkzrBG1Z_Q7R5BB71Y.RpXQSuzvuuxOCx7aqQVHHJ7HZrYjBleNgsWK9TzTuQRfV6Ue2aVpMhpjLlBJ.u.yzLR1KjaFfgnrwxRYsbO19T4o1RZ8ffygqNsSKYJ9qP_rGO_Ifw6iGgsKZeI2SKOsoTFAz_zqXu4ud6hXlGuVD7dnkRVD.Au1AaTyBTZvXRLYwsIMyjVs_Njc1SaNKPcMLFODDtdYinUkyjhNGle.RLc1uG1jZPdlFxAaG08',
    'styliticsWidgetSession': 'e6659008-195b-4c0f-9c54-0e22999014ce',
    '__cf_bm': '8.YVm6WhIv4j0We1CvaoIsHuNwInWOPNBPcZWRI8Kvk-1787553249.6161616-1.0.1.1-65K7VdrOwusQinPIWph5hYyxMhHZe0Q8Enw_eY.Ds121qz.FZBv7zefAZNWXWm3lqpcqQGGDZ6spYUsq_ZFnp663EEknSZ7ZZyN2cVYuasfPzYqZHqTzgbKLq3XsrPH4',
    '_swb': 'c304fb6f-0e73-49c7-94d4-c3496db1310a',
    '__ssid': '9a7330e5-bec8-48a6-975a-5fcbaa56c5d6',
    '_ketch_consent_v1_': 'eyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIl19LCJhbmFseXRpY3MiOnsic3RhdHVzIjoiZ3JhbnRlZCIsImNhbm9uaWNhbFB1cnBvc2VzIjpbImFuYWx5dGljcyJdfSwiZXNzZW50aWFsX3NlcnZpY2VzIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJlc3NlbnRpYWxfc2VydmljZXMiXX19',
    '_swb_consent_': 'eyJjb2xsZWN0ZWRBdCI6MTc4NzU1MzI1MCwiY29udGV4dCI6eyJjb25maWd1cmF0aW9uSWQiOiJhSFZqYTJKbGNuSjVMMmgxWTJ0aVpYSnllUzl3Y205a2RXTjBhVzl1TDJOd2NtRXZaVzR2TVRjNE5EVTJNekF4T0E9PSIsImlzc3VlZEF0IjowLCJzb3VyY2UiOiJsZWdhbEJhc2lzRGVmYXVsdCJ9LCJjb250cm9sbGVyQ29kZSI6IiIsImVudmlyb25tZW50Q29kZSI6InByb2R1Y3Rpb24iLCJpZGVudGl0aWVzIjp7InN3Yl9odWNrYmVycnkiOiJjMzA0ZmI2Zi0wZTczLTQ5YzctOTRkNC1jMzQ5NmRiMTMxMGEifSwianVyaXNkaWN0aW9uQ29kZSI6ImNwcmEiLCJwcm9wZXJ0eUNvZGUiOiJodWNrYmVycnkiLCJwdXJwb3NlcyI6eyJhbmFseXRpY3MiOnsiYWxsb3dlZCI6InRydWUiLCJjb2xsZWN0ZWRBdCI6MCwiaXNzdWVkQXQiOjAsImxlZ2FsQmFzaXNDb2RlIjoiY29uc2VudF9vcHRvdXQiLCJzb3VyY2UiOiIifSwiYmVoYXZpb3JhbF9hZHZlcnRpc2luZyI6eyJhbGxvd2VkIjoidHJ1ZSIsImNvbGxlY3RlZEF0IjowLCJpc3N1ZWRBdCI6MCwibGVnYWxCYXNpc0NvZGUiOiJjb25zZW50X29wdG91dCIsInNvdXJjZSI6IiJ9LCJlc3NlbnRpYWxfc2VydmljZXMiOnsiYWxsb3dlZCI6InRydWUiLCJjb2xsZWN0ZWRBdCI6MCwiaXNzdWVkQXQiOjAsImxlZ2FsQmFzaXNDb2RlIjoiZGlzY2xvc3VyZSIsInNvdXJjZSI6IiJ9fSwiaW50ZXJhY3RpdmUiOmZhbHNlLCJjYWNoZWRBdCI6MTc4NzU1MzI1MH0%3D',
    'rl_anonymous_id': 'RS_ENC_v3_IjhjZmU5NDk4LWU2ZjctNGQzOS1hNDcyLTcyNzViMjg5OTI5ZSI%3D',
    'rl_page_init_referrer': 'RS_ENC_v3_IiRkaXJlY3Qi',
    'decrypted_rl_anonymous_id': '8cfe9498-e6f7-4d39-a472-7275b289929e',
    'FPC': '707326f3-b0c3-44d8-83d0-2e39fa6ca234',
    '_ga': 'GA1.1.207434078.1787553256',
    '_fbp': 'fb.1.1787553255708.661246161556739077',
    '_pin_unauth': 'dWlkPU1URTVZemc0WWpBdFpUUmxOUzAwTmpkaUxXSTJOall0TlRobFlUSTVOek01TlRZMw',
    '_twpid': 'tw.1787553256189.157970711777512744',
    '_rdt_uuid': '1787553256259.ef3c4f51-9cb2-437c-90fe-474d8d17d953',
    'polaris_consent_settings': '{"clientId":"945c786d-d146-4ae6-ad02-796e9ea059c9","implicit":true,"analyticsPermitted":true,"personalizationPermitted":true,"adsPermitted":true,"notOptedOut":true,"essentialPermitted":true}',
    'us_privacy': '1YNN',
    'mp_huckberry_mixpanel': '%7B%22distinct_id%22%3A%20%221a0327a1773938-0323a4fa36985a8-26071851-190140-1a0327a17742978%22%2C%22bc_persist_updated%22%3A%201787553257333%7D',
    'tatari-cookie-test': '91987555',
    'tatari-session-cookie': '5af3df38-c23f-eb3c-54f7-249117532486',
    'bc_invalidateUrlCache_targeting': '1787553257393',
    '__attn_eat_id': '102b6577c66242efa72375e76b7faabf',
    '__attentive_id': '93500b34824d49499c51124eb583bc64',
    '__attentive_session_id': 'ff4bc9fae80e4788a2e07bbe7ee819a1',
    '_attn_': 'eyJ1Ijoie1wiY29cIjoxNzg3NTUzMjU3NDYwLFwidW9cIjoxNzg3NTUzMjU3NDYwLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjkzNTAwYjM0ODI0ZDQ5NDk5YzUxMTI0ZWI1ODNiYzY0XCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg3NTUzMjU3NDU1LFwidW9cIjoxNzg3NTUzMjU3NDU1LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL3NtYXpuLmh1Y2tiZXJyeS5jb21cIn0ifQ==',
    '__attentive_cco': '1787553257461',
    '_tt_enable_cookie': '1',
    '_ttp': '01M0S7M63XA5M2VPPY7WHYH9G0_.tt.1',
    'fingerprint-uuid': 'f0ac18a1-1fe8-4257-b66c-940626839400',
    'gleen-faq-fingerprint-uuid': 'f0ac18a1-1fe8-4257-b66c-940626839400',
    '__qca': 'P1-34bf6296-8366-420c-a1c5-f053deedc880',
    'bluecoreNV': 'true',
    '__attentive_ss_referrer': 'ORGANIC',
    '__attentive_dv': '1',
    '_attn_bopd_': 'none',
    '_clck': 'ah3yft%5E2%5Eg8v%5E1%5E2427',
    '_gcl_au': '1.1.40563347.1787553256.-.-.1787553256.1506707226.1787553256.1787553263',
    '__attentive_pv': '2',
    '_clsk': '1beuhup%5E1787553264319%5E2%5E1%5Eo.clarity.ms%2Fcollect',
    'avmws': '1.10233398736a8be5ea92e0d620391069.105342077.1787553258.1787553265.2.2597425387',
    '_ga_59L0QDKBLT': 'GS2.1.s1787553255$o1$g1$t1787553264$j51$l0$h0',
    'yotpo_pixel': '08cc3c9b-df05-4975-bd0a-09ecfe57d2e8',
    '_sp_id.accb': '3dda0097f4bfd10d.1787553267.1.1787553267.1787553267',
    '_sp_ses.accb': '*',
    'apt_pixel': 'eyJkZXZpY2VJZCI6ImNjOTQ0ZjkzLWEzN2ItNGExMS1hMjIwLTM2MmFmN2JlYjAxNCIsInVzZXJJZCI6bnVsbCwiZXZlbnRJZCI6MSwibGFzdEV2ZW50VGltZSI6MTc4NzU1MzI2NzE2NiwiY2hlY2tvdXQiOnsiYnJhbmQiOiJjYXNoYXBwYWZ0ZXJwYXkifX0=',
    'amp_f24a38': 'ri2oB8iO8amBlQ7eCIL9Fj...1k0p7kffb.1k0p7kffb.0.0.0',
    'ttcsid': '1787553257602::eROFhqRB3q3baWWnnJKn.1.1787553273000.0::1.5900.0::15394.3.1402.23::6042.3.0',
    'ttcsid_CF8PCRRC77U2ISB9LENG': '1787553257602::5j78U5yhoIWJOpnGi8qn.1.1787553273000.1',
    'rl_session': 'RS_ENC_v3_eyJpZCI6MTc4NzU1MzI1MjkwMSwiZXhwaXJlc0F0IjoxNzg3NTU1MDczMDAzLCJ0aW1lb3V0IjoxODAwMDAwLCJhdXRvVHJhY2siOnRydWUsInNlc3Npb25TdGFydCI6ZmFsc2V9',
    '_ga_KDVZE23CS0': 'GS2.1.s1787553255$o1$g1$t1787553273$j42$l0$h939216548',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
    # 'cookie': 'guest_token=eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaEpJaHRzUVhSbVkxQndVblV3Wkc5WWFFTnVja0UyU0ROM0Jqb0dSVVk9IiwiZXhwIjpudWxsLCJwdXIiOiJjb29raWUuZ3Vlc3RfdG9rZW4ifX0%3D--571360ee22d9232356ef8abd492c09023e38db66; _session_id=03a2cb4087ae612106e55052a4f0d880; has_visited_before=true; suppress_gate_for_visit=true; sms_prompt_last_viewed=1787553247639; cf_clearance=ZnGM_iBTdq6wkPfBVPpvbAZpOEsSWbhn2oiGW4gOkeM-1787553248-1.2.1.1-QkbB8CS_2r9Hoy54Q_5dFOsW14F7Y3R5m7ZwOTsKh4s8UOhE6FGrTRmMMiN3xHoJp_6FQG4cebry2aMOvsY7Q0VxfuXnnS2HYBwCa6MGr90GOSoCJQkzrBG1Z_Q7R5BB71Y.RpXQSuzvuuxOCx7aqQVHHJ7HZrYjBleNgsWK9TzTuQRfV6Ue2aVpMhpjLlBJ.u.yzLR1KjaFfgnrwxRYsbO19T4o1RZ8ffygqNsSKYJ9qP_rGO_Ifw6iGgsKZeI2SKOsoTFAz_zqXu4ud6hXlGuVD7dnkRVD.Au1AaTyBTZvXRLYwsIMyjVs_Njc1SaNKPcMLFODDtdYinUkyjhNGle.RLc1uG1jZPdlFxAaG08; styliticsWidgetSession=e6659008-195b-4c0f-9c54-0e22999014ce; __cf_bm=8.YVm6WhIv4j0We1CvaoIsHuNwInWOPNBPcZWRI8Kvk-1787553249.6161616-1.0.1.1-65K7VdrOwusQinPIWph5hYyxMhHZe0Q8Enw_eY.Ds121qz.FZBv7zefAZNWXWm3lqpcqQGGDZ6spYUsq_ZFnp663EEknSZ7ZZyN2cVYuasfPzYqZHqTzgbKLq3XsrPH4; _swb=c304fb6f-0e73-49c7-94d4-c3496db1310a; __ssid=9a7330e5-bec8-48a6-975a-5fcbaa56c5d6; _ketch_consent_v1_=eyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJiZWhhdmlvcmFsX2FkdmVydGlzaW5nIl19LCJhbmFseXRpY3MiOnsic3RhdHVzIjoiZ3JhbnRlZCIsImNhbm9uaWNhbFB1cnBvc2VzIjpbImFuYWx5dGljcyJdfSwiZXNzZW50aWFsX3NlcnZpY2VzIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJlc3NlbnRpYWxfc2VydmljZXMiXX19; _swb_consent_=eyJjb2xsZWN0ZWRBdCI6MTc4NzU1MzI1MCwiY29udGV4dCI6eyJjb25maWd1cmF0aW9uSWQiOiJhSFZqYTJKbGNuSjVMMmgxWTJ0aVpYSnllUzl3Y205a2RXTjBhVzl1TDJOd2NtRXZaVzR2TVRjNE5EVTJNekF4T0E9PSIsImlzc3VlZEF0IjowLCJzb3VyY2UiOiJsZWdhbEJhc2lzRGVmYXVsdCJ9LCJjb250cm9sbGVyQ29kZSI6IiIsImVudmlyb25tZW50Q29kZSI6InByb2R1Y3Rpb24iLCJpZGVudGl0aWVzIjp7InN3Yl9odWNrYmVycnkiOiJjMzA0ZmI2Zi0wZTczLTQ5YzctOTRkNC1jMzQ5NmRiMTMxMGEifSwianVyaXNkaWN0aW9uQ29kZSI6ImNwcmEiLCJwcm9wZXJ0eUNvZGUiOiJodWNrYmVycnkiLCJwdXJwb3NlcyI6eyJhbmFseXRpY3MiOnsiYWxsb3dlZCI6InRydWUiLCJjb2xsZWN0ZWRBdCI6MCwiaXNzdWVkQXQiOjAsImxlZ2FsQmFzaXNDb2RlIjoiY29uc2VudF9vcHRvdXQiLCJzb3VyY2UiOiIifSwiYmVoYXZpb3JhbF9hZHZlcnRpc2luZyI6eyJhbGxvd2VkIjoidHJ1ZSIsImNvbGxlY3RlZEF0IjowLCJpc3N1ZWRBdCI6MCwibGVnYWxCYXNpc0NvZGUiOiJjb25zZW50X29wdG91dCIsInNvdXJjZSI6IiJ9LCJlc3NlbnRpYWxfc2VydmljZXMiOnsiYWxsb3dlZCI6InRydWUiLCJjb2xsZWN0ZWRBdCI6MCwiaXNzdWVkQXQiOjAsImxlZ2FsQmFzaXNDb2RlIjoiZGlzY2xvc3VyZSIsInNvdXJjZSI6IiJ9fSwiaW50ZXJhY3RpdmUiOmZhbHNlLCJjYWNoZWRBdCI6MTc4NzU1MzI1MH0%3D; rl_anonymous_id=RS_ENC_v3_IjhjZmU5NDk4LWU2ZjctNGQzOS1hNDcyLTcyNzViMjg5OTI5ZSI%3D; rl_page_init_referrer=RS_ENC_v3_IiRkaXJlY3Qi; decrypted_rl_anonymous_id=8cfe9498-e6f7-4d39-a472-7275b289929e; FPC=707326f3-b0c3-44d8-83d0-2e39fa6ca234; _ga=GA1.1.207434078.1787553256; _fbp=fb.1.1787553255708.661246161556739077; _pin_unauth=dWlkPU1URTVZemc0WWpBdFpUUmxOUzAwTmpkaUxXSTJOall0TlRobFlUSTVOek01TlRZMw; _twpid=tw.1787553256189.157970711777512744; _rdt_uuid=1787553256259.ef3c4f51-9cb2-437c-90fe-474d8d17d953; polaris_consent_settings={"clientId":"945c786d-d146-4ae6-ad02-796e9ea059c9","implicit":true,"analyticsPermitted":true,"personalizationPermitted":true,"adsPermitted":true,"notOptedOut":true,"essentialPermitted":true}; us_privacy=1YNN; mp_huckberry_mixpanel=%7B%22distinct_id%22%3A%20%221a0327a1773938-0323a4fa36985a8-26071851-190140-1a0327a17742978%22%2C%22bc_persist_updated%22%3A%201787553257333%7D; tatari-cookie-test=91987555; tatari-session-cookie=5af3df38-c23f-eb3c-54f7-249117532486; bc_invalidateUrlCache_targeting=1787553257393; __attn_eat_id=102b6577c66242efa72375e76b7faabf; __attentive_id=93500b34824d49499c51124eb583bc64; __attentive_session_id=ff4bc9fae80e4788a2e07bbe7ee819a1; _attn_=eyJ1Ijoie1wiY29cIjoxNzg3NTUzMjU3NDYwLFwidW9cIjoxNzg3NTUzMjU3NDYwLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjkzNTAwYjM0ODI0ZDQ5NDk5YzUxMTI0ZWI1ODNiYzY0XCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg3NTUzMjU3NDU1LFwidW9cIjoxNzg3NTUzMjU3NDU1LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL3NtYXpuLmh1Y2tiZXJyeS5jb21cIn0ifQ==; __attentive_cco=1787553257461; _tt_enable_cookie=1; _ttp=01M0S7M63XA5M2VPPY7WHYH9G0_.tt.1; fingerprint-uuid=f0ac18a1-1fe8-4257-b66c-940626839400; gleen-faq-fingerprint-uuid=f0ac18a1-1fe8-4257-b66c-940626839400; __qca=P1-34bf6296-8366-420c-a1c5-f053deedc880; bluecoreNV=true; __attentive_ss_referrer=ORGANIC; __attentive_dv=1; _attn_bopd_=none; _clck=ah3yft%5E2%5Eg8v%5E1%5E2427; _gcl_au=1.1.40563347.1787553256.-.-.1787553256.1506707226.1787553256.1787553263; __attentive_pv=2; _clsk=1beuhup%5E1787553264319%5E2%5E1%5Eo.clarity.ms%2Fcollect; avmws=1.10233398736a8be5ea92e0d620391069.105342077.1787553258.1787553265.2.2597425387; _ga_59L0QDKBLT=GS2.1.s1787553255$o1$g1$t1787553264$j51$l0$h0; yotpo_pixel=08cc3c9b-df05-4975-bd0a-09ecfe57d2e8; _sp_id.accb=3dda0097f4bfd10d.1787553267.1.1787553267.1787553267; _sp_ses.accb=*; apt_pixel=eyJkZXZpY2VJZCI6ImNjOTQ0ZjkzLWEzN2ItNGExMS1hMjIwLTM2MmFmN2JlYjAxNCIsInVzZXJJZCI6bnVsbCwiZXZlbnRJZCI6MSwibGFzdEV2ZW50VGltZSI6MTc4NzU1MzI2NzE2NiwiY2hlY2tvdXQiOnsiYnJhbmQiOiJjYXNoYXBwYWZ0ZXJwYXkifX0=; amp_f24a38=ri2oB8iO8amBlQ7eCIL9Fj...1k0p7kffb.1k0p7kffb.0.0.0; ttcsid=1787553257602::eROFhqRB3q3baWWnnJKn.1.1787553273000.0::1.5900.0::15394.3.1402.23::6042.3.0; ttcsid_CF8PCRRC77U2ISB9LENG=1787553257602::5j78U5yhoIWJOpnGi8qn.1.1787553273000.1; rl_session=RS_ENC_v3_eyJpZCI6MTc4NzU1MzI1MjkwMSwiZXhwaXJlc0F0IjoxNzg3NTU1MDczMDAzLCJ0aW1lb3V0IjoxODAwMDAwLCJhdXRvVHJhY2siOnRydWUsInNlc3Npb25TdGFydCI6ZmFsc2V9; _ga_KDVZE23CS0=GS2.1.s1787553255$o1$g1$t1787553273$j42$l0$h939216548',
}



from _ljp.mb.zj import GetDetail
from _ljp.mb.model import Base, PageModel


def w():
    from playwright.sync_api import sync_playwright
    from fingerprint_toolkit import FingerprintKit
    from itertools import cycle

    edge = sync_playwright().start()
    browser = edge.chromium.launch(headless=False)

    # 创建4个上下文，保存对应的 fpk
    contexts = [browser.new_context() for _ in range(4)]
    context_fpk = {}
    for ctx in contexts:
        fpk = FingerprintKit()
        context_fpk[ctx] = fpk
        # 可选：创建一个初始页面，但不强制

    context_cycle = cycle(contexts)  # 循环迭代器

    def get():
        ctx = next(context_cycle)
        fpk = context_fpk[ctx]
        page = ctx.new_page()
        fpk.inject(page)
        return page

    return get


class Pc(GetDetail):


    def before_request(self, p: PageModel):
        url = p.url
        res= Tool.get(url,headers=headers,cookies=cookies)
        text = res.text
        match = re.search(r'"versionId"\s*:\s*"([^"]+?)"', text)
        if match:
            pro_id = match.group(1)  # 提取的值
            p.extra['p_id'] = pro_id
            print(pro_id)
        else:
            match = re.search(r'"version_id"\s*:\s*"([^"]+?)"', text)
            if match:
                pro_id = match.group(1)  # 提取的值
                p.extra['p_id'] = pro_id
                print(pro_id)
            else:
                print(url)
                print("未找到id")
                print(f'响应文本:{text}')


    def fetch_page(self, P:PageModel, params):


        """请求并解析单页。

        返回 (product_urls, next_url)：
            product_urls - 当前页商品链接列表
            next_url     - 下一页完整链接；为空或等于当前 url 表示停止翻页


        确认结束 p.status = 'end'
        确认失败 p.status = 'fail' 或者set_fail()
        """
        try:
            raw_url = 'https://huckberry.com/api/pages/tiles'
            if not params['version_id']:
                Tool.print(f'缺少id')
                P.set_fail()
                return [],None

            res = Tool.get(raw_url,headers=headers,cookies=cookies,params=params)

            if '<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...' in res.text:
                Tool.print(f'遇到反爬')
                exit()
            data = res.json()



            titles = data['tiles']
            ls = []
            for i in titles:
                ul = i['payload']['url']
                ul = Tool.URL.add_site(ul)
                ls.append(ul)

            print(f'长度: {len(ls)},：{ls}')

            if len(ls) < 48 :
                P.set_end()
                P.status = 'end'
                return ls,None

            return ls,raw_url

        except Exception as e:
            P.set_fail()
            return None,None

    def build_params(self, page:PageModel):
        """构造参与缓存哈希的请求参数；默认仅包含页码"""

        params = {
            'version_id': page.extra.get('p_id',None),
            'page': page.page,
            'in_stock': 'false',
            'should_fallback': 'false',
        }
        return params




if __name__ == '__main__':
    pc = Pc(
       tool=Tool,
       input_path=file_path,
       output_path=save_path,
       catch_path=catch_path,
       index_path=index_path,
       ts_num=ts_num,
       flush=flush,
       skip_input_url_ls=skip_input_url_ls,
       skip_output_url_ls=skip_output_url_ls,
       catch_save_num=catch_save_num
       )
    pc.run()

    if ts_num:
        Tool.print(f'当前执行测试调速{ts_num}')