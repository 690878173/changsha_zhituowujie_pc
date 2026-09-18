from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')
js_path = Tool.File.path_add_site('hc/1/js_code.json')

cookies = {
    'OptanonAlertBoxClosed': '2026-08-17T07:32:09.354Z',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Mon+Aug+17+2026+15%3A32%3A11+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202504.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=dd41da20-804a-4aa2-8abc-469817bacc86&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0005%3A1%2CC0001%3A1%2CBG441%3A1%2CC0002%3A1%2CC0003%3A1%2CBG442%3A1&intType=1&geolocation=US%3BCA&AwaitingReconsent=false',
    'user_country': 'HK',
    'dwanonymous_a0bee6d5d02f73f6e619681126569802': 'abwHk0wKs1kXgRxbkYxaYYlrFF',
    '_ga': 'GA1.1.1765035832.1786938135',
    '_gcl_au': '1.1.1254396896.1786938135',
    'FPID': 'FPID2.2.2BBrQaheVcrZfLr61eRHKvbUdj7u0lE2qhkz9M%2FCImM%3D.1786938135',
    '_scid': '13df4536-ef75-48aa-e8ef-873da1911d06',
    '_gtmeec-tt': 'eyJjb3VudHJ5IjoidXMifQ%3D%3D',
    'FPLC': 'WkD9nONJyFDB5ybPTUyi3GS8umKpWClO2NHXT%2BmlbW7FlNiCkv1WUml37GrgwDF6r%2F3Eg7pBj4Yt%2FiIQV2ad2frsv6oPbyFd8gsKutWzhaP9%2FoI3XvHNzfvLUk3MHg%3D%3D',
    '_fbp': 'fb.1.1786938136765.654244661702356831.AQYCAQMB',
    'BVBRANDID': 'dd62c723-44b9-4724-97ae-5fbd6f3dbd36',
    'BCSessionID': 'ba9706fb-a13d-4cc5-ad56-a9759426f6cd',
    '__cq_dnt': '1',
    'dw_dnt': '1',
    'bv_metrics': 'true',
    'IM_surveyAction': 'open',
    'IM_shown_1643': 'true',
    'bm_mi': 'C9E9E1A177C35B7CF524148EC2D1E17F~YAAQRw7SFwJfLu+fAQAAWA0/DgBZw499AO94n9jeh1lpYPGhQQo0VJUKvjICzKKVVU9p+Vf3OdKP2sl7k3+8S/o+sLdNogJUEKGXDOOcAbPNYmJ0MXb9SE5imnnTffepOEEjNuZYHIy6Bo5jaUw6a97g9a7mt9CIPBVg6JGUH2zCk1fbGLpFvdpI7rSbxb2kJ4pXPOMGIv41ysGLMvEX2nuFmWfMlD5ZFgaF/+O6NL3zfxH7WYtu4trWfsDBeDVjjpAD371MEHivpm/D6GqZSRnrSygVFz/Cyw4tLAd4RwDTVRzwyH2PSIcF77IXe2N+7bKlPnKFFMSKDUYyTvF+/cPgbajt391BiwbBiwzdTGYgqYsAhBcr/nBm3knKR/0=~1',
    'ak_bmsc': '53288B62C63E9ABBA17115FA5BD85DB4~000000000000000000000000000000~YAAQRw7SF6NgLu+fAQAA9Rs/DgAmOeUNFhDquXmWmt9Q3otsVf1jKe2b4AiABqUBSdISz49vkf6KB1ulnUOmmz9olfYCe9eR0qk/5S4TfrfkH/P9W3s59Gyeog2x25k/YOt9fIsTYFrSXg3ZETgS4A1A2zSl5YSCYylRoOhteMFt/u2Mwnf7bQLQzIPetSivwetF2kXNxEPzd4/2IMR1TO8+P1LLsVUFof87dN7IMVGQMPdVopYU00W2twI5f9qoHhLkjJSFgPoW1JuN2VpOSbknIuug1DOh49hdfRKS/r4kibmqTtbxSs6qpoJ4jaTwIpWc5T/pzv9CRfxEJF4OKH4ID2rlZa7RLM5SBRajzG6bTdO8ZmzjvUp9H/+e3eLKnPgeo4iBQIPg7KdfMAO5yhEg3t2IOpVQuaiuRnb06KS0h6b8NMsd6Yz4L+g+01bahLXaKR/jMH8hFrkmlWqWEKai56p/8IsUSmtFxi8iSEMjjLHfScEoIutjry6kqnUIwwBos1TxJx4RYmEP3PxXRkznStllhyVVoQJoPxGmukJnaA==',
    'extole_access_token': '174I6BNP8EEEITFN5UT87BDHV2',
    'AKA_A2': 'A',
    'dwsid': 'OFMv-Hbao73uJu996x6apjdy4QvQhHl8DF1Rnu1sTkaggo50FYlVQ_aMJr8OnyRqt6gXPIEMZET5igkUXfBTdg==',
    'BVBRANDSID': 'dbd7e739-61ba-4269-8996-c3b9e620128f',
    'sid': 'Hnu7hj7uPu255EHicubNNBFadXWYsOQsW58',
    'bm_so': '8EDFFB778FE600D076C7B559885D52E3A473BF26B2429E90936D775DEDA1FFD4~YAAQRw7SF5eMNu+fAQAADGyiDghBb87Ry3vAxnUpuSebxdDReqW2pfHnSgMFcyCEJBVN9/vh249SGIAed2utsRB/4fcHY8XqO1W+X0WAzJCfxSRs1WlxW8Ljb7DPLW6qT8lYyvOfOl5x7NRNv+bXjswvUWomB8NI03PsW0jfJ7xtMHfy0nC+4ZeCHwChwjkAKlUv/WmupVsAqGipasMLptR7DNjih77uPN1pne8OxH+tO7LFsFNqG41ifWZqHl2cTwqcoBoZlRn5KHtlnHSC347npTuzz7gok9cFAMBx6fiAtvQqYuOn9qd5RFMw4NIlOO12NOQmeWiTQS1tfMlW6EMq8JjMkEivdVO+aLLimSAcvaP9zCyLi7OZGITjx7W/8JMwWKmrq72akHg77LzjzeOyi1QlgHgeWIndqHr74gD+NuVEXkYM330ubEIML72pqEjuDaE5abZwFbEu7paJoOk=',
    'bm_sz': 'BE582C72D64B6B665D8D0FFD7DE1BFB0~YAAQRw7SF3+NNu+fAQAAl3miDgDO/KZB7qz93fKw5cFHkCkmWGwAUTrFLW3Wj/d/UKDtzrOKrV6flMGguMSIi1SNDdUvZ8sImjZeMxrVvvAG3m3bPURszJoUyZcOrjlC+Vm+9lq37e6fPYIF3COA/3AiJbCiflC2iHij8Q9MUYx0qmJ1rONaPg1VYCoEnGjb+x4sIgtq96vL4sWo1DCAsw1sPi5uPopEo/dgfp+mxkUGz5LeMmkEYbqLLeyPQiHlXQMbfq8/Zc+CqYCI28AYN2plke8LItKB6uEenL27E11Uk0ELXANXOgcnv+zrs5+fybv/NsbOgAZbLle/y28k18DaRU6kZLxD+S5bmDsm06CuS2PO7YAu5Vp7wLAYjBLfZGEzCnZnvq3x7MU7GTxPxRZ9TXWCSP0C69OBtUydPW0hRFyfONH1TThzoizIqt8aGQDOLmuH2Ntcdi6Hua78oGdA75P9CxKfSWxHL42b6LfBguty/cu7DQbn29Op9fAh30EWkoqWEwJW+apClkBvlbFLzgBVIWe/cs/TLQhftnjhWJygLmt4fTdSBWcM5CY8QmY/zTfQgFwUwYffv+aXSxQHpQ==~3228467~3159603',
    'bm_lso': '8EDFFB778FE600D076C7B559885D52E3A473BF26B2429E90936D775DEDA1FFD4~YAAQRw7SF5eMNu+fAQAADGyiDghBb87Ry3vAxnUpuSebxdDReqW2pfHnSgMFcyCEJBVN9/vh249SGIAed2utsRB/4fcHY8XqO1W+X0WAzJCfxSRs1WlxW8Ljb7DPLW6qT8lYyvOfOl5x7NRNv+bXjswvUWomB8NI03PsW0jfJ7xtMHfy0nC+4ZeCHwChwjkAKlUv/WmupVsAqGipasMLptR7DNjih77uPN1pne8OxH+tO7LFsFNqG41ifWZqHl2cTwqcoBoZlRn5KHtlnHSC347npTuzz7gok9cFAMBx6fiAtvQqYuOn9qd5RFMw4NIlOO12NOQmeWiTQS1tfMlW6EMq8JjMkEivdVO+aLLimSAcvaP9zCyLi7OZGITjx7W/8JMwWKmrq72akHg77LzjzeOyi1QlgHgeWIndqHr74gD+NuVEXkYM330ubEIML72pqEjuDaE5abZwFbEu7paJoOk=~1786951928457',
    'last_visit_bc': '1786951930019',
    '_ga_ANASER001': 'GS2.1.s1786950270$o3$g1$t1786951932$j55$l0$h103662693',
    '_ga_YGVM1D8ER1': 'GS2.1.s1786938135$o1$g1$t1786951932$j55$l0$h349554001',
    'forterToken': '0b4b55eda765474eb76bcb639f7cef85_1786951926568__UDF43-m4_27ck_U9TtQ4gCVjE%3D-365-v2',
    'forterToken': '0b4b55eda765474eb76bcb639f7cef85_1786951926568__UDF43-m4_27ck_U9TtQ4gCVjE%3D-365-v2',
    '_abck': 'D6EDF1B899428EC9D7895216B2C546A8~0~YAAQRw7SF0+RNu+fAQAASLeiDhAqWt2KkmR4qDMMDHE4RUpfiBDESyb9w6uoUxldBT/oJhhXPJsodlusUeXLjhpEQAihWELv8LGMXOqQgcZdd+II+SaiJWCWSqu33VDskpBDHsqObDZFj7YbYBotI8NFUwV51gZBEYKfgaFndwoTYdEzgQAbqQjogx5QLrB8Mk6Lo8nKEnM4LviyQX8Sl/EiI/VtFpP0iwfKM9pOKIut2CdbX946YTvZJh1uLQ/Lj2/c4bVM/1uKYDQtdxrck7pk7jTXHmbnq47F7YWhJtYETNppi2M+xytcdwDiLeeLLxihtVCpsx42abwj6eFnN0d+1TJhijdPk4XqslyA+1YkJtYMoUtWlOTeOgeWiEyxlb2a5pqGWqoYyfL5zmcF6v2UULb8CFMH3xKlqGNYiB4ebNjDuzgZOS+NhuEz0o6AWexOSGkkQss9FUlOGMB5w8qVMmqz6QrZKIN4lED11+MC2PQ387NlTIzixkJHqdXe8gKe7WVKcVDozYdFLIuVUZqqA4Ymre1hEcIaabv+0D6DVhUfqiT2xdV8hISIOOjtJHDVJbQ6k2qe4AyRyhnnHNO0Pckb1LkwUur4tD39iwHWXQz1bH2CIdL0zJqPJyRWJ1cBu0s4jECLR2egKsCqputB6wSniGfC/3urlRhoTKnRS7BQNhqDyXeGOBEmXu+Yvl6xuqpHKK03cJGGlqLTZY5RAVo=~-1~-1~-1~AAQAAAAG%2f%2f%2f%2f%2f0CDb+Lt+c8vk1FY0OHI9Z0fREYYy5Po4Ol7GIsCQcoLwasTk91%2fhB7LrL75%2fEVOwdsD6SFW8TXdt3jELSRjsIoduVtVqckxugjCq7cKJDLKDsiJGC8hST9rTz9BmVIwyCUm4VlpF1pi5xjaORxobQm5mhbV8P%2f+p3qEM9VmVCBJZ1rgFp1Caoe0GQRAq7pVFoTBIOTib5Rq~-1',
    'bm_s': 'YAAQRw7SFyKUNu+fAQAAYuGiDgXGz+vK/p9HJ2jeVNp/DOyD5zzj+4u/LTeP2DRcvCURTlQcJRbqLyLpC3QdAyI+LGBGtvieZdWKiz+iRLOjNtoecy308jcmglyZ3CP/4Iq4v+I1wS0PDysx6//AFnY7ea9DM9HFwvlw+4hpLdPXLpz/LdAUioZX95jzl6F+3w+CC3hu3rpzvmk5gwwWTOXy5lDqZfb7rsE2eu1T8/z5Jc9hanvRuT2edahzCPSHtnXIiMG20ivpyScDel3f+umCDjaoqNRBMnrElwumgoS6yPW943jmVi3HpR3G9bFcPdxVGv6/Sxfb6zx0QiGP6fuccoK2mgIFwULEsS0/Hl2KQ2jItXPCnlnrud+dKHEWTfLYu+6PoT7jGCWdRXJ8Fofd0zrChkSk/9a1TBIN7hvN7hodU68F4UHLPS7C52Lcj8OMZgYV7x+k5RphyfYpSFIRJ9V1FIkm9UKh8W35peqDLIe33tZFAMdlPR+3Dzqg+s00Ud//WNqAGNKtSI993ny9g6GUA1gal8AXB6J8C1QZkUc0sm/utacgLaLMHWjsHxKHrXIr5jqKVg0ecyyIOLlNBzHoGlhn8gvtCt+8vEa9jZkQK0kWlPRGlwh77ZLuaKXBvPsUtiroi6fw1w43kuOwiPMZAe/kiSj+f7lc1jLJeJysHUGbnMtSIlRJtZDiEPEDgfotin6HpusxOKKL0dlUXgbAGYG05jGt/YUzgMFA35yLe/hmxW8rmQYbE++TKjjThuFcaR08dQ4v1CWExEUu+C9PUTXDpjhVmY4TMF33pyhO3G2V2HlT+wv0gAmldpi8bG2iePdDxhviDLnslnDNZ5drVaXQN+XbVAJ0EBka6ayKQgOoz0EENsZI0LaYqfwsh7nPOmDFkps1ycEpy5NqLZrYuympPjOrkhqSUHmuzn5n1FuZ0ViTTuFebQr7c5js6aF6qX/tR8ermYR5x9aiyBRLMYBo2Zjd5M4dJEgrl1j9Yn9KwXf469V3NT/xH/qjARY2CcDFKUCB2CiqQo04a49e6MDvKtCmXspwxeo=',
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
    # 'cookie': 'OptanonAlertBoxClosed=2026-08-17T07:32:09.354Z; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Aug+17+2026+15%3A32%3A11+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202504.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=dd41da20-804a-4aa2-8abc-469817bacc86&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0005%3A1%2CC0001%3A1%2CBG441%3A1%2CC0002%3A1%2CC0003%3A1%2CBG442%3A1&intType=1&geolocation=US%3BCA&AwaitingReconsent=false; user_country=HK; dwanonymous_a0bee6d5d02f73f6e619681126569802=abwHk0wKs1kXgRxbkYxaYYlrFF; _ga=GA1.1.1765035832.1786938135; _gcl_au=1.1.1254396896.1786938135; FPID=FPID2.2.2BBrQaheVcrZfLr61eRHKvbUdj7u0lE2qhkz9M%2FCImM%3D.1786938135; _scid=13df4536-ef75-48aa-e8ef-873da1911d06; _gtmeec-tt=eyJjb3VudHJ5IjoidXMifQ%3D%3D; FPLC=WkD9nONJyFDB5ybPTUyi3GS8umKpWClO2NHXT%2BmlbW7FlNiCkv1WUml37GrgwDF6r%2F3Eg7pBj4Yt%2FiIQV2ad2frsv6oPbyFd8gsKutWzhaP9%2FoI3XvHNzfvLUk3MHg%3D%3D; _fbp=fb.1.1786938136765.654244661702356831.AQYCAQMB; BVBRANDID=dd62c723-44b9-4724-97ae-5fbd6f3dbd36; BCSessionID=ba9706fb-a13d-4cc5-ad56-a9759426f6cd; __cq_dnt=1; dw_dnt=1; bv_metrics=true; IM_surveyAction=open; IM_shown_1643=true; bm_mi=C9E9E1A177C35B7CF524148EC2D1E17F~YAAQRw7SFwJfLu+fAQAAWA0/DgBZw499AO94n9jeh1lpYPGhQQo0VJUKvjICzKKVVU9p+Vf3OdKP2sl7k3+8S/o+sLdNogJUEKGXDOOcAbPNYmJ0MXb9SE5imnnTffepOEEjNuZYHIy6Bo5jaUw6a97g9a7mt9CIPBVg6JGUH2zCk1fbGLpFvdpI7rSbxb2kJ4pXPOMGIv41ysGLMvEX2nuFmWfMlD5ZFgaF/+O6NL3zfxH7WYtu4trWfsDBeDVjjpAD371MEHivpm/D6GqZSRnrSygVFz/Cyw4tLAd4RwDTVRzwyH2PSIcF77IXe2N+7bKlPnKFFMSKDUYyTvF+/cPgbajt391BiwbBiwzdTGYgqYsAhBcr/nBm3knKR/0=~1; ak_bmsc=53288B62C63E9ABBA17115FA5BD85DB4~000000000000000000000000000000~YAAQRw7SF6NgLu+fAQAA9Rs/DgAmOeUNFhDquXmWmt9Q3otsVf1jKe2b4AiABqUBSdISz49vkf6KB1ulnUOmmz9olfYCe9eR0qk/5S4TfrfkH/P9W3s59Gyeog2x25k/YOt9fIsTYFrSXg3ZETgS4A1A2zSl5YSCYylRoOhteMFt/u2Mwnf7bQLQzIPetSivwetF2kXNxEPzd4/2IMR1TO8+P1LLsVUFof87dN7IMVGQMPdVopYU00W2twI5f9qoHhLkjJSFgPoW1JuN2VpOSbknIuug1DOh49hdfRKS/r4kibmqTtbxSs6qpoJ4jaTwIpWc5T/pzv9CRfxEJF4OKH4ID2rlZa7RLM5SBRajzG6bTdO8ZmzjvUp9H/+e3eLKnPgeo4iBQIPg7KdfMAO5yhEg3t2IOpVQuaiuRnb06KS0h6b8NMsd6Yz4L+g+01bahLXaKR/jMH8hFrkmlWqWEKai56p/8IsUSmtFxi8iSEMjjLHfScEoIutjry6kqnUIwwBos1TxJx4RYmEP3PxXRkznStllhyVVoQJoPxGmukJnaA==; extole_access_token=174I6BNP8EEEITFN5UT87BDHV2; AKA_A2=A; dwsid=OFMv-Hbao73uJu996x6apjdy4QvQhHl8DF1Rnu1sTkaggo50FYlVQ_aMJr8OnyRqt6gXPIEMZET5igkUXfBTdg==; BVBRANDSID=dbd7e739-61ba-4269-8996-c3b9e620128f; sid=Hnu7hj7uPu255EHicubNNBFadXWYsOQsW58; bm_so=8EDFFB778FE600D076C7B559885D52E3A473BF26B2429E90936D775DEDA1FFD4~YAAQRw7SF5eMNu+fAQAADGyiDghBb87Ry3vAxnUpuSebxdDReqW2pfHnSgMFcyCEJBVN9/vh249SGIAed2utsRB/4fcHY8XqO1W+X0WAzJCfxSRs1WlxW8Ljb7DPLW6qT8lYyvOfOl5x7NRNv+bXjswvUWomB8NI03PsW0jfJ7xtMHfy0nC+4ZeCHwChwjkAKlUv/WmupVsAqGipasMLptR7DNjih77uPN1pne8OxH+tO7LFsFNqG41ifWZqHl2cTwqcoBoZlRn5KHtlnHSC347npTuzz7gok9cFAMBx6fiAtvQqYuOn9qd5RFMw4NIlOO12NOQmeWiTQS1tfMlW6EMq8JjMkEivdVO+aLLimSAcvaP9zCyLi7OZGITjx7W/8JMwWKmrq72akHg77LzjzeOyi1QlgHgeWIndqHr74gD+NuVEXkYM330ubEIML72pqEjuDaE5abZwFbEu7paJoOk=; bm_sz=BE582C72D64B6B665D8D0FFD7DE1BFB0~YAAQRw7SF3+NNu+fAQAAl3miDgDO/KZB7qz93fKw5cFHkCkmWGwAUTrFLW3Wj/d/UKDtzrOKrV6flMGguMSIi1SNDdUvZ8sImjZeMxrVvvAG3m3bPURszJoUyZcOrjlC+Vm+9lq37e6fPYIF3COA/3AiJbCiflC2iHij8Q9MUYx0qmJ1rONaPg1VYCoEnGjb+x4sIgtq96vL4sWo1DCAsw1sPi5uPopEo/dgfp+mxkUGz5LeMmkEYbqLLeyPQiHlXQMbfq8/Zc+CqYCI28AYN2plke8LItKB6uEenL27E11Uk0ELXANXOgcnv+zrs5+fybv/NsbOgAZbLle/y28k18DaRU6kZLxD+S5bmDsm06CuS2PO7YAu5Vp7wLAYjBLfZGEzCnZnvq3x7MU7GTxPxRZ9TXWCSP0C69OBtUydPW0hRFyfONH1TThzoizIqt8aGQDOLmuH2Ntcdi6Hua78oGdA75P9CxKfSWxHL42b6LfBguty/cu7DQbn29Op9fAh30EWkoqWEwJW+apClkBvlbFLzgBVIWe/cs/TLQhftnjhWJygLmt4fTdSBWcM5CY8QmY/zTfQgFwUwYffv+aXSxQHpQ==~3228467~3159603; bm_lso=8EDFFB778FE600D076C7B559885D52E3A473BF26B2429E90936D775DEDA1FFD4~YAAQRw7SF5eMNu+fAQAADGyiDghBb87Ry3vAxnUpuSebxdDReqW2pfHnSgMFcyCEJBVN9/vh249SGIAed2utsRB/4fcHY8XqO1W+X0WAzJCfxSRs1WlxW8Ljb7DPLW6qT8lYyvOfOl5x7NRNv+bXjswvUWomB8NI03PsW0jfJ7xtMHfy0nC+4ZeCHwChwjkAKlUv/WmupVsAqGipasMLptR7DNjih77uPN1pne8OxH+tO7LFsFNqG41ifWZqHl2cTwqcoBoZlRn5KHtlnHSC347npTuzz7gok9cFAMBx6fiAtvQqYuOn9qd5RFMw4NIlOO12NOQmeWiTQS1tfMlW6EMq8JjMkEivdVO+aLLimSAcvaP9zCyLi7OZGITjx7W/8JMwWKmrq72akHg77LzjzeOyi1QlgHgeWIndqHr74gD+NuVEXkYM330ubEIML72pqEjuDaE5abZwFbEu7paJoOk=~1786951928457; last_visit_bc=1786951930019; _ga_ANASER001=GS2.1.s1786950270$o3$g1$t1786951932$j55$l0$h103662693; _ga_YGVM1D8ER1=GS2.1.s1786938135$o1$g1$t1786951932$j55$l0$h349554001; forterToken=0b4b55eda765474eb76bcb639f7cef85_1786951926568__UDF43-m4_27ck_U9TtQ4gCVjE%3D-365-v2; forterToken=0b4b55eda765474eb76bcb639f7cef85_1786951926568__UDF43-m4_27ck_U9TtQ4gCVjE%3D-365-v2; _abck=D6EDF1B899428EC9D7895216B2C546A8~0~YAAQRw7SF0+RNu+fAQAASLeiDhAqWt2KkmR4qDMMDHE4RUpfiBDESyb9w6uoUxldBT/oJhhXPJsodlusUeXLjhpEQAihWELv8LGMXOqQgcZdd+II+SaiJWCWSqu33VDskpBDHsqObDZFj7YbYBotI8NFUwV51gZBEYKfgaFndwoTYdEzgQAbqQjogx5QLrB8Mk6Lo8nKEnM4LviyQX8Sl/EiI/VtFpP0iwfKM9pOKIut2CdbX946YTvZJh1uLQ/Lj2/c4bVM/1uKYDQtdxrck7pk7jTXHmbnq47F7YWhJtYETNppi2M+xytcdwDiLeeLLxihtVCpsx42abwj6eFnN0d+1TJhijdPk4XqslyA+1YkJtYMoUtWlOTeOgeWiEyxlb2a5pqGWqoYyfL5zmcF6v2UULb8CFMH3xKlqGNYiB4ebNjDuzgZOS+NhuEz0o6AWexOSGkkQss9FUlOGMB5w8qVMmqz6QrZKIN4lED11+MC2PQ387NlTIzixkJHqdXe8gKe7WVKcVDozYdFLIuVUZqqA4Ymre1hEcIaabv+0D6DVhUfqiT2xdV8hISIOOjtJHDVJbQ6k2qe4AyRyhnnHNO0Pckb1LkwUur4tD39iwHWXQz1bH2CIdL0zJqPJyRWJ1cBu0s4jECLR2egKsCqputB6wSniGfC/3urlRhoTKnRS7BQNhqDyXeGOBEmXu+Yvl6xuqpHKK03cJGGlqLTZY5RAVo=~-1~-1~-1~AAQAAAAG%2f%2f%2f%2f%2f0CDb+Lt+c8vk1FY0OHI9Z0fREYYy5Po4Ol7GIsCQcoLwasTk91%2fhB7LrL75%2fEVOwdsD6SFW8TXdt3jELSRjsIoduVtVqckxugjCq7cKJDLKDsiJGC8hST9rTz9BmVIwyCUm4VlpF1pi5xjaORxobQm5mhbV8P%2f+p3qEM9VmVCBJZ1rgFp1Caoe0GQRAq7pVFoTBIOTib5Rq~-1; bm_s=YAAQRw7SFyKUNu+fAQAAYuGiDgXGz+vK/p9HJ2jeVNp/DOyD5zzj+4u/LTeP2DRcvCURTlQcJRbqLyLpC3QdAyI+LGBGtvieZdWKiz+iRLOjNtoecy308jcmglyZ3CP/4Iq4v+I1wS0PDysx6//AFnY7ea9DM9HFwvlw+4hpLdPXLpz/LdAUioZX95jzl6F+3w+CC3hu3rpzvmk5gwwWTOXy5lDqZfb7rsE2eu1T8/z5Jc9hanvRuT2edahzCPSHtnXIiMG20ivpyScDel3f+umCDjaoqNRBMnrElwumgoS6yPW943jmVi3HpR3G9bFcPdxVGv6/Sxfb6zx0QiGP6fuccoK2mgIFwULEsS0/Hl2KQ2jItXPCnlnrud+dKHEWTfLYu+6PoT7jGCWdRXJ8Fofd0zrChkSk/9a1TBIN7hvN7hodU68F4UHLPS7C52Lcj8OMZgYV7x+k5RphyfYpSFIRJ9V1FIkm9UKh8W35peqDLIe33tZFAMdlPR+3Dzqg+s00Ud//WNqAGNKtSI993ny9g6GUA1gal8AXB6J8C1QZkUc0sm/utacgLaLMHWjsHxKHrXIr5jqKVg0ecyyIOLlNBzHoGlhn8gvtCt+8vEa9jZkQK0kWlPRGlwh77ZLuaKXBvPsUtiroi6fw1w43kuOwiPMZAe/kiSj+f7lc1jLJeJysHUGbnMtSIlRJtZDiEPEDgfotin6HpusxOKKL0dlUXgbAGYG05jGt/YUzgMFA35yLe/hmxW8rmQYbE++TKjjThuFcaR08dQ4v1CWExEUu+C9PUTXDpjhVmY4TMF33pyhO3G2V2HlT+wv0gAmldpi8bG2iePdDxhviDLnslnDNZ5drVaXQN+XbVAJ0EBka6ayKQgOoz0EENsZI0LaYqfwsh7nPOmDFkps1ycEpy5NqLZrYuympPjOrkhqSUHmuzn5n1FuZ0ViTTuFebQr7c5js6aF6qX/tR8ermYR5x9aiyBRLMYBo2Zjd5M4dJEgrl1j9Yn9KwXf469V3NT/xH/qjARY2CcDFKUCB2CiqQo04a49e6MDvKtCmXspwxeo=',
}

