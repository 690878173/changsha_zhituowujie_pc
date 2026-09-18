from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')
cookies = {
    '__apex_test__': '',
    '__apex_test__': '',
    'dwac_505af6cc998cc5f9f827821855': 'edlBIFDWjGPOcg9XsM8_3Wk_X6Rh50pANLw%3D|dw-only|||USD|false|US%2FPacific|true',
    'cqcid': 'abVj6lxZLAIIeMuMmYX4AupE66',
    'cquid': '||',
    'dwanonymous_adb6f0c0bea1959b44ade4a112139272': 'abVj6lxZLAIIeMuMmYX4AupE66',
    'sid': 'edlBIFDWjGPOcg9XsM8_3Wk_X6Rh50pANLw',
    'dwsid': 'TUSlS7q70NXU6R_bVqECQl2iu8-Lihb2Licw0Z0i2garABVWc1eKVpjebLBrBc9jGbOIMzRrgM6u--BpN91jdQ==',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    'osano_consentmanager_uuid': 'e7a32569-6385-42ff-9cf7-1db238e0452d',
    'osano_consentmanager': 'KgmRt9QJJhI3LEFdcokYh3o-gfsobvE5T4wfld-JvIS63aU5YmtNG8cjhLfiQtpM-xs8JiTiEriN-KU29WgreitZzeKuD19X08zzeEQJOHZfssmusSjd-o4UBmX7xkQVxKMde_PGyM6zw1jnTNaIIvAJWNQ0_cBs0lkBRnSFPbDhOSXMCEplumFLmTxKbppgQDQ6eFZJ4vxbMLCZYQrDyKslPhk-oOA-ozT07wnxKV6sMGVLSDnSbDmxI82cOIOH_giz-7MZR18hRuUy7NygMMOEbhmhCGH3-sBGBu_-xFYlvdECA3Bwbs5tOY0sPTlDO7YqgNAR6uo=',
    '__apex_test__': '',
    'locale_pref': 'en_US',
    '__attn_eat_id': '4e8a3969778646918dd8615afbfcabd5',
    '__attentive_id': '237f6bc864214bf28f213b809092a977',
    '__attentive_session_id': '35ce2ff326ee4af9a8bea129373a9df2',
    '__attentive_cco': '1786763462598',
    '_attn_bopd_': 'browser',
    '__attentive_dv': '1',
    '__attentive_ss_referrer': 'https://www.hoka.com/',
    'pixlee_analytics_cookie': '%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2237c5ae71-19f0-1f76-8a45-646edc14eecf%22%7D',
    'pixlee_analytics_cookie_legacy': '%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2237c5ae71-19f0-1f76-8a45-646edc14eecf%22%7D',
    'yotpo_pixel': '3897cbee-3ac8-4815-9ef2-08c59dd7ee10',
    '_sp_ses.1f99': '*',
    'tfExperimentId': 't-9519872adb1046528acf84034a2c0ea6',
    'tf-version': 'v1',
    'visitCount': '6',
    '_attn_': 'eyJ1Ijoie1wiY29cIjoxNzg2NzYzNDYyNTkxLFwidW9cIjoxNzg2NzYzNDYyNTkxLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjIzN2Y2YmM4NjQyMTRiZjI4ZjIxM2I4MDkwOTJhOTc3XCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg2NzYzNDk3OTc0LFwidW9cIjoxNzg2NzYzNDk3OTc0LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL25iaWF2Lmhva2EuY29tXCJ9In0=',
    '_sp_id.1f99': 'fbec3ac5cf8faf9d.1786763475.1.1786763498.1786763475',
    '__attentive_pv': '5',
    'forterToken': 'b453ed77463b42848e4c1ff207f2ca2a_1786763496777__UDF43-m4_23ck_',
    'datadome': 'IEAsnmHgQvMCPvElY4k_G9cgG_Pg6LJ6Fg_8yZOFuN72fn2FnOv7aSxJEHf0ymwlalCsOrZdQJn1vI1bDZldfp1YG09EKBMcY2M2F3zuPoM6JVRty3WzizDKTuOudEOw',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.hoka.com/en/us/new-arrivals/',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    # 'cookie': '__apex_test__=; __apex_test__=; dwac_505af6cc998cc5f9f827821855=edlBIFDWjGPOcg9XsM8_3Wk_X6Rh50pANLw%3D|dw-only|||USD|false|US%2FPacific|true; cqcid=abVj6lxZLAIIeMuMmYX4AupE66; cquid=||; dwanonymous_adb6f0c0bea1959b44ade4a112139272=abVj6lxZLAIIeMuMmYX4AupE66; sid=edlBIFDWjGPOcg9XsM8_3Wk_X6Rh50pANLw; dwsid=TUSlS7q70NXU6R_bVqECQl2iu8-Lihb2Licw0Z0i2garABVWc1eKVpjebLBrBc9jGbOIMzRrgM6u--BpN91jdQ==; __cq_dnt=0; dw_dnt=0; osano_consentmanager_uuid=e7a32569-6385-42ff-9cf7-1db238e0452d; osano_consentmanager=KgmRt9QJJhI3LEFdcokYh3o-gfsobvE5T4wfld-JvIS63aU5YmtNG8cjhLfiQtpM-xs8JiTiEriN-KU29WgreitZzeKuD19X08zzeEQJOHZfssmusSjd-o4UBmX7xkQVxKMde_PGyM6zw1jnTNaIIvAJWNQ0_cBs0lkBRnSFPbDhOSXMCEplumFLmTxKbppgQDQ6eFZJ4vxbMLCZYQrDyKslPhk-oOA-ozT07wnxKV6sMGVLSDnSbDmxI82cOIOH_giz-7MZR18hRuUy7NygMMOEbhmhCGH3-sBGBu_-xFYlvdECA3Bwbs5tOY0sPTlDO7YqgNAR6uo=; __apex_test__=; locale_pref=en_US; __attn_eat_id=4e8a3969778646918dd8615afbfcabd5; __attentive_id=237f6bc864214bf28f213b809092a977; __attentive_session_id=35ce2ff326ee4af9a8bea129373a9df2; __attentive_cco=1786763462598; _attn_bopd_=browser; __attentive_dv=1; __attentive_ss_referrer=https://www.hoka.com/; pixlee_analytics_cookie=%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2237c5ae71-19f0-1f76-8a45-646edc14eecf%22%7D; pixlee_analytics_cookie_legacy=%7B%22CURRENT_PIXLEE_USER_ID%22%3A%2237c5ae71-19f0-1f76-8a45-646edc14eecf%22%7D; yotpo_pixel=3897cbee-3ac8-4815-9ef2-08c59dd7ee10; _sp_ses.1f99=*; tfExperimentId=t-9519872adb1046528acf84034a2c0ea6; tf-version=v1; visitCount=6; _attn_=eyJ1Ijoie1wiY29cIjoxNzg2NzYzNDYyNTkxLFwidW9cIjoxNzg2NzYzNDYyNTkxLFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcIjIzN2Y2YmM4NjQyMTRiZjI4ZjIxM2I4MDkwOTJhOTc3XCJ9IiwiZWF0Ijoie1wiY29cIjoxNzg2NzYzNDk3OTc0LFwidW9cIjoxNzg2NzYzNDk3OTc0LFwibWFcIjozNjUwLFwiaW5cIjp0cnVlLFwidmFsXCI6XCJodHRwczovL25iaWF2Lmhva2EuY29tXCJ9In0=; _sp_id.1f99=fbec3ac5cf8faf9d.1786763475.1.1786763498.1786763475; __attentive_pv=5; forterToken=b453ed77463b42848e4c1ff207f2ca2a_1786763496777__UDF43-m4_23ck_; datadome=IEAsnmHgQvMCPvElY4k_G9cgG_Pg6LJ6Fg_8yZOFuN72fn2FnOv7aSxJEHf0ymwlalCsOrZdQJn1vI1bDZldfp1YG09EKBMcY2M2F3zuPoM6JVRty3WzizDKTuOudEOw',
}


