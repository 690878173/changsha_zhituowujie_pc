import hashlib
import json
import time

import requests
from lxml import etree
from config import Tool

file_path = Tool.File.path_add_site('data/ml.json')
save_path = Tool.File.path_add_site('data/detail_url.json')
catch_path = Tool.File.path_add_site('hc/2/data.json')

index_path = Tool.File.path_add_site('hc/2/index.json')

# 测试数据条数,以初始url数量计数
ts_num = None

# 排除某些 URL
input_url_no_ls = []
output_url_no_ls = []

# 覆盖缓存
flush = False
cookies = {
    'device-id': 'fd1f440a-0948-4d9e-933f-6d3922117a19',
    'pid': 'NoEFWgvUQpCvC6FBuKxH6Q',
    'abTestingAnonymousPID': 'NoEFWgvUQpCvC6FBuKxH6Q',
    '_ga': 'GA1.1.1719990769.1786688366',
    'ajs_anonymous_id': 'be583619-fa8e-4ab6-804e-7e521d505c05',
    '_iidt': 'gYYryEs4QDhuGOpSLPXcLGMK3PxVPErVaCLMdD2dDFCmEe1p/C9FGK93dhSIGV/mrdhYHyGzRNknMg==',
    '_vid_t': 'hIHdCswvk0h7KczvytS5ZDKPk5ctHM9rNZ564uwhTZW9Qg8UfaTHQIca25Q7yakrP8oEffYzQ3fPbg==',
    'fppro_id': '{"rid":"1786688384153.OUXOU4","vid":"Tjwr9NL0253VhNXLhUr9","exp":1787120383478}',
    '_pin_unauth': 'dWlkPVlqSm1abVJsTkRZdFltRmpaUzAwTXpCa0xUaG1ObUV0WVRSaFpqRTVZV0kyWkdGag',
    '__obref': '025f3d5d-8514-48f5-ac10-d30dd5f20561',
    'forterToken': '7d944be9d9fe40f7825fc257c1e0b16e_1786786543776_2559_UDF43-m4_23ck_',
    'bm_so': '52F56633893E55454BA267169DE4CF8354D34064125F06EDD4337B9CCFDF3865~YAAQD3HKF20fVwagAQAAUvJ5EgjMUa0w1XVzTXcZJxbKGt62idmGsq6wMxwC27jeIg7Eb5W/WQrRXD20f934yZlU7dR2S1XNhM016eiJEeipomZJ/BFcUWdlkUJldHiGVzQUiRJyolThrbdyeS1EDVcpr02cQjwZ/yxr6WgqIuH0gkQrRP4JQ937jvWqJOtcNU/60G16tlqvMisNyBdKimamcVsKLmtZtVRciWed/sdAA4axzhnlMJ6H5Q9geZXcwXzXTLWrFvU9dKrCz4EPV30cVsCIAaEEsv4287YgDn/inVq3klqKQvl6UZ+QdGMTCjQGMsqSQ/u9gwFGYR+TPJ/MICXQUMr8HLgGQ2fYmgTfEaz+HYjiI4O/h8uae41QkQlyvL55JEUJCP96XKhW5y3ChgRV8/S8sEAAc90rfzT6W3sEzYimpf4F2E5HnfRJjYHnWz4cMTnixx3inEdltzYhqW9i6j8ZGA==',
    'bm_lso': '52F56633893E55454BA267169DE4CF8354D34064125F06EDD4337B9CCFDF3865~YAAQD3HKF20fVwagAQAAUvJ5EgjMUa0w1XVzTXcZJxbKGt62idmGsq6wMxwC27jeIg7Eb5W/WQrRXD20f934yZlU7dR2S1XNhM016eiJEeipomZJ/BFcUWdlkUJldHiGVzQUiRJyolThrbdyeS1EDVcpr02cQjwZ/yxr6WgqIuH0gkQrRP4JQ937jvWqJOtcNU/60G16tlqvMisNyBdKimamcVsKLmtZtVRciWed/sdAA4axzhnlMJ6H5Q9geZXcwXzXTLWrFvU9dKrCz4EPV30cVsCIAaEEsv4287YgDn/inVq3klqKQvl6UZ+QdGMTCjQGMsqSQ/u9gwFGYR+TPJ/MICXQUMr8HLgGQ2fYmgTfEaz+HYjiI4O/h8uae41QkQlyvL55JEUJCP96XKhW5y3ChgRV8/S8sEAAc90rfzT6W3sEzYimpf4F2E5HnfRJjYHnWz4cMTnixx3inEdltzYhqW9i6j8ZGA==~1787016377414',
    'experiment_': '',
    'bm_sc': '4~1~399789654~YAAQD3HKFx0pVwagAQAARQB6Eglg1dwO24FZcSJWR/XNxK1VBOh3+0b+gRgp3Euo/Q5DwLwIj/NDY7uYn241RsACfVyL4rFW3GqTi3URZoasJQJF1wCJ5WHW1H4r2gqLBJRS5XlPtqADmoa7gty76/qUlH3/kJoTMRhaUqrBkGTJ5Y48oLJBJJEAjxxKp6XYF3EFSOy9/JVPiKzuI0wISOcao9Z7QAl3ViUiFX6Nl96+o4gEE3M+pbTHNqGHU4mt38aGLi1JxlQB6UoEY9QOQo8QUyZhT937LNojiFmUHTSGmLJy/r8Hotq9G5ZvB3uisF+ZI8lJRZaoTglzXAr4pCDMrI6iZxiTsZdwLOr3Qwk0ZH9pf2T1YG9pK4hV/DPzM48/xX730m03449bc6sjXpHnLyv2Y/7iVko75t7AciA3PW1W0haBw7xsP+e2OdZEmykfdNXmY2/R0dwgFEvHSO/JQ1AXKb3z8Vuam9+Wyk61WRo3DVxEa5lVpUxxZjwXG+JxzZEnd/7j7Rc=~0~0~0',
    'sid': 'f03fcb08-b7fb-4d9c-bb3c-e2ebd55c66a3',
    'KP_UIDz-ssn': '0chjGlrCxG0rbYuhTpL3G71KLvqu9sfN9dJP4OV7RDOtCy9pfAO5NyDCJ5c3GYlMHjBvD8VMANb0YoTqAz1RvKbTSyRwNMuLna8S0DaeD8xq2vTnspq4ZVt4p79YvW8SfzG9xphCh2sqvnoY9M5vAskV33XloZ3dJLSkt4qkEJHUbYb',
    'KP_UIDz': '0chjGlrCxG0rbYuhTpL3G71KLvqu9sfN9dJP4OV7RDOtCy9pfAO5NyDCJ5c3GYlMHjBvD8VMANb0YoTqAz1RvKbTSyRwNMuLna8S0DaeD8xq2vTnspq4ZVt4p79YvW8SfzG9xphCh2sqvnoY9M5vAskV33XloZ3dJLSkt4qkEJHUbYb',
    'bm_s': 'YAAQBnHKF5F7UQagAQAA/zl6EgUNmZc+GAPy7tER3tAiia5CxGCovwF+TSXQk+SWwZHolW4/wJjFuhgR5FQVHCIfveYJKpg86DAl9VFYkN49T87dzX0+0lZzUE2rWYINeNQ1rev12WB8WLzO3EzxhZtuTAUV9yc1l8L89hbuIK1zOhVH2rIDbVVBQD+4hzfhNWyI7F8tN8kNiFOxjKocReP2lwHV6eQ1CLl1zezDaAv9dveJO7d42wCCT8xcqCNIhiYblDZ4u660SM8Wqxj6b9js7tLvNu6efcInFdpUstkcKL9/+LJ3I6NUBhiyzxbjVOTvJG7/otLSsU49ZmrzSGNIem9ia5T7PAg0Ypl4B4WZfj7pNnRPAfxTFUI1xreV9/fg8cwOn/WcOBsGvi5Q+hpP6Ks3+zeRU7T3M6K4civJ9OzKCQ2MugaoapWczRmzrE2RXHzKherqmOF7PcJtAzMl6BFOAKMt5isCCf7wv4v5cYoR0zUr/aFFs4no9/yV+JFYDOt+koMRwrfSqiXSuyiwDqeroQyhhDymZKdwvu7UrLu/dOtNn4xd1lha9LxF7wySQyUx/whmM42i4vTzGRJZR3aQdq+DK1qOjwRjLcnfAYxhX6PC9sgxysEA0uXnpuOvY05J6XkqyCaHle7C4S5f18chWju7hAYdZ+P8S8X9iKUNc959CCh8uqDm6SlGzFWdjmknYRUttQlPXbbDozNKjUfZRDMkwYVi2TI5qNBmuMk8Fjc4Xa04/JGm0dDQ9BVolZQ6ZUHBKofOXlm+Dg+1jcMoCsVtrwXoEBB1mabQe7pQV68BKIWe/O7u9DShbKfiSOL81N0Mw4YXDbXSZ+upPxgkdTlo50hpnhge1WnHhHhTHJUnf03750B5aSpmPu8Hnq4QsFQa5xaeRghPVqHaiP4pQrB+p9jgaPMN7QKlWc+bHomnw7tbm1e5lU7XW2oREDLnopzxkNrWbN+dtgIycDTQwnhCr56EcUi1Pbxev7D+Tv/Q5DxZGiJ59tWgdZVzzPGW+w8gmee4qyAXFTm34YwE4XntsvpjT5/oRr/4efBSIh0MbjEGum6LsnaPqyv9IXouI5+9+FLPBT6hncopSN0BU9Pe',
    'pageviewCount': '82',
    '_ga_GM4GWYGVKP': 'GS2.1.s1787016382$o13$g1$t1787016395$j47$l0$h376535105$d7XwqMX0XqhUj6c_2QDA52oMR86ZzrMum2A',
    '_gcl_au': '1.1.961155179.1786688360.-.-.1786688369.1828179980.1786963601.1787016397',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Tue+Aug+18+2026+09%3A26%3A41+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202604.2.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=BG36%3A1%2CC0004%3A1%2CC0010%3A1%2CC0011%3A1%2CC0001%3A1%2CC0003%3A1%2CC0002%3A1&AwaitingReconsent=false',
    'pageviewCount30m': '3',
    'akaalb_chewy_ALB': '1787017020~op=chewy_com_ALB_use2:www-chewy-use2|~rv=76~m=www-chewy-use2:0|~os=43a06daff4514d805d02d3b6b5e79808~id=13c8d82a9d43855e522bd89dc6ca08eb',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.chewy.com/',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    # 'cookie': 'device-id=fd1f440a-0948-4d9e-933f-6d3922117a19; pid=NoEFWgvUQpCvC6FBuKxH6Q; abTestingAnonymousPID=NoEFWgvUQpCvC6FBuKxH6Q; _ga=GA1.1.1719990769.1786688366; ajs_anonymous_id=be583619-fa8e-4ab6-804e-7e521d505c05; _iidt=gYYryEs4QDhuGOpSLPXcLGMK3PxVPErVaCLMdD2dDFCmEe1p/C9FGK93dhSIGV/mrdhYHyGzRNknMg==; _vid_t=hIHdCswvk0h7KczvytS5ZDKPk5ctHM9rNZ564uwhTZW9Qg8UfaTHQIca25Q7yakrP8oEffYzQ3fPbg==; fppro_id={"rid":"1786688384153.OUXOU4","vid":"Tjwr9NL0253VhNXLhUr9","exp":1787120383478}; _pin_unauth=dWlkPVlqSm1abVJsTkRZdFltRmpaUzAwTXpCa0xUaG1ObUV0WVRSaFpqRTVZV0kyWkdGag; __obref=025f3d5d-8514-48f5-ac10-d30dd5f20561; forterToken=7d944be9d9fe40f7825fc257c1e0b16e_1786786543776_2559_UDF43-m4_23ck_; bm_so=52F56633893E55454BA267169DE4CF8354D34064125F06EDD4337B9CCFDF3865~YAAQD3HKF20fVwagAQAAUvJ5EgjMUa0w1XVzTXcZJxbKGt62idmGsq6wMxwC27jeIg7Eb5W/WQrRXD20f934yZlU7dR2S1XNhM016eiJEeipomZJ/BFcUWdlkUJldHiGVzQUiRJyolThrbdyeS1EDVcpr02cQjwZ/yxr6WgqIuH0gkQrRP4JQ937jvWqJOtcNU/60G16tlqvMisNyBdKimamcVsKLmtZtVRciWed/sdAA4axzhnlMJ6H5Q9geZXcwXzXTLWrFvU9dKrCz4EPV30cVsCIAaEEsv4287YgDn/inVq3klqKQvl6UZ+QdGMTCjQGMsqSQ/u9gwFGYR+TPJ/MICXQUMr8HLgGQ2fYmgTfEaz+HYjiI4O/h8uae41QkQlyvL55JEUJCP96XKhW5y3ChgRV8/S8sEAAc90rfzT6W3sEzYimpf4F2E5HnfRJjYHnWz4cMTnixx3inEdltzYhqW9i6j8ZGA==; bm_lso=52F56633893E55454BA267169DE4CF8354D34064125F06EDD4337B9CCFDF3865~YAAQD3HKF20fVwagAQAAUvJ5EgjMUa0w1XVzTXcZJxbKGt62idmGsq6wMxwC27jeIg7Eb5W/WQrRXD20f934yZlU7dR2S1XNhM016eiJEeipomZJ/BFcUWdlkUJldHiGVzQUiRJyolThrbdyeS1EDVcpr02cQjwZ/yxr6WgqIuH0gkQrRP4JQ937jvWqJOtcNU/60G16tlqvMisNyBdKimamcVsKLmtZtVRciWed/sdAA4axzhnlMJ6H5Q9geZXcwXzXTLWrFvU9dKrCz4EPV30cVsCIAaEEsv4287YgDn/inVq3klqKQvl6UZ+QdGMTCjQGMsqSQ/u9gwFGYR+TPJ/MICXQUMr8HLgGQ2fYmgTfEaz+HYjiI4O/h8uae41QkQlyvL55JEUJCP96XKhW5y3ChgRV8/S8sEAAc90rfzT6W3sEzYimpf4F2E5HnfRJjYHnWz4cMTnixx3inEdltzYhqW9i6j8ZGA==~1787016377414; experiment_=; bm_sc=4~1~399789654~YAAQD3HKFx0pVwagAQAARQB6Eglg1dwO24FZcSJWR/XNxK1VBOh3+0b+gRgp3Euo/Q5DwLwIj/NDY7uYn241RsACfVyL4rFW3GqTi3URZoasJQJF1wCJ5WHW1H4r2gqLBJRS5XlPtqADmoa7gty76/qUlH3/kJoTMRhaUqrBkGTJ5Y48oLJBJJEAjxxKp6XYF3EFSOy9/JVPiKzuI0wISOcao9Z7QAl3ViUiFX6Nl96+o4gEE3M+pbTHNqGHU4mt38aGLi1JxlQB6UoEY9QOQo8QUyZhT937LNojiFmUHTSGmLJy/r8Hotq9G5ZvB3uisF+ZI8lJRZaoTglzXAr4pCDMrI6iZxiTsZdwLOr3Qwk0ZH9pf2T1YG9pK4hV/DPzM48/xX730m03449bc6sjXpHnLyv2Y/7iVko75t7AciA3PW1W0haBw7xsP+e2OdZEmykfdNXmY2/R0dwgFEvHSO/JQ1AXKb3z8Vuam9+Wyk61WRo3DVxEa5lVpUxxZjwXG+JxzZEnd/7j7Rc=~0~0~0; sid=f03fcb08-b7fb-4d9c-bb3c-e2ebd55c66a3; KP_UIDz-ssn=0chjGlrCxG0rbYuhTpL3G71KLvqu9sfN9dJP4OV7RDOtCy9pfAO5NyDCJ5c3GYlMHjBvD8VMANb0YoTqAz1RvKbTSyRwNMuLna8S0DaeD8xq2vTnspq4ZVt4p79YvW8SfzG9xphCh2sqvnoY9M5vAskV33XloZ3dJLSkt4qkEJHUbYb; KP_UIDz=0chjGlrCxG0rbYuhTpL3G71KLvqu9sfN9dJP4OV7RDOtCy9pfAO5NyDCJ5c3GYlMHjBvD8VMANb0YoTqAz1RvKbTSyRwNMuLna8S0DaeD8xq2vTnspq4ZVt4p79YvW8SfzG9xphCh2sqvnoY9M5vAskV33XloZ3dJLSkt4qkEJHUbYb; bm_s=YAAQBnHKF5F7UQagAQAA/zl6EgUNmZc+GAPy7tER3tAiia5CxGCovwF+TSXQk+SWwZHolW4/wJjFuhgR5FQVHCIfveYJKpg86DAl9VFYkN49T87dzX0+0lZzUE2rWYINeNQ1rev12WB8WLzO3EzxhZtuTAUV9yc1l8L89hbuIK1zOhVH2rIDbVVBQD+4hzfhNWyI7F8tN8kNiFOxjKocReP2lwHV6eQ1CLl1zezDaAv9dveJO7d42wCCT8xcqCNIhiYblDZ4u660SM8Wqxj6b9js7tLvNu6efcInFdpUstkcKL9/+LJ3I6NUBhiyzxbjVOTvJG7/otLSsU49ZmrzSGNIem9ia5T7PAg0Ypl4B4WZfj7pNnRPAfxTFUI1xreV9/fg8cwOn/WcOBsGvi5Q+hpP6Ks3+zeRU7T3M6K4civJ9OzKCQ2MugaoapWczRmzrE2RXHzKherqmOF7PcJtAzMl6BFOAKMt5isCCf7wv4v5cYoR0zUr/aFFs4no9/yV+JFYDOt+koMRwrfSqiXSuyiwDqeroQyhhDymZKdwvu7UrLu/dOtNn4xd1lha9LxF7wySQyUx/whmM42i4vTzGRJZR3aQdq+DK1qOjwRjLcnfAYxhX6PC9sgxysEA0uXnpuOvY05J6XkqyCaHle7C4S5f18chWju7hAYdZ+P8S8X9iKUNc959CCh8uqDm6SlGzFWdjmknYRUttQlPXbbDozNKjUfZRDMkwYVi2TI5qNBmuMk8Fjc4Xa04/JGm0dDQ9BVolZQ6ZUHBKofOXlm+Dg+1jcMoCsVtrwXoEBB1mabQe7pQV68BKIWe/O7u9DShbKfiSOL81N0Mw4YXDbXSZ+upPxgkdTlo50hpnhge1WnHhHhTHJUnf03750B5aSpmPu8Hnq4QsFQa5xaeRghPVqHaiP4pQrB+p9jgaPMN7QKlWc+bHomnw7tbm1e5lU7XW2oREDLnopzxkNrWbN+dtgIycDTQwnhCr56EcUi1Pbxev7D+Tv/Q5DxZGiJ59tWgdZVzzPGW+w8gmee4qyAXFTm34YwE4XntsvpjT5/oRr/4efBSIh0MbjEGum6LsnaPqyv9IXouI5+9+FLPBT6hncopSN0BU9Pe; pageviewCount=82; _ga_GM4GWYGVKP=GS2.1.s1787016382$o13$g1$t1787016395$j47$l0$h376535105$d7XwqMX0XqhUj6c_2QDA52oMR86ZzrMum2A; _gcl_au=1.1.961155179.1786688360.-.-.1786688369.1828179980.1786963601.1787016397; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Aug+18+2026+09%3A26%3A41+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202604.2.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=BG36%3A1%2CC0004%3A1%2CC0010%3A1%2CC0011%3A1%2CC0001%3A1%2CC0003%3A1%2CC0002%3A1&AwaitingReconsent=false; pageviewCount30m=3; akaalb_chewy_ALB=1787017020~op=chewy_com_ALB_use2:www-chewy-use2|~rv=76~m=www-chewy-use2:0|~os=43a06daff4514d805d02d3b6b5e79808~id=13c8d82a9d43855e522bd89dc6ca08eb',
}

