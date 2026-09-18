import time

from lxml import etree

from config import Tool

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')

fail_file = Tool.File.path_add_site('dail/4.json')
# NOTE 缓存策略
index_path = Tool.File.path_add_site('hc/4/index.json')
catch_path = Tool.File.path_add_site('hc/4/catch.json')
catch_save_num = None

skip_input_url_ls = []
skip_output_url_ls = []
# 默认使用fieldnames=None,自动写入自定义字段，需要控制字段写入由下游控制，这里保留所有字段
fieldnames = None

ts_num = None
cookies = {
    'localization': 'US',
    'cart_currency': 'USD',
    'em_cookie_ts': '2026-08-28T02%3A15%3A40.314Z',
    'em_device_id': '0x5d5c098203017ffe',
    'em_session_id': '0x38ac010fb6f6cb38',
    'em_migration': '4',
    'ig-id': 'ig_4fb250483fce90cb86b8d1c195f0efa9b5c9',
    'ig-location': '{"country":"US","city":"Los Angeles","continent":"NA","latitude":"34.05","longitude":"-118.24","region":"California","regionCode":"CA"}',
    'ig-fv': '1787883343577',
    '_hp5_event_props.3916164544': '%7B%7D',
    '_hp5_meta.3916164544': '%7B%22userId%22%3A%227014197707253435%22%2C%22sessionId%22%3A%227152597292524716%22%2C%22sessionProperties%22%3A%7B%22time%22%3A1787883343944%2C%22id%22%3A%227152597292524716%22%2C%22initial_pageview_info%22%3A%7B%22time%22%3A1787883343944%2C%22id%22%3A%221141590804527252%22%2C%22title%22%3A%22BRUNT%20Workwear%20%7C%20Quality%20Work%20Boots%20and%20Comfortable%20Apparel%20%7C%22%2C%22url%22%3A%7B%22domain%22%3A%22bruntworkwear.com%22%2C%22path%22%3A%22%2F%22%2C%22query%22%3A%22%22%2C%22hash%22%3A%22%22%7D%7D%2C%22search_keyword%22%3A%22%22%2C%22referrer%22%3A%22%22%2C%22utm%22%3A%7B%22source%22%3A%22%22%2C%22medium%22%3A%22%22%2C%22term%22%3A%22%22%2C%22content%22%3A%22%22%2C%22campaign%22%3A%22%22%7D%7D%7D',
    '_SIG2': 'ZWRnZQ%3D%3D',
    '_SIG3': 'ZWRnZQ%3D%3D',
    '_sp_puid': '87597a21-5a82-454e-aa19-13bd2def4c32',
    '_sp_puid': '87597a21-5a82-454e-aa19-13bd2def4c32',
    'cart': 'hWNGA0Y2HZCTjIL4YYQsFyC8%3Fkey%3Dd56e85ac3ab3fde0b2100858f5be8507',
    '_fbp': 'fb.1.1787883352871.6236753378',
    'cookieconsent_preferences_disabled': '',
    'FPC': 'cd2bbff4-748d-47db-a2d1-3a181c418e47',
    '_pvd_uid': '1.11-347au9qv-mtcbl905',
    '_sp_country_code': 'US',
    '_ga': 'GA1.1.1780766788.1787883360',
    '_shopify_y': '3d1e16e4-7e9f-48e7-9e53-0cb6d62de844',
    '_shopify_s': '15464ebc-28ef-4725-84af-17be6ab2e00c',
    '_shopify_analytics': ':AaBGJxLSAAEAXbfgBrDJTKC0A-8QpXRqEHhL78xnOeHh0VUXGIpVJ_iQ-0KGpYgHthH51NN2JrSDDrgv0Acdv7zfgLsxjCS8rkFgrLAiY7CammadG1W9prfnFnV0AYko6hX4aMyQlzjlWeM:',
    '_shopify_marketing': ':AaBGJxLZAAEAK0A1XNJJmDm-PjNAdwqfxWoLNXPN9k0Q9PJn1QlLPkpLI-fv4445JKx9Wi5qkGTZeGnpn-x3bqtoK6D4HHSkOSO3CiT1yCnGjS71gUTSHZhc06tshdLVdco:',
    'hm_source': 'unknown',
    '__kla_id': 'eyJjaWQiOiJNRGMzTkRrMk1qUXROMlV5TkMwME5UZ3dMV0UxTUdFdFlXRTBPRGRsWVRjMU5XWmsifQ==',
    '_twpid': 'tw.1787883362314.533966231531394080',
    'shopify_client_id': '3d1e16e4-7e9f-48e7-9e53-0cb6d62de844',
    '_pk_id.244.YnJ1bnR3': 'eimqayi6qaum6qa2.1787883364.',
    'vUUID_244': 'b512b39e-7fdd-4b17-95ad-158df511b0be',
    '_axwrt': '3d1e16e4-7e9f-48e7-9e53-0cb6d62de844',
    '_ps_session': '_lb7nUyx566X7rnrUq7n3',
    '_ps_site_visit': 'true',
    'cookieconsent_status2': 'page_refresh',
    'ig-vars': '{%22407c378e6f94%22:%22_UNASSIGNED%22%2C%2270f8f3288e65%22:%22_UNASSIGNED%22%2C%220ffb7b59b065%22:%22939e9396cf65%22%2C%22c635567a68a9%22:%22_UNASSIGNED%22%2C%22de8f10acfd1a%22:%22972e9a105bbf%22%2C%2299014707fb62%22:%22_UNASSIGNED%22%2C%2278da11bf5230%22:%2246915a1d8174%22%2C%225467410eab72%22:%22d85cbb515399%22%2C%22aedc8fe1d336%22:%22af5b69561145%22%2C%22c8b310efcfa6%22:%225f169caa2fff%22%2C%2272bda5c2cf5f%22:%22ff92cffe5d0b%22%2C%22redirectedFrom%22:%22%22}',
    '_ps_unique_impression_01d272cc-b171-4f1d-889a-0512f6c6f619': 'true',
    '_ps_pop_01d272cc-b171-4f1d-889a-0512f6c6f619': 'r',
    'baMet_visit': 'fad1814c222d42af84b2795a67051e951787885757329',
    '_ps_unique_impression_f541ff4b-c761-4959-b341-139147587180': 'true',
    '_gcl_au': '1.1.1240995819.1787883361.-.-.1787883439.1511827127.1787883440.1787885820',
    '_heatVid_244': '6828110806196006004',
    'cf_clearance': 'PW278yc4UyGh1k0WdbLGF24N28Z41W9fE2oFHzjBbkI-1787886506-1.2.1.1-4tkyMBN5EBgrsVuIfjUbV6x0XoikFhGQc66xx1hLzoN1kZxe0IIZd2hAtX4pW6gU3gRoZwKDHTwztpg.QbEaHQkAbW3m3jB1WEEczok0VvgynjwLpxbgu1mWcsoEB2TZdqE.Em7yD7GAzAP12qzYjcWZxSHaiUSP6iHA5Ct3hsUo8PFtjR55RQkjXAmXNYuP1Y5iFqMqyOmtO6eXPCgIGQ7lRw9ARINCuKsEI8mrNt2LZo8QEcIm8aee2OZ7nCZgSCckRjdpY4jJTqjGmNZsud1qh2ubhRZRcSf6PCoMq83GiwSm0cnI7DdPjhUYtAsR277zzJtM2STAkPOUIVKw35l0h3dG7ka6GUdVxovzz7SuuM5iUykPawg4vU7aLudgN7hij_AYPiPT.w5uCMyKM5txgqrZWAasGKlIGH3hWVbyZM20s0KqBD005IRrnbrIpdX8P_Pu2Sdxx1hBkaUBCcGWrjDwEk3Gw61cN.DQAnNzRuxXcgx7YQyAnkI3LVq2G.aIB3.OCFJFWRfrrYFfVQ',
    '__cf_bm': 'a6YIAEJlkLaq58BRmTxbteHrQqblj_0gjEuJiLv20j0-1787886506.5773637-1.0.1.1-ER09ETM296XIKk4knSrDG3OzV9ecfi6rshod2oaasXBTcIuu_8YlDMMHBzIF1EyGmB4sh3G3.us0ZuwZ_dfEt1mdOKE68SF5dFLwtwmrF1J9FPCv73GlJOSDJd7jS0s3',
    '_haus_session': 'f1199d05-a83d-4bc6-b9ac-ed964594810b|1787886519315',
    '_ga_289302657': 'GS2.1.s1787886522$o2$g0$t1787886522$j60$l0$h0',
    'em_nav_id': '0xc6b1ea3e47638bf4',
    'em_sec': 'cRjba19fOAg0ED9pelSm3WC%2BR1mMAiL16AaAjT3TM3ctAEa9vGxPQ0fufwKWj4il7993DKH0miJatBLTP8u0iDCtE2O3WYZf%2BniZHk987nTuBAz4NbOAmS1awQ%3D%3D',
    'ig-pv': '14',
    '_dd_s': 'aid=78e7a300-0826-4c14-b0bc-965a9ed700ef&logs=1&id=6091baf3-1ae5-4170-9134-89d44b0a4989&created=1787883359425&expire=1787887460054',
    '_heatIdvUpdated_244': '1787886561095',
    'ax_visitor': '%7B%22firstVisitTs%22%3A1787883364182%2C%22lastVisitTs%22%3Anull%2C%22currentVisitStartTs%22%3A1787883364182%2C%22ts%22%3A1787886561509%2C%22visitCount%22%3A1%7D',
    '_ax_last_event': '1787886561509',
    'g_state': '{"i_l":0,"i_ll":1787886562273,"i_b":"yiwS0fkt2P0zYOnH44nTEp6pBJ06zS9pwkke/oZaxjs","i_e":{"enable_itp_optimization":24},"i_et":1787886562273}',
    '_ga_3W6GXYKVJ6': 'GS2.1.s1787885756$o2$g1$t1787886562$j21$l0$h0',
    '_shopify_essential': ':AaBGJtiLAAEATtuSQY94OaIt4XAIcPtQ8jOZnc0mRBAl4xJERszKKTm4G8XYNbmsqkcw67-MuuCbMq49-f43JjNqJIkM1xKTnwUc2cQvXNEPJVkwPtQE5WY3PI0m6i22K1_5fPI7KV-GlZEbQeFybfPtPEaoEQPm5Jz7HGAwl6wv2MzUK8iQU63XFNZFGeosKRic-utWlTu1AIJgrh5kWWkIjPf7e8aGfjqq5vfyHUOTSgwx2_o98q_u9BbOrj3X2OYtPWiE_vjtBWQci3HPUMRbcPVHzCoaNE7BowqfCLjPiJJsh3uTsotN_1mPTSiA-hcPfCD3ln3nt0m6N-iBjdUvXrE5P9XRMzUCdKh0pdwo_apkdMaFWYlAhQkXBwoHFCM88V6fg_1vOkNN3kKRCRoRXwQzAdpIKSTRzEE8FQkXrSKZsm1gAl3AMT8EKBrLd2HlqRgBHTo6ui17gZbLwnFTACQGBTbZdvUOt4yK2pOGHBKnr3Vo35syeRDu55oZuvq_fBWGhl3TUf7i7XX35SVPcX4RYHm8pBOEBdKKcRMvgOM7Q4s8TMcuP0XeXJnntQVnxxqMVFleh0nLuzUJYaanx-z14xMKlvLFRXHBNss04eF_jQKRSuNwW0rW2dV9AS6BE-8PcTfp9CLSjobxjdHy99cXl2FD4Xm16EktW74vVcxPStmLNDdfpB4Vtef6_eRCVUEdmegNG327v_yh1dgqiSR1ygmZTecTW0tr3TrWdgVO_5ye8i21fASHxUtQPJMkPOLebRkWsHoc0k2bKBa1GVpb:',
    '_ga_L33416Z77F': 'GS2.1.s1787883358$o1$g1$t1787886569$j47$l0$h0',
    '_hp5_let.3916164544': '1787886568860',
    '_ps_session_site_visit': '%7B%22sessionId%22%3A%22ee33e790-80da-487c-ac68-7dc546ff3b80%22%2C%22startTime%22%3A1787886572882%7D',
    '_ax_session_data': 'eyJpbnZpc2libGVUaW1lIjowLCJ0b3RhbFRpbWUiOjExODk3LCJsYXN0VXBkYXRlIjoxNzg3ODg2NTczNTAwfQ==',
}

