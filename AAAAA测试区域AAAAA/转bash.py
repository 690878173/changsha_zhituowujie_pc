from curl_cffi import requests
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'referer': 'https://balticborn.com/collections/best-sellers',
    'sec-ch-ua': '"Chromium";v="154", "Microsoft Edge";v="154", "Not A(Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-viewport-width': '1912',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36 Edg/154.0.0.0',
    'cookie': 'test=test; test; localization=US; cart_currency=USD; _shopify_analytics=:AaDmvz7SAAEAtTfLAFuAG_3HUySm5kSX_K4mGn2sf0Jjk5MYdYB5Zgf8C3xBRedGR4JZy72IM7HnfKOg1e-D_ZhCYHT204Xjaj1Pe36MKw-xydiSr2h-c78alBRH7DDRidYC2FBnQQBSwxoTN0khK4mm_y8:; _shopify_marketing=:AaDmvz7TAAEA-KWN9-MmHiCWA-NXvu8JJaexYm3MaTwdyrjDKQe8dHO5VWCRxAZ8ePkVQSxsO400tBN3qZUiunz4RfXXY5N0zEPoAPJiLOLN7jS3zJTTgr8HiQtrqHf5SQhh0PChkiPlG4i8mI77lDcZqzs:; __cf_bm=8EnHq2Mwg5XsiMlVNlgzOyfmN2IUyQf9k93fUd7xdE4-1790577687.9734921-1.0.1.1-.sfyo.wEGjP8XdgjLftgayzk52si.fUFf83O5mYpqML.hc.EUi9b5.f.r5.fqm7GWm6XH8RTW0rqMWCk0Wd55aJy_xJUE.QtREmXA2cRyJd.HnO0TgVcg3B_9VY8p82M; shopify_client_id=4dfe3421-7edb-48c7-b177-fa070475618b; _axwrt=4dfe3421-7edb-48c7-b177-fa070475618b; _picky.widget.discounts.sessionId%3Abaltic-born.myshopify.com=b9d3b1e8-9a55-466f-bf40-5c83930ddfc7; _heatVid_5237=6928144129303007006; hm_source=unknown; _pk_id.5237.YmFsdGlj=ymeyyi2m6maq6uay.1790577689.; __kla_id=eyJjaWQiOiJNamczT1dRNU5qVXRNV0V4T1MwME9URXlMVGs0WmpVdE1EUXlNamN4WVdFMVpERTUifQ==; swym-session-id="5jufdzavbjw2rsrhi8q5u4rmnsm3bl66lpm03vb4agld9ls91e2ypvxfe8qba8ql"; swym-pid="SHLkNYdeeKObytM0AqGOWxCip/YXAqMS+F0e1Nq9QV0="; _picky.widget.discounts.isDiscountActive=false; cookieyes-consent=consentid:ZXlrMUZhYmtyNjV0STRuRXZoeEc0UTZOY1VKZGhGdEY,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes; cart=hWNHLOsE0Hw3r9uFq0E43k7s%3Fkey%3D81aeb303b5ff6838dcff703cecc02219; _ga=GA1.1.1921688195.1790577690; vUUID_5237=93e0f342-8fd7-4fdb-b699-b040b89c3f18; _ks_scriptVersionChecked=true; test=test; test; 2c.cId=6aba0c1f14de2275f6f5cd03; _ks_userCountryUnit=0; _ks_countryCodeFromIP=US; bm=8277d5a4-655e-4765-9ed6-a9f33a9a9f32; __blka_ts=1790579533955; _gcl_au=1.1.560697135.1790577690.-.-.1790577690.99859980.1790577690.1790577735; _heatIdvUpdated_5237=1790577735813; _ga_9Y865RBMCQ=GS2.1.s1790577690$o1$g1$t1790577735$j15$l0$h0; _ga_31GDGB6LCJ=GS2.1.s1790577689$o1$g1$t1790577735$j14$l0$h355798658; _ga_D3TFYDD195=GS2.1.s1790577690$o1$g1$t1790577735$j15$l0$h0; _pin_unauth=dWlkPU5EYzBZek14WkdJdE1USXhZeTAwTVRZMExXSXhOREl0T0Rnd00yUXhNV0ZrTkdVMA; ax_visitor=%7B%22firstVisitTs%22%3A1790577688429%2C%22lastVisitTs%22%3Anull%2C%22currentVisitStartTs%22%3A1790577688429%2C%22ts%22%3A1790577738795%2C%22visitCount%22%3A1%7D; _ax_last_event=1790577738701; kiwi-sizing-token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJiZjg4OTNiNC0xNmNjLTQ3NTQtYTI0Ni0yYjUzZmQ4NWY1N2QiLCJpYXQiOjE3OTA1Nzc3NDEsImV4cCI6MTc5MDU4MTM0MX0.MvmjOljHT_JQXDjGkd1BtliVTz9vQn2awCrgKecDFNA; _shopify_essential=:AaDmvz3eAAEAslAJ9azCQuRGjL3528OdG9hIkjHonCUBkzX-0jH4r4AfeZTNGUwyeSx5b6XCb9E9gMQtVnm3rxFBqEYQdZvO-NzK2u7KrunD3pZuUWGRGLVeZyZquktqmicijtuLOZ51YHoZBaOtxwBVP75Qb7ovBJUwbXPhTdhYNkd_Y8KLy4IPRWFfwik4BEc6Wz-nulHcgLNQ4SDKJFy3Qpth7UzGixvf8uri6rnJC-8ccG4p4kPv83eGIp6wtZr8i6P-YhzL4EyfLZ9uOl-TxQSsdzK1WX4f_OtjXiv24IFB91lhMZt5X7NmVFlfmpsg5UEdiDaTkpNJ2EzZkzxb_r8ZjzCSGiF1CJ-TWyYJick-yvGVnRJviawA:; _ax_session_data=eyJpbnZpc2libGVUaW1lIjoyNDUwMDcsInRvdGFsVGltZSI6MjcxOTQzLCJsYXN0VXBkYXRlIjoxNzkwNTc4MDEwNzExfQ==; _dd_s=aid=32e11788-56e2-402f-80f0-169d451f67e1&logs=1&id=cefd9906-3c45-4c3e-ac25-a0ff7f82ebe6&created=1790577691660&expire=1790578911153',
}

params = {
    'variant': '41688508760229',
}

response = requests.get('https://balticborn.com/products/clarisa-lace-midi-dress-vinatge-cream', params=params, headers=headers)
print(response.status_code)

print(response.text)