def _api(url,par):

    gro_id = url.split('-')[-1]
    params = {
        'catalogId': '1004',
        'count': '36',
        'from': par.get('page')*36,
        'sort': 'byRelevance',
        'groupId': gro_id,
    }

    response = requests.get('https://www.chewy.com/plp/api/search', params=params, cookies=cookies, headers=headers)
    ls = []
    for i in range(3):
        try:
            data = response.json()['products']
            for df in data:
                url = df['href']
                ls.append(url)
            return ls,True
        except:
            pass

    return [],False


@Tool.zs('具体需重写=>获取详细链接，返回列表,下一页码')
def get_detail_url(url, par):
    is_next = False
    par['page'] = par.get('page', 0) + 1


    ls,is_next = _api(url,par)

    # res = Tool.get(url,headers=headers,cookies=cookies)
    # html = etree.HTML(res.text)
    # Tool.HTML.save(res.text)
    # ls = []
    #
    # data = html.xpath('//a[@class="kib-product-image product-card-image"]/@href')
    # print(len(data))
    # detail_links = data
    # a = html.xpath('.//a[@aria-label="Next Page"]/@href')[0]

    if is_next:
        par['next_url'] = url

    detail_links = ls
    print(detail_links)

    return detail_links,is_next


def get_detail_all_url(url):
    ls = []
    par = {}
    _num = 1
    while True:
        res_ls,is_next = get_detail_url(url, par=par)
        ls.extend(res_ls)
        if not is_next:
            break
        try:
            url = par['next_url']
        except:
            Tool.print(f'par未设置next_url')
        _num += 1
        time.sleep(0.2)
        if _num >20:
            Tool.print(f'页数超过20,当前{_num},检查是否异常',color='yellow')
    return ls