headers = {
    'accept': 'application/signed-exchange;v=b3;q=0.7,*/*;q=0.8',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'available-dictionary': ':GT9pt4eYvV3g8AjGRAA+st2X8510631KbMqQRjoswck=:',
    'cache-control': 'no-cache',
    'dictionary-id': '"BusbgTR8"',
    'origin': 'https://bruntworkwear.com',
    'pragma': 'no-cache',
    'priority': 'u=4, i',
    'referer': 'https://bruntworkwear.com/products/torra-hd-cargo-short?variant=45101432537246',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-viewport-width': '1912',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-purpose': 'prefetch',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    # 'cookie': 'localization=US; cart_currency=USD; em_cookie_ts=2026-08-28T02%3A15%3A40.314Z; em_device_id=0x5d5c098203017ffe; em_session_id=0x38ac010fb6f6cb38; em_migration=4; ig-id=ig_4fb250483fce90cb86b8d1c195f0efa9b5c9; ig-location={"country":"US","city":"Los Angeles","continent":"NA","latitude":"34.05","longitude":"-118.24","region":"California","regionCode":"CA"}; ig-fv=1787883343577; _hp5_event_props.3916164544=%7B%7D; _hp5_meta.3916164544=%7B%22userId%22%3A%227014197707253435%22%2C%22sessionId%22%3A%227152597292524716%22%2C%22sessionProperties%22%3A%7B%22time%22%3A1787883343944%2C%22id%22%3A%227152597292524716%22%2C%22initial_pageview_info%22%3A%7B%22time%22%3A1787883343944%2C%22id%22%3A%221141590804527252%22%2C%22title%22%3A%22BRUNT%20Workwear%20%7C%20Quality%20Work%20Boots%20and%20Comfortable%20Apparel%20%7C%22%2C%22url%22%3A%7B%22domain%22%3A%22bruntworkwear.com%22%2C%22path%22%3A%22%2F%22%2C%22query%22%3A%22%22%2C%22hash%22%3A%22%22%7D%7D%2C%22search_keyword%22%3A%22%22%2C%22referrer%22%3A%22%22%2C%22utm%22%3A%7B%22source%22%3A%22%22%2C%22medium%22%3A%22%22%2C%22term%22%3A%22%22%2C%22content%22%3A%22%22%2C%22campaign%22%3A%22%22%7D%7D%7D; _SIG2=ZWRnZQ%3D%3D; _SIG3=ZWRnZQ%3D%3D; _sp_puid=87597a21-5a82-454e-aa19-13bd2def4c32; _sp_puid=87597a21-5a82-454e-aa19-13bd2def4c32; cart=hWNGA0Y2HZCTjIL4YYQsFyC8%3Fkey%3Dd56e85ac3ab3fde0b2100858f5be8507; _fbp=fb.1.1787883352871.6236753378; cookieconsent_preferences_disabled=; FPC=cd2bbff4-748d-47db-a2d1-3a181c418e47; _pvd_uid=1.11-347au9qv-mtcbl905; _sp_country_code=US; _ga=GA1.1.1780766788.1787883360; _shopify_y=3d1e16e4-7e9f-48e7-9e53-0cb6d62de844; _shopify_s=15464ebc-28ef-4725-84af-17be6ab2e00c; _shopify_analytics=:AaBGJxLSAAEAXbfgBrDJTKC0A-8QpXRqEHhL78xnOeHh0VUXGIpVJ_iQ-0KGpYgHthH51NN2JrSDDrgv0Acdv7zfgLsxjCS8rkFgrLAiY7CammadG1W9prfnFnV0AYko6hX4aMyQlzjlWeM:; _shopify_marketing=:AaBGJxLZAAEAK0A1XNJJmDm-PjNAdwqfxWoLNXPN9k0Q9PJn1QlLPkpLI-fv4445JKx9Wi5qkGTZeGnpn-x3bqtoK6D4HHSkOSO3CiT1yCnGjS71gUTSHZhc06tshdLVdco:; hm_source=unknown; __kla_id=eyJjaWQiOiJNRGMzTkRrMk1qUXROMlV5TkMwME5UZ3dMV0UxTUdFdFlXRTBPRGRsWVRjMU5XWmsifQ==; _twpid=tw.1787883362314.533966231531394080; shopify_client_id=3d1e16e4-7e9f-48e7-9e53-0cb6d62de844; _pk_id.244.YnJ1bnR3=eimqayi6qaum6qa2.1787883364.; vUUID_244=b512b39e-7fdd-4b17-95ad-158df511b0be; _axwrt=3d1e16e4-7e9f-48e7-9e53-0cb6d62de844; _ps_session=_lb7nUyx566X7rnrUq7n3; _ps_site_visit=true; cookieconsent_status2=page_refresh; ig-vars={%22407c378e6f94%22:%22_UNASSIGNED%22%2C%2270f8f3288e65%22:%22_UNASSIGNED%22%2C%220ffb7b59b065%22:%22939e9396cf65%22%2C%22c635567a68a9%22:%22_UNASSIGNED%22%2C%22de8f10acfd1a%22:%22972e9a105bbf%22%2C%2299014707fb62%22:%22_UNASSIGNED%22%2C%2278da11bf5230%22:%2246915a1d8174%22%2C%225467410eab72%22:%22d85cbb515399%22%2C%22aedc8fe1d336%22:%22af5b69561145%22%2C%22c8b310efcfa6%22:%225f169caa2fff%22%2C%2272bda5c2cf5f%22:%22ff92cffe5d0b%22%2C%22redirectedFrom%22:%22%22}; _ps_unique_impression_01d272cc-b171-4f1d-889a-0512f6c6f619=true; _ps_pop_01d272cc-b171-4f1d-889a-0512f6c6f619=r; baMet_visit=fad1814c222d42af84b2795a67051e951787885757329; _ps_unique_impression_f541ff4b-c761-4959-b341-139147587180=true; _gcl_au=1.1.1240995819.1787883361.-.-.1787883439.1511827127.1787883440.1787885820; _heatVid_244=6828110806196006004; cf_clearance=PW278yc4UyGh1k0WdbLGF24N28Z41W9fE2oFHzjBbkI-1787886506-1.2.1.1-4tkyMBN5EBgrsVuIfjUbV6x0XoikFhGQc66xx1hLzoN1kZxe0IIZd2hAtX4pW6gU3gRoZwKDHTwztpg.QbEaHQkAbW3m3jB1WEEczok0VvgynjwLpxbgu1mWcsoEB2TZdqE.Em7yD7GAzAP12qzYjcWZxSHaiUSP6iHA5Ct3hsUo8PFtjR55RQkjXAmXNYuP1Y5iFqMqyOmtO6eXPCgIGQ7lRw9ARINCuKsEI8mrNt2LZo8QEcIm8aee2OZ7nCZgSCckRjdpY4jJTqjGmNZsud1qh2ubhRZRcSf6PCoMq83GiwSm0cnI7DdPjhUYtAsR277zzJtM2STAkPOUIVKw35l0h3dG7ka6GUdVxovzz7SuuM5iUykPawg4vU7aLudgN7hij_AYPiPT.w5uCMyKM5txgqrZWAasGKlIGH3hWVbyZM20s0KqBD005IRrnbrIpdX8P_Pu2Sdxx1hBkaUBCcGWrjDwEk3Gw61cN.DQAnNzRuxXcgx7YQyAnkI3LVq2G.aIB3.OCFJFWRfrrYFfVQ; __cf_bm=a6YIAEJlkLaq58BRmTxbteHrQqblj_0gjEuJiLv20j0-1787886506.5773637-1.0.1.1-ER09ETM296XIKk4knSrDG3OzV9ecfi6rshod2oaasXBTcIuu_8YlDMMHBzIF1EyGmB4sh3G3.us0ZuwZ_dfEt1mdOKE68SF5dFLwtwmrF1J9FPCv73GlJOSDJd7jS0s3; _haus_session=f1199d05-a83d-4bc6-b9ac-ed964594810b|1787886519315; _ga_289302657=GS2.1.s1787886522$o2$g0$t1787886522$j60$l0$h0; em_nav_id=0xc6b1ea3e47638bf4; em_sec=cRjba19fOAg0ED9pelSm3WC%2BR1mMAiL16AaAjT3TM3ctAEa9vGxPQ0fufwKWj4il7993DKH0miJatBLTP8u0iDCtE2O3WYZf%2BniZHk987nTuBAz4NbOAmS1awQ%3D%3D; ig-pv=14; _dd_s=aid=78e7a300-0826-4c14-b0bc-965a9ed700ef&logs=1&id=6091baf3-1ae5-4170-9134-89d44b0a4989&created=1787883359425&expire=1787887460054; _heatIdvUpdated_244=1787886561095; ax_visitor=%7B%22firstVisitTs%22%3A1787883364182%2C%22lastVisitTs%22%3Anull%2C%22currentVisitStartTs%22%3A1787883364182%2C%22ts%22%3A1787886561509%2C%22visitCount%22%3A1%7D; _ax_last_event=1787886561509; g_state={"i_l":0,"i_ll":1787886562273,"i_b":"yiwS0fkt2P0zYOnH44nTEp6pBJ06zS9pwkke/oZaxjs","i_e":{"enable_itp_optimization":24},"i_et":1787886562273}; _ga_3W6GXYKVJ6=GS2.1.s1787885756$o2$g1$t1787886562$j21$l0$h0; _shopify_essential=:AaBGJtiLAAEATtuSQY94OaIt4XAIcPtQ8jOZnc0mRBAl4xJERszKKTm4G8XYNbmsqkcw67-MuuCbMq49-f43JjNqJIkM1xKTnwUc2cQvXNEPJVkwPtQE5WY3PI0m6i22K1_5fPI7KV-GlZEbQeFybfPtPEaoEQPm5Jz7HGAwl6wv2MzUK8iQU63XFNZFGeosKRic-utWlTu1AIJgrh5kWWkIjPf7e8aGfjqq5vfyHUOTSgwx2_o98q_u9BbOrj3X2OYtPWiE_vjtBWQci3HPUMRbcPVHzCoaNE7BowqfCLjPiJJsh3uTsotN_1mPTSiA-hcPfCD3ln3nt0m6N-iBjdUvXrE5P9XRMzUCdKh0pdwo_apkdMaFWYlAhQkXBwoHFCM88V6fg_1vOkNN3kKRCRoRXwQzAdpIKSTRzEE8FQkXrSKZsm1gAl3AMT8EKBrLd2HlqRgBHTo6ui17gZbLwnFTACQGBTbZdvUOt4yK2pOGHBKnr3Vo35syeRDu55oZuvq_fBWGhl3TUf7i7XX35SVPcX4RYHm8pBOEBdKKcRMvgOM7Q4s8TMcuP0XeXJnntQVnxxqMVFleh0nLuzUJYaanx-z14xMKlvLFRXHBNss04eF_jQKRSuNwW0rW2dV9AS6BE-8PcTfp9CLSjobxjdHy99cXl2FD4Xm16EktW74vVcxPStmLNDdfpB4Vtef6_eRCVUEdmegNG327v_yh1dgqiSR1ygmZTecTW0tr3TrWdgVO_5ye8i21fASHxUtQPJMkPOLebRkWsHoc0k2bKBa1GVpb:; _ga_L33416Z77F=GS2.1.s1787883358$o1$g1$t1787886569$j47$l0$h0; _hp5_let.3916164544=1787886568860; _ps_session_site_visit=%7B%22sessionId%22%3A%22ee33e790-80da-487c-ac68-7dc546ff3b80%22%2C%22startTime%22%3A1787886572882%7D; _ax_session_data=eyJpbnZpc2libGVUaW1lIjowLCJ0b3RhbFRpbWUiOjExODk3LCJsYXN0VXBkYXRlIjoxNzg3ODg2NTczNTAwfQ==',
}