@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url,headers=headers,cookies=cookies)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    # import re, json
    # res_text = res.text
    # match = re.search(r"nineyi\['__PRELOADED_STATE__'\]\s*=\s*([^;]+);", res_text)
    # if match:
    #     data = json.loads(match.group(1))
    #     Tool.File.save_json(data,js_path)

    ml1 = html.xpath('//li[@class="navigationMenu__item"]')


    header_node = ml1

    for node in header_node:


        _name = node.xpath('./button//text()')

        _name = ''.join(_name).strip()
        url_dic[_name] = {'child':{}}

        childs = node.xpath('./div/div/div/div')


        f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    # node = childs
    #
    # childs = node['additionalChildList']
    # child_id_key = node['childList']
    #
    # key_dic = {}
    # for i in child_id_key:
    #     name = i['text']
    #     c_id = i['itemKey']
    #     key_dic[c_id] = name

    if childs:



        for i in childs:
            print(66666)
            Tool.HTML.to_str(i)
            _childs = i.xpath('./ul/li')

            for child in _childs:


                _name = child.xpath('./a//text()')

                _name = ''.join(_name).strip()

                dic[_name] = { 'child': {}}

                n_childs_ls = child.xpath('./div/ul/li')
                f3(dic[_name]['child'],n_childs_ls)

    return dic


def f3(dic,childs):
    for child in childs:
        c_a = child.xpath('./a')

        c_tx, c_url = Tool.HTML.get_a_text_and_url(c_a[0])
        _name = c_tx
        _url = c_url
        _url = Tool.URL.add_site(_url)

        dic[_name] = {'url': _url, 'child': {}}


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