def main():

    data = Tool.File.load_json(catch_path)

    catch_data = Tool.File.load_json(catch_path)
    index_data = Tool.File.load_json(index_path)

    urls_data = Tool.File.load_json(file_path)

    result = data

    num = 0
    for name, url in urls_data.items():
        if not flush:
            if name in data and data.get(name, False):
                Tool.print(f"跳过分类：{name}，因为该分类已存在数据",color='yellow')
                continue
        if url in input_url_no_ls:
            Tool.print(f'跳过分类：{name}，目标url排除',color='yellow')
            continue
        print(f"\n====== 正在处理分类：{name} ======")
        print(f"目标集合: {url.strip()}")

        result[name] = []

        if isinstance(ts_num, int) and num >= ts_num:
            print(f"已处理 {num} 条数据，已超出限制，任务结束")
            break
        num += 1

        try:
            print(f"正在分析 URL: {url}")
            detail_urls = get_detail_all_url(url)
            if detail_urls:
                detail_urls = [i for i in detail_urls if i not in output_url_no_ls]
                before_count = len(result[name])
                result[name].extend(detail_urls)
                result[name] = list(dict.fromkeys(result[name]))
                after_count = len(result[name])
                dup_count = before_count + len(detail_urls) - after_count
                if dup_count > 0:
                    print(f"  [去重] 分类 [{name}] 本次移除了 {dup_count} 条重复URL")
                print(f"  成功获取到 {len(detail_urls)} 条详情页链接")
            else:
                print(f"  get_detail_all_url返回空值，URL: {url} 未获取到数据 (可能是 API 结构不同)")
        except Exception as e:
            print(f"  URL: {url} 处理中途中断: {e}")

        Tool.File.save_json(result, catch_path)

    Tool.File.save_json(result, save_path)
    Tool.File.save_json(result, catch_path)

    total_count = sum(len(v) for v in result.values())
    print(f"\n任务结束！总共抓取到 {total_count} 条详情页链接，已保存到 {save_path}")