if_wp = False
time_sleep = 7

from _ljp.mb.shopify import Get_Product
class Pc(Get_Product):


    def zdy_zd(self,url):
        '''返回字典格式'''
        res = Tool.get(url,headers=headers,cookies=cookies,timeout=15)
        html = etree.HTML(res.text)
        Tool.HTML.save(res.text)

        ls = html.xpath('//div[@class="product__accordion"]/accordion-custom/details')
        dic = {}

        for i in ls:
            _name = i.xpath('./summary/h5/text()')[0]
            for name in ['PRODUCT DETAILS','MATERIAL & CARE']:
                if name in _name:
                    value = i.xpath('./div')[0]

                    dic[name] = Tool.HTML.clean_product_desc(value)

                    break

        print(dic)
        return dic



    def fetch_product(self, url, category) -> list:
        Tool = self.tool
        handle = Tool.URL.get_handle(url)

        p_url = f"https://www.{Tool.site}.com/products/{handle}.json"

        try:
            r = Tool.get(p_url, headers=headers,cookies=cookies,timeout=15)

            if r.status_code == 404:
                return []
            data = r.json()

            #TODO 使用原url还是   p_url.replace('.json', '')

            zdy_data = self.zdy_zd(url)

            time.sleep(time_sleep)

            shopify_product = data.get("product")

            shopify_product[Tool.custom_key] = zdy_data
            shopify_product['__url'] = url

        except Exception as e:
            Tool.print(f'[ERROR] 接口请求失败:{url} 未知异常: {e}')
            return []

        woo_product = self.shopify_to_woocommerce(
            shopify_product,
            brand=Tool.site,
            custom_categories=category
        )
        _products = [woo_product]
        variations = self.create_variation_products(shopify_product, woo_product)

        if variations:
            _products.extend(variations)


        return _products



if __name__ == '__main__':
    pc = Pc(
        tool=Tool,
        input_path=input_file,
        output_path=output_file,
        fail_file=fail_file,
        catch_path=catch_path,
        index_path=index_path,
        output_ts_file=output_ts_file,
        ts_num=ts_num,
        catch_save_num = catch_save_num,
        skip_input_url_ls=skip_input_url_ls,
        skip_output_url_ls=skip_output_url_ls,
        fieldnames=fieldnames,
        max_threads=10,
        if_wp=if_wp
    )

    pc.run()