no_url_ls = ['https://www.hoka.com/en/us/hoka-shoe-finder.html',
             'https://www.hoka.com/en/us/just-for-you/']

@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url,headers=headers,cookies=cookies)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//ul[@class="nav navbar-nav navbar-category-links"]/li')
    header_node = ml1

    no_name = ['shoe-finder','resources']

    for node in header_node:


        _name = node.get('data-nav-section')
        _name = _name.strip()
        if _name in no_name:
            continue

        a_node = node.xpath('./a')[0]

        _url = a_node.get('href')
        _url = Tool.URL.add_site(_url)

        childs = []

        c_node = node.xpath('./ul/li')
        if c_node:
            childs = c_node

        url_dic[_name] = {'url':_url,'child':{}}



        f2(url_dic[_name]['child'], childs,_url)
    print(url_dic)
    return url_dic

def f2(dic, childs,url):
    for child in childs:
        c_node = child.xpath('./ul/li')

        _name = child.xpath('./span/span//text()')
        _name = ''.join(_name).strip()
        _url = url
        if not _name:
            a_node = child.xpath('./a')
            if not a_node:
                continue
            a_node = a_node[0]
            _url = a_node.get('href')
            _name = child.xpath('./a/span/text()')
            _name = ''.join(_name).strip()

        _url = Tool.URL.add_site(_url)

        if _url in no_url_ls:
            continue
        dic[_name] = {'url': _url, 'child': {}}

        n_childs_ls = c_node
        f3(dic[_name]['child'],n_childs_ls)

    return dic


def f3(dic,childs):
    for child in childs:
        c_a = child.xpath('./a')

        c_tx, c_url = Tool.HTML.get_a_text_and_url(c_a[0])
        _name = c_tx
        _url = c_url
        _url = Tool.URL.add_site(_url)
        if _url in no_url_ls:
            continue

        dic[_name] = {'url': _url, 'child': {}}


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



