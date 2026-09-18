import time

from lxml import etree

from config import Tool

input_file = Tool.File.path_add_site('data/detail_url.json')
output_file = Tool.File.path_add_site('res/result.csv')
output_ts_file = Tool.File.path_add_site('res/ts_res.csv')

fail_file = Tool.File.path_add_site('fail/4.json')
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
    '__apex_test__': '',
    'localization': 'US',
    'cart_currency': 'USD',
    'ede-s': '7b3ee075-e83e-43b0-9681-3dc79681ddc7',
    'ede-i': 'b464d9e9-0c26-4727-837d-0f76f308f9a8',
    'ede-expid': 'a1add734-06d4-4d89-be8f-1d84d23b70db',
    'ede-expvar': 'Edge Delivery Enabled',
    'ig-location': '{"country":"US","city":"Los Angeles","continent":"NA","latitude":"34.05","longitude":"-118.24","region":"California","regionCode":"CA"}',
    'ig-id': 'ig_0d99afc97551011ac28658338d7f27ab81a4',
    'ig-fv': '1789558493844',
    'cart': 'hWNGtdby1yUaR98U8OsVgCWu%3Fkey%3Dc86af9f26bdb472e2f8a58c4f9a4ac84',
    'cf_clearance': '_dlf9SDpGdT3qbgJ6RkzIt7nCOFVD4dRpcOFmlrNwzE-1789558495-1.2.1.1-iyGlczsZb6pr5tKLikSFyUQvlpM05IsSHkL5pPjHGYgyL5YTE586cv4RUWCC8HN7N5OOF88d5y6Ofif6IuDTFjazxEGrU5zFI5cwrYwLjfYnmF8XY.QBh_qkLMNdLAJ6iYULPz3TFvSp75a.RAKN9q257eS2Vl628vqIAwPspA3P0IveZos1N6vtBuQ1G2sF8c_eauWQj9WjQjLkdcvX6U7rJpWkHcR0Q_.r0xH4Q8n.pBHh0DLcleLMxxR7zzt6BsB2.wL62plZy_tqiK6R_W.eY5t2A7QPrGywVvFOC4levkfTm11Uw_FhdUKBAXQfRkz_3bGz2soi6co7y8d7oQMAAIAlE0u5QjO_drHs7Zc',
    'gb_anonymous_id': 'user_816c8ce3-f329-44a6-bdc7-76a38aaff777',
    'gb_session_id': 'cae30d09-2af6-4590-8b43-2a92f6a15f8c',
    'variant_cart': 'hWNGtdby1yUaR98U8OsVgCWu%3Fkey%3Dc86af9f26bdb472e2f8a58c4f9a4ac84',
    'styliticsWidgetSession': 'bd3c9909-2d2f-4f6f-90eb-80a85f0e16d5',
    '_bcai_i': 'DuNWk5yFFix56o2FtqGT3',
    '_bcai_v': 'DuNWk5yFFix56o2FtqGT3',
    '_bcai_vs': 'BLACKCROW',
    '_bcai_vn': '_bcai_v',
    'storefront_url': 'https://www.carvedesigns.com',
    'smartDash': '41368510-5d53-4f02-8add-8e26b55e9e8c',
    '__apex_test__': '',
    'cookieconsent_status': 'page_scroll',
    'cookieconsent_preferences_disabled': '',
    '_ga': 'GA1.1.36010658.1789558509',
    '_shopify_y': '6bf2efc5-dd05-42e2-a660-3b048b24f632',
    '_shopify_s': 'bf028db1-3a18-41a3-b346-7d88e7f1acf0',
    '_rsession': '1312f22093368ea2',
    '_ruid': 'eyJ1dWlkIjoiMWJkYzM2ODQtZjNmOS00NTQwLTk4OGMtY2YwMDlmNmZkNDc1In0%3D',
    '__kla_id': 'eyJjaWQiOiJZV0prTVdaalpUTXRNR00zT1MwMFlUUTFMVGc0T1dRdFl6bGhNR013TkdNMlpUVTIifQ==',
    '_shopify_s': 'bf028db1-3a18-41a3-b346-7d88e7f1acf0',
    '_shopify_y': '6bf2efc5-dd05-42e2-a660-3b048b24f632',
    'shopify_client_id': '6bf2efc5-dd05-42e2-a660-3b048b24f632',
    'shd_s': 'bf028db1-3a18-41a3-b346-7d88e7f1acf0',
    '_shd_y': '6bf2efc5-dd05-42e2-a660-3b048b24f632',
    'ssCartProducts': '',
    '__cf_bm': 'XuOSEvZ3LsoiMNsti3O1QmNXh5cXBjyBx7wgvzQ8Vhw-1789558524.6774065-1.0.1.1-na9alaqvz30KNgU87AlQbiXLaMyWXb_z3hMnaPc9tssb0yazSF0y0p3M8TnILNf0R5DZ1Xxc_hKFN22Lj9CrPv9FYtKiPL7S06r5C66SGq92y0H8KqPxJ.caHtvzGmYI',
    'first_pla_call': 'none',
    '_vid_t': 'Ij4A4XXbck7ZL/q2Du/VKc8MiQ3N8RnmgZPEkHu1G6w2VOttN5wNnRI8s0RdKfHE9MLQcGIxR+olug==',
    '_gegeo': 'JTdCJTIyc3RhdHVzJTIyJTNBJTIyc3VjY2VzcyUyMiUyQyUyMmNvdW50cnklMjIlM0ElMjJVbml0ZWQlMjBTdGF0ZXMlMjIlMkMlMjJjb3VudHJ5Q29kZSUyMiUzQSUyMlVTJTIyJTJDJTIybW9iaWxlJTIyJTNBZmFsc2UlMkMlMjJwcm94eSUyMiUzQXRydWUlMkMlMjJob3N0aW5nJTIyJTNBZmFsc2UlN0Q=',
    '_geref': 'https://www.carvedesigns.com/collections/new',
    '_geuid': '65808615-2bb2-4554-a3de-f37f04e0de94-1789558542849',
    '_heatVid_3228': '6916193542947008002',
    'hm_source': 'unknown',
    'vUUID_3228': '37246131-4e43-4e81-9317-07ef14eaeb2a',
    '_pk_id.3228.d3d3LmNh': 'ymaymaymayia2m6y.1789558550.',
    '_reidsn': 'i_1.12',
    '_geran': '3',
    '_getdran': '1',
    '_heatIdvUpdated_3228': '1789558602269',
    '_gecntaos': '2',
    '_geppv': '2',
    'ede-c': 'stash-hit',
    'ede-r': '',
    'ig-vars': '{%2207cc004e8882%22:%2230f31f1d4112%22%2C%22redirectedFrom%22:%22%22}',
    '_gcl_au': '1.1.1649800034.1789558522.-.-.1789558522.1990666521.1789558523.1789558716',
    '_shdfp': 'eyJub25jZSI6MTc4OTU1ODcxOTk0MSwic2hkSWQiOiJvQjkwdHlZQnZUeDI3VUpqdExueCIsImNyZWF0ZWRBdCI6MTc4OTU1ODUzODUzNywiaXNQcml2YXRlIjpmYWxzZSwiaXNCb3QiOmZhbHNlLCJ1cGRhdGVkQXQiOjE3ODk1NTg1Mzg1MzcsImZpbmdlcnByaW50UHJvRXZlbnRJZCI6IjE3ODk1NTg1Mzg0NDAueWFWR3FzIn0%3D',
    '_ga_PHZ6RS2JQX': 'GS2.1.s1789558522$o1$g1$t1789558722$j42$l0$h0',
    'ede-p': '/products/marais-reversible-jacket-orion-fleur-tweed',
    'ig-pv': '8',
    '_bcai_lpv': '8',
    '_bcai_spv': '8',
    '_shopify_analytics': ':AaCp_-aIAAEA3VYXJr7Yu8_JhyfKqo9ZTFPzhXJtMZpgnnc5HzkfchfM4McTB385F-y4YBKhkCveHqNHdodyXsFl8TbAemswXqBp3iXfWyfjZJcBiLd9MsbGLwSkfN8xiApmpCJKJV8-rIWAcaeRY_YwoE8:',
    '_shopify_marketing': ':AaCp_-aPAAEAMb9pRFGK7706BX70Ze2t59boM75Ogw0L3Od_7dTX0G_5PdcuDF7IoCCCt5WG2me7_8oun7b1zuSia_veXgic0dFCj2NHeErywttgSiB8WuUKfh0aCCI80IEKVwUADA2Jga9-Im852omNVeg:',
    '_bcai_h': '840f9515-6c13-4489-a510-ae15f29348bc_4e93981f-5aa9-42cb-a49b-1db142d36b8d_1789558817799',
    'ssViewedProducts': 'JCLD30-439-XXS%2CJCLD30-439-XXS%2CTWWB90-401-XXS%2CTWFF50-445-XXS',
    'ssUserId': '596d2397-a6bc-4ba1-a5ed-8649a4f2c3df',
    'ssSessionId': '057cab85-3cb5-4bd4-ad58-2d5f01d99d45',
    '_pin_unauth': 'dWlkPVlqY3dZVFZrWlRNdE1ESTFaQzAwWmprNUxUZ3dPRGN0WVRJMllXVmxOV0l6TlRSaw',
    '_ga_H1BMMD40CZ': 'GS2.1.s1789558507$o1$g1$t1789558825$j60$l0$h271562822',
    '_shopify_essential': ':AaCp_5DdAAEALyeuu0RUtunUbcx908zfQpE0lM1K9URp5nzPBBB4shb1HPOgU5GX7Upd33FEwUEWm-l973gbJFMpswmlwmUHrhuIBsCLh6HmuY11m1Q2sy1PcxYYLqT_4UgWEZpc-F1h_Mi_vmn7s9cAWEd_7HDLfWTPnoFHA8IFyARCLF33NWdDqzYb-w8gM9qyyMvHLqaKYltAeZ7INVUpuRV31zxRO8tWOSPUNC-BRe0UPxWWkawVSE5a_4Jr8GhVkHiqCFofBkz5U8SMdE3E640mOPSs_DA3TS8v8cv_uPSwpZFGl_6kko6HApi6nQBLLIGz5y4I-YUBYY56hHwGRuPmfVeXbpuJISyiZZ_dTGL0x_Vk5lT9eH_Kz5oKpzRLPD7zy-6xnn3ZYZQkI1mUX_m-Z-VKrWwp_I8Ms4MbhHlpP4DEzSh0fByB_ojPlh8EAbVttUo__jaJcIvc68wy9AZKeF4z0htf-YW86P44CMUyeAHlabvIhH4-iMZgN8gMSX0nl_6ELD5wSHcNwa1vpEszPvzchV7c31WUMDgEpTbcsFlC92dyZk9fBUFTc_YmZbtpg9vSaU7gIOFcgoSgtRdK1WpoyQBHU5V5ZRbLgeHQJ1l1zlS-Nf3lfMQpbNDyQitDJK0uSiZB-WLWVM_8CnV0XCpdcjkAGeZYjzIV0bluK6Mhnz1VA6oSn05s7A7uaqR1MPws4k14Dz0oV4uoqc-4rtGMz3599fUmkjkO0EdqSB-zcJmm4nLSXHBoew:',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-viewport-width': '1912',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
    # 'cookie': '__apex_test__=; localization=US; cart_currency=USD; ede-s=7b3ee075-e83e-43b0-9681-3dc79681ddc7; ede-i=b464d9e9-0c26-4727-837d-0f76f308f9a8; ede-expid=a1add734-06d4-4d89-be8f-1d84d23b70db; ede-expvar=Edge Delivery Enabled; ig-location={"country":"US","city":"Los Angeles","continent":"NA","latitude":"34.05","longitude":"-118.24","region":"California","regionCode":"CA"}; ig-id=ig_0d99afc97551011ac28658338d7f27ab81a4; ig-fv=1789558493844; cart=hWNGtdby1yUaR98U8OsVgCWu%3Fkey%3Dc86af9f26bdb472e2f8a58c4f9a4ac84; cf_clearance=_dlf9SDpGdT3qbgJ6RkzIt7nCOFVD4dRpcOFmlrNwzE-1789558495-1.2.1.1-iyGlczsZb6pr5tKLikSFyUQvlpM05IsSHkL5pPjHGYgyL5YTE586cv4RUWCC8HN7N5OOF88d5y6Ofif6IuDTFjazxEGrU5zFI5cwrYwLjfYnmF8XY.QBh_qkLMNdLAJ6iYULPz3TFvSp75a.RAKN9q257eS2Vl628vqIAwPspA3P0IveZos1N6vtBuQ1G2sF8c_eauWQj9WjQjLkdcvX6U7rJpWkHcR0Q_.r0xH4Q8n.pBHh0DLcleLMxxR7zzt6BsB2.wL62plZy_tqiK6R_W.eY5t2A7QPrGywVvFOC4levkfTm11Uw_FhdUKBAXQfRkz_3bGz2soi6co7y8d7oQMAAIAlE0u5QjO_drHs7Zc; gb_anonymous_id=user_816c8ce3-f329-44a6-bdc7-76a38aaff777; gb_session_id=cae30d09-2af6-4590-8b43-2a92f6a15f8c; variant_cart=hWNGtdby1yUaR98U8OsVgCWu%3Fkey%3Dc86af9f26bdb472e2f8a58c4f9a4ac84; styliticsWidgetSession=bd3c9909-2d2f-4f6f-90eb-80a85f0e16d5; _bcai_i=DuNWk5yFFix56o2FtqGT3; _bcai_v=DuNWk5yFFix56o2FtqGT3; _bcai_vs=BLACKCROW; _bcai_vn=_bcai_v; storefront_url=https://www.carvedesigns.com; smartDash=41368510-5d53-4f02-8add-8e26b55e9e8c; __apex_test__=; cookieconsent_status=page_scroll; cookieconsent_preferences_disabled=; _ga=GA1.1.36010658.1789558509; _shopify_y=6bf2efc5-dd05-42e2-a660-3b048b24f632; _shopify_s=bf028db1-3a18-41a3-b346-7d88e7f1acf0; _rsession=1312f22093368ea2; _ruid=eyJ1dWlkIjoiMWJkYzM2ODQtZjNmOS00NTQwLTk4OGMtY2YwMDlmNmZkNDc1In0%3D; __kla_id=eyJjaWQiOiJZV0prTVdaalpUTXRNR00zT1MwMFlUUTFMVGc0T1dRdFl6bGhNR013TkdNMlpUVTIifQ==; _shopify_s=bf028db1-3a18-41a3-b346-7d88e7f1acf0; _shopify_y=6bf2efc5-dd05-42e2-a660-3b048b24f632; shopify_client_id=6bf2efc5-dd05-42e2-a660-3b048b24f632; shd_s=bf028db1-3a18-41a3-b346-7d88e7f1acf0; _shd_y=6bf2efc5-dd05-42e2-a660-3b048b24f632; ssCartProducts=; __cf_bm=XuOSEvZ3LsoiMNsti3O1QmNXh5cXBjyBx7wgvzQ8Vhw-1789558524.6774065-1.0.1.1-na9alaqvz30KNgU87AlQbiXLaMyWXb_z3hMnaPc9tssb0yazSF0y0p3M8TnILNf0R5DZ1Xxc_hKFN22Lj9CrPv9FYtKiPL7S06r5C66SGq92y0H8KqPxJ.caHtvzGmYI; first_pla_call=none; _vid_t=Ij4A4XXbck7ZL/q2Du/VKc8MiQ3N8RnmgZPEkHu1G6w2VOttN5wNnRI8s0RdKfHE9MLQcGIxR+olug==; _gegeo=JTdCJTIyc3RhdHVzJTIyJTNBJTIyc3VjY2VzcyUyMiUyQyUyMmNvdW50cnklMjIlM0ElMjJVbml0ZWQlMjBTdGF0ZXMlMjIlMkMlMjJjb3VudHJ5Q29kZSUyMiUzQSUyMlVTJTIyJTJDJTIybW9iaWxlJTIyJTNBZmFsc2UlMkMlMjJwcm94eSUyMiUzQXRydWUlMkMlMjJob3N0aW5nJTIyJTNBZmFsc2UlN0Q=; _geref=https://www.carvedesigns.com/collections/new; _geuid=65808615-2bb2-4554-a3de-f37f04e0de94-1789558542849; _heatVid_3228=6916193542947008002; hm_source=unknown; vUUID_3228=37246131-4e43-4e81-9317-07ef14eaeb2a; _pk_id.3228.d3d3LmNh=ymaymaymayia2m6y.1789558550.; _reidsn=i_1.12; _geran=3; _getdran=1; _heatIdvUpdated_3228=1789558602269; _gecntaos=2; _geppv=2; ede-c=stash-hit; ede-r=; ig-vars={%2207cc004e8882%22:%2230f31f1d4112%22%2C%22redirectedFrom%22:%22%22}; _gcl_au=1.1.1649800034.1789558522.-.-.1789558522.1990666521.1789558523.1789558716; _shdfp=eyJub25jZSI6MTc4OTU1ODcxOTk0MSwic2hkSWQiOiJvQjkwdHlZQnZUeDI3VUpqdExueCIsImNyZWF0ZWRBdCI6MTc4OTU1ODUzODUzNywiaXNQcml2YXRlIjpmYWxzZSwiaXNCb3QiOmZhbHNlLCJ1cGRhdGVkQXQiOjE3ODk1NTg1Mzg1MzcsImZpbmdlcnByaW50UHJvRXZlbnRJZCI6IjE3ODk1NTg1Mzg0NDAueWFWR3FzIn0%3D; _ga_PHZ6RS2JQX=GS2.1.s1789558522$o1$g1$t1789558722$j42$l0$h0; ede-p=/products/marais-reversible-jacket-orion-fleur-tweed; ig-pv=8; _bcai_lpv=8; _bcai_spv=8; _shopify_analytics=:AaCp_-aIAAEA3VYXJr7Yu8_JhyfKqo9ZTFPzhXJtMZpgnnc5HzkfchfM4McTB385F-y4YBKhkCveHqNHdodyXsFl8TbAemswXqBp3iXfWyfjZJcBiLd9MsbGLwSkfN8xiApmpCJKJV8-rIWAcaeRY_YwoE8:; _shopify_marketing=:AaCp_-aPAAEAMb9pRFGK7706BX70Ze2t59boM75Ogw0L3Od_7dTX0G_5PdcuDF7IoCCCt5WG2me7_8oun7b1zuSia_veXgic0dFCj2NHeErywttgSiB8WuUKfh0aCCI80IEKVwUADA2Jga9-Im852omNVeg:; _bcai_h=840f9515-6c13-4489-a510-ae15f29348bc_4e93981f-5aa9-42cb-a49b-1db142d36b8d_1789558817799; ssViewedProducts=JCLD30-439-XXS%2CJCLD30-439-XXS%2CTWWB90-401-XXS%2CTWFF50-445-XXS; ssUserId=596d2397-a6bc-4ba1-a5ed-8649a4f2c3df; ssSessionId=057cab85-3cb5-4bd4-ad58-2d5f01d99d45; _pin_unauth=dWlkPVlqY3dZVFZrWlRNdE1ESTFaQzAwWmprNUxUZ3dPRGN0WVRJMllXVmxOV0l6TlRSaw; _ga_H1BMMD40CZ=GS2.1.s1789558507$o1$g1$t1789558825$j60$l0$h271562822; _shopify_essential=:AaCp_5DdAAEALyeuu0RUtunUbcx908zfQpE0lM1K9URp5nzPBBB4shb1HPOgU5GX7Upd33FEwUEWm-l973gbJFMpswmlwmUHrhuIBsCLh6HmuY11m1Q2sy1PcxYYLqT_4UgWEZpc-F1h_Mi_vmn7s9cAWEd_7HDLfWTPnoFHA8IFyARCLF33NWdDqzYb-w8gM9qyyMvHLqaKYltAeZ7INVUpuRV31zxRO8tWOSPUNC-BRe0UPxWWkawVSE5a_4Jr8GhVkHiqCFofBkz5U8SMdE3E640mOPSs_DA3TS8v8cv_uPSwpZFGl_6kko6HApi6nQBLLIGz5y4I-YUBYY56hHwGRuPmfVeXbpuJISyiZZ_dTGL0x_Vk5lT9eH_Kz5oKpzRLPD7zy-6xnn3ZYZQkI1mUX_m-Z-VKrWwp_I8Ms4MbhHlpP4DEzSh0fByB_ojPlh8EAbVttUo__jaJcIvc68wy9AZKeF4z0htf-YW86P44CMUyeAHlabvIhH4-iMZgN8gMSX0nl_6ELD5wSHcNwa1vpEszPvzchV7c31WUMDgEpTbcsFlC92dyZk9fBUFTc_YmZbtpg9vSaU7gIOFcgoSgtRdK1WpoyQBHU5V5ZRbLgeHQJ1l1zlS-Nf3lfMQpbNDyQitDJK0uSiZB-WLWVM_8CnV0XCpdcjkAGeZYjzIV0bluK6Mhnz1VA6oSn05s7A7uaqR1MPws4k14Dz0oV4uoqc-4rtGMz3599fUmkjkO0EdqSB-zcJmm4nLSXHBoew:',
}

if_wp = False
time_sleep = 2

from _ljp.mb.shopify import Get_Product


class Pc(Get_Product):

    def zdy_zd(self, url):
        '''返回字典格式'''
        res = Tool.get(url)
        html = etree.HTML(res.text)

        Tool.HTML.save(res.text)
        dic = {}
        for node in html.xpath('//div[@class="product-accordions"]/div'):
            name = node.xpath('./div/p/text()')[0]

            for i in ['Details', 'Fit','Materials & Care']:
                if i in name:
                    value = node.xpath('./div/ul')[0]
                    dic[i] = Tool.HTML.clean_product_desc(value)
                    break

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

            try:
                zdy_data = self.zdy_zd(url)
            except Exception as e:
                raise ValueError(f'自定义字段获取失败:{e}')

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