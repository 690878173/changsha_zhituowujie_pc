from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')
cookies = {
    'deckersSID': 'e5c6e6fe-459b-4e7b-a59a-031f787a732e',
    'deckersUserID': '49304fa3-eeaf-4349-888b-3c5886b2238c',
    'csrfToken': 'f7cd3d18a94c34cd0479cf689dfcb5a1caf66d39dc3ff7713bbcda94ea3d2e12',
    '_dyid_server': '6115888553455153550',
    '_dyjsession': 'odk8ucrsremjachkqepi9zdwr3pmjhzf',
    'auth_access_token': 'eyJ2ZXIiOiIxLjAiLCJqa3UiOiJzbGFzL3Byb2QvYmRqZF9wcmQiLCJraWQiOiJjMjRkNmVhZS0xYjhkLTQxZjctYjgyOC1kMGFhMmMxOTk2NzAiLCJ0eXAiOiJqd3QiLCJjbHYiOiJKMi4zLjQiLCJhbGciOiJFUzI1NiJ9.eyJhdXQiOiJHVUlEIiwic2NwIjoic2ZjYy5zaG9wcGVyLW15YWNjb3VudC5iYXNrZXRzIHNmY2Muc2hvcHBlci1wcm9kdWN0cyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnJ3IHNmY2Muc2hvcHBlci1jdXN0b21lcnMubG9naW4gc2ZjYy5zaG9wcGVyLWNvbnRleHQucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5vcmRlcnMgc2ZjYy5zaG9wcGVyLWN1c3RvbWVycy5yZWdpc3RlciBzZmNjLnNob3BwZXItbXlhY2NvdW50LmFkZHJlc3Nlcy5ydyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnByb2R1Y3RsaXN0cy5ydyBzZmNjLnNob3BwZXItcHJvbW90aW9ucyBzZmNjLnNob3BwZXItY3VzdG9tLW9iamVjdHMuc3VwZXJHcm91cCBjX2Z1bGxQcm9kdWN0X3Igc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wYXltZW50aW5zdHJ1bWVudHMucncgc2ZjYy5zaG9wcGVyLXByb2R1Y3Qtc2VhcmNoIGNfc2hpcHBpbmdNZXRob2RzX3Igc2ZjYy5zaG9wcGVyLXNlbyBzZmNjLnNob3BwZXItY2F0ZWdvcmllcyIsInN1YiI6ImNjLXNsYXM6OmJkamRfcHJkOjpzY2lkOjg4YzQzYTQ1LWFjMTMtNDUxZC05Y2ZlLTU0MDZlMmIzZGE0YTo6dXNpZDo0OTMwNGZhMy1lZWFmLTQzNDktODg4Yi0zYzU4ODZiMjIzOGMiLCJjdHgiOiJzbGFzIiwiaXNzIjoic2xhcy9wcm9kL2JkamRfcHJkIiwiaXN0IjoxLCJkbnQiOiIwIiwiYXVkIjoiY29tbWVyY2VjbG91ZC9wcm9kL2JkamRfcHJkIiwibmJmIjoxNzg3OTgyMTkyLCJzdHkiOiJVc2VyIiwiaXNiIjoidWlkbzpzbGFzOjp1cG46R3Vlc3Q6OnVpZG46R3Vlc3QgVXNlcjo6Z2NpZDphYmxiSVhrYnBLd3JrUnh1dEZ4R1lZa1hvMzo6Y2hpZDpURVZBLVVTIiwiZXhwIjoxNzg3OTg0MDIyLCJpYXQiOjE3ODc5ODIyMjIsImp0aSI6IkMyQy05NjgxODMzNDEwOTUwNDg0ODY2MzAyOTE2MTkzOTkwNDU5NzkifQ.bUwaFwsI1DwgfvM_aOUy7G-f9ZFd1MF-zk-BIMclgN1dCZ-Leu4zqeap4bjWjIQDlHgbB0DovPvPPC67lyNogw',
    'auth_refresh_token': 'F-vq7sickAAk9iwozpK2yUS2zN-Wu5D9ELdWo-GNKPU',
    'auth_expires_in': '1800',
    'auth_issued_at': '1787982222',
    'auth_refresh_at': '1787983122',
    'auth_guest_id': 'ablbIXkbpKwrkRxutFxGYYkXo3',
    'builderSessionId': '462fb9c323cd4503bbafc6a67af10a3b',
    'deckersSessionCartID': 'dsl3fbxyvtui50aqcapztb33',
    'kampyle_userid': 'a950-1a5e-5469-8236-2fcd-2b37-b25d-5bda',
    '_dd_s': 'aid=8f6dec8c-540c-425d-9669-780b5ab74951&rum=0&expire=1787983152019',
    'kampyleUserSession': '1787982252494',
    'kampyleUserSessionsCount': '2',
    'kampyleUserPercentile': '84.70177785169064',
    'kampyleSessionPageCounter': '1',
    'forterToken': 'b412b5500f814c05b920f01f871c34ce_1787982252049__UDF43-m4_17ck_',
    'deckers-forter-token': 'b412b5500f814c05b920f01f871c34ce_1787982252049__UDF43-m4_17ck__tt',
    '__attn_eat_id': '0127d98cf2b649ef9c118f56efe75e0f',
    'datadome': 'fMY40J3bHCv65El2YSbLA9fbn6OrYrJMmflq_HxjNlqjX7yNMnaeNfHEWIeNjfw80V9mC3JjI3bo_VDEcFDvF7ReEwbB~zOCo1Ru4x~F8TiAjK3SLQgJvsZvogkrYFi~',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.teva.com/',
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Microsoft Edge";v="152"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0',
    # 'cookie': 'deckersSID=e5c6e6fe-459b-4e7b-a59a-031f787a732e; deckersUserID=49304fa3-eeaf-4349-888b-3c5886b2238c; csrfToken=f7cd3d18a94c34cd0479cf689dfcb5a1caf66d39dc3ff7713bbcda94ea3d2e12; _dyid_server=6115888553455153550; _dyjsession=odk8ucrsremjachkqepi9zdwr3pmjhzf; auth_access_token=eyJ2ZXIiOiIxLjAiLCJqa3UiOiJzbGFzL3Byb2QvYmRqZF9wcmQiLCJraWQiOiJjMjRkNmVhZS0xYjhkLTQxZjctYjgyOC1kMGFhMmMxOTk2NzAiLCJ0eXAiOiJqd3QiLCJjbHYiOiJKMi4zLjQiLCJhbGciOiJFUzI1NiJ9.eyJhdXQiOiJHVUlEIiwic2NwIjoic2ZjYy5zaG9wcGVyLW15YWNjb3VudC5iYXNrZXRzIHNmY2Muc2hvcHBlci1wcm9kdWN0cyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnJ3IHNmY2Muc2hvcHBlci1jdXN0b21lcnMubG9naW4gc2ZjYy5zaG9wcGVyLWNvbnRleHQucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5vcmRlcnMgc2ZjYy5zaG9wcGVyLWN1c3RvbWVycy5yZWdpc3RlciBzZmNjLnNob3BwZXItbXlhY2NvdW50LmFkZHJlc3Nlcy5ydyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnByb2R1Y3RsaXN0cy5ydyBzZmNjLnNob3BwZXItcHJvbW90aW9ucyBzZmNjLnNob3BwZXItY3VzdG9tLW9iamVjdHMuc3VwZXJHcm91cCBjX2Z1bGxQcm9kdWN0X3Igc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wYXltZW50aW5zdHJ1bWVudHMucncgc2ZjYy5zaG9wcGVyLXByb2R1Y3Qtc2VhcmNoIGNfc2hpcHBpbmdNZXRob2RzX3Igc2ZjYy5zaG9wcGVyLXNlbyBzZmNjLnNob3BwZXItY2F0ZWdvcmllcyIsInN1YiI6ImNjLXNsYXM6OmJkamRfcHJkOjpzY2lkOjg4YzQzYTQ1LWFjMTMtNDUxZC05Y2ZlLTU0MDZlMmIzZGE0YTo6dXNpZDo0OTMwNGZhMy1lZWFmLTQzNDktODg4Yi0zYzU4ODZiMjIzOGMiLCJjdHgiOiJzbGFzIiwiaXNzIjoic2xhcy9wcm9kL2JkamRfcHJkIiwiaXN0IjoxLCJkbnQiOiIwIiwiYXVkIjoiY29tbWVyY2VjbG91ZC9wcm9kL2JkamRfcHJkIiwibmJmIjoxNzg3OTgyMTkyLCJzdHkiOiJVc2VyIiwiaXNiIjoidWlkbzpzbGFzOjp1cG46R3Vlc3Q6OnVpZG46R3Vlc3QgVXNlcjo6Z2NpZDphYmxiSVhrYnBLd3JrUnh1dEZ4R1lZa1hvMzo6Y2hpZDpURVZBLVVTIiwiZXhwIjoxNzg3OTg0MDIyLCJpYXQiOjE3ODc5ODIyMjIsImp0aSI6IkMyQy05NjgxODMzNDEwOTUwNDg0ODY2MzAyOTE2MTkzOTkwNDU5NzkifQ.bUwaFwsI1DwgfvM_aOUy7G-f9ZFd1MF-zk-BIMclgN1dCZ-Leu4zqeap4bjWjIQDlHgbB0DovPvPPC67lyNogw; auth_refresh_token=F-vq7sickAAk9iwozpK2yUS2zN-Wu5D9ELdWo-GNKPU; auth_expires_in=1800; auth_issued_at=1787982222; auth_refresh_at=1787983122; auth_guest_id=ablbIXkbpKwrkRxutFxGYYkXo3; builderSessionId=462fb9c323cd4503bbafc6a67af10a3b; deckersSessionCartID=dsl3fbxyvtui50aqcapztb33; kampyle_userid=a950-1a5e-5469-8236-2fcd-2b37-b25d-5bda; _dd_s=aid=8f6dec8c-540c-425d-9669-780b5ab74951&rum=0&expire=1787983152019; kampyleUserSession=1787982252494; kampyleUserSessionsCount=2; kampyleUserPercentile=84.70177785169064; kampyleSessionPageCounter=1; forterToken=b412b5500f814c05b920f01f871c34ce_1787982252049__UDF43-m4_17ck_; deckers-forter-token=b412b5500f814c05b920f01f871c34ce_1787982252049__UDF43-m4_17ck__tt; __attn_eat_id=0127d98cf2b649ef9c118f56efe75e0f; datadome=fMY40J3bHCv65El2YSbLA9fbn6OrYrJMmflq_HxjNlqjX7yNMnaeNfHEWIeNjfw80V9mC3JjI3bo_VDEcFDvF7ReEwbB~zOCo1Ru4x~F8TiAjK3SLQgJvsZvogkrYFi~',
}

@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.get(url,headers=headers,cookies=cookies)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    ml1 = html.xpath('//header/ul[@role="menu"]/div/li')
    header_node = ml1


    for node in header_node:

        c_node = node.xpath('./a')
        _name,_url = Tool.HTML.get_a_text_and_url(c_node[0])
        _url = Tool.URL.add_site(_url)

        if 'Inside Teva' in _name:
            continue

        url_dic[_name] = {'url':_url,'child':{}}

        childs = node.xpath('./ul/li/div')

        f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:
        c_node = child.xpath('./a')

        _name,_url = Tool.HTML.get_a_text_and_url(c_node[0])

        _url = Tool.URL.add_site(_url)
        dic[_name] = {'url': _url, 'child': {}}

        n_childs_ls = child.xpath('./ul/li')
        f3(dic[_name]['child'],n_childs_ls)

    return dic


def f3(dic,childs):
    for child in childs:
        c_a = child.xpath('./a')

        c_tx, c_url = Tool.HTML.get_a_text_and_url(c_a[0])
        _name = c_tx
        _url = c_url
        _url = Tool.URL.add_site(_url)
        if '/p/' in _url:
            continue

        dic[_name] = {'url': _url, 'child': {}}


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