class Sc(object):
    def __init__(self):
        self.catch_data = Tool.File.load_json(catch_path)
        self.input_data = Tool.File.load_json(file_path)
        self.index_data = Tool.File.load_json(index_path)
        self.total_category = len(self.input_data)

    def get_index_id(self, url, params: dict) -> str:
        raw = json.dumps(
            {"url": url, "params": params},
            sort_keys=True,
            ensure_ascii=False
        ).encode("utf-8")
        return hashlib.md5(raw).hexdigest()

    def get_all_detail_url(self, url, name, category_idx):
        """单个分类分页循环入口"""
        _num = 0
        par = {'_raw_url': url, 'page': _num}
        current_page_url = url
        while True:
            # 打印当前分类内分页进度
            Tool.print(
                f"【分类 {category_idx}/{self.total_category} | {name}】正在处理第 {_num + 1} 页: {current_page_url}")
            index_id, is_next = self.get_detail_url(current_page_url, par=par)

            id_list = self.catch_data.setdefault(name, [])
            if index_id not in id_list:
                id_list.append(index_id)
            else:
                Tool.print(f'分类:{name}，分页索引已存在，跳过', color='green')

            if not is_next:
                break

            try:
                current_page_url = par['next_url']
            except KeyError:
                Tool.print(f'par未设置next_url，终止当前分类翻页', color="yellow")
                break

            _num += 1
            par['page'] += 1
            if _num > 30:
                Tool.print(f'页数超过20,当前{_num},仅警告继续运行', color='yellow')

            if _num % 30 == 0:
                self.save_res()

        self.save_res()

    def get_detail_url(self, url, par: dict):
        """
        模板方法，预留占位：
        下游在这里实现：
            1. 请求网页
            2. xpath提取product_urls
            3. xpath提取next_link，赋值 par['next_url']
        """
        is_next = False
        par['next_url'] = None
        raw_url = par['_raw_url']
        gro_id = url.split('-')[-1]
        params = {
            'catalogId': '1004',
            'count': '36',
            'from': par.get('page') * 36,
            'sort': 'byRelevance',
            'groupId': gro_id,
        }

        index_id = self.get_index_id(raw_url, params=params)
        _catch = self.index_data.get(raw_url, {}).get(index_id)

        # flush=True 强制忽略缓存，重新请求
        if not flush and _catch:
            par['next_url'] = _catch.get('next_url')
            if par['next_url']:
                return index_id, True

        # ========== 【下游业务实现区域 START】==========
        for i in range(3):
            try:
                ls = []
                response = Tool.get('https://www.chewy.com/plp/api/search',params=params,headers=headers,cookies=cookies)
                data = response.json()['products']
                for df in data:
                    _url = df['href']
                    ls.append(_url)
                    print(_url)
                    # 链接黑名单过滤


                product_urls = [u for u in ls if u not in output_url_no_ls]

                if not product_urls:
                    Tool.print(f'{url}:第{par['page']}页未获取到数据 (可能是 API 结构不同)', color='yellow')
                    return index_id, False

                par['next_url'] = url
                # ========== 【下游业务实现区域 END】 ==========

                self.index_data.setdefault(raw_url, {})[index_id] = {
                    'data': product_urls,
                    'next_url': par['next_url']
                }
                is_next = True
                return index_id, is_next

            except Exception as e:
                Tool.print(f'请求失败:{e}')
                pass


        return index_id,False



    def save_res(self,catch=True):
        if catch:
            Tool.File.save_json(self.index_data,index_path)
            Tool.File.save_json(self.catch_data,catch_path)
            return

        res_dic = {}
        for name, index_ls in self.catch_data.items():
            ls = []
            base_raw_key = self.input_data[name]
            for index in index_ls:
                cache_item = self.index_data.get(base_raw_key, {}).get(index, {})
                page_url_list = cache_item.get("data", [])
                ls.extend(page_url_list)
            res_dic[name] = list(dict.fromkeys(ls))

        Tool.File.save_json(res_dic, save_path)

        return res_dic


    def run(self):
        category_idx = 0
        for name, url in self.input_data.items():
            category_idx += 1
            if url in input_url_no_ls:
                Tool.print(f'【{category_idx}/{self.total_category}】跳过分类：{name}，目标url排除', color='yellow')
                continue

            print(f"\n====== 【{category_idx}/{self.total_category}】正在处理分类：{name} ======")
            print(f"分类首页URL: {url.strip()}")

            if isinstance(ts_num, int) and (category_idx - 1) >= ts_num:
                print(f"已达到测试条数限制 {ts_num}，任务结束")
                break

            self.get_all_detail_url(url, name, category_idx)

        Tool.print("\n所有分类抓取完成，开始汇总输出最终详情链接……", color='green')
        res_dic = self.save_res(catch=False)
        total = sum(len(v) for v in res_dic.values())
        Tool.print(f"\n✅ 任务全部完成！汇总详情URL总数：{total}，结果保存至 {save_path}", color='green')


if __name__ == '__main__':
    Sc().run()