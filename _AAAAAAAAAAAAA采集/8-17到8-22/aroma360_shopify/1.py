from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')
cookies = {
    '__cf_bm': 'pMmDhKfLk2FhwIFyv9_mNuW5fRvTHppP65yNOJNezz0-1787102691.4471073-1.0.1.1-6MySa6OIJNlV15wCpX798o7MvVYNit.q4l2nYOlT0gzpPxvHK96qkbcAAZ_Pj0PUj7T7T_JHwlgKrYNaBZSXhHBgit278e6.51DeBrl4LMyXMyGpdLX1jxAZw1SqzffV',
    'localization': 'US',
    'cart_currency': 'USD',
    'ede-s': 'a73235c8-e7c8-4301-8d71-105e76057fdd',
    'ede-i': 'babf8a35-3f05-4bb6-ac2a-ee82b8f79056',
    'ede-expid': 'd3c0a12b-502e-4448-977c-dc1d4d028809',
    'ede-expvar': 'Edge Delivery Enabled',
    'og_session_id': '0e1238e24e6d11ee8ec0320baddbf188.156430.1787102859',
    'current-store': 'Aroma',
    'landing_url': 'https://aroma360.com/',
    '_ga': 'GA1.1.2040956108.1787102862',
    'tag_user_id': 'f2501f97-644e-4023-ae53-c926f32c9bba-1787102861854',
    'tag_session': '0de1438d-f236-4adb-b43a-7be3d243b179-9c8c45b4-0b72-476d-8f4d-b93381c856bf-1787102863232',
    'cart': 'hWNFokR28h4n7Z0zqVTc4PkW%3Fkey%3Dff572acb10b5856d46787cbf2ed58cf1',
    'tatari-cookie-test': '22531231',
    'tatari-session-cookie': '9db79f3b-f06e-090b-1125-fab4fe24ba06',
    '_pin_unauth': 'dWlkPU16YzNNVEk0WkdJdE5tVXhNUzAwTkRVNExUa3pZbVF0WVRNM1lURXdaR00yTldRdw',
    'alia-jwt': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsYXN0VXNlcklEIjo2OTY0MjI4MDM3LCJpYXQiOjE3ODcxMDI4NjN9.KzZdH0vZUn2R-xUNH4_TPUWulBNbKm2bAm7x9dfiLNQ',
    'safe-ship-in-cart': 'no',
    'mystery-item-in-cart': 'no',
    '__uidcei': '4315df29-5cd5-4693-913d-c3a91e97af9e',
    'osid': '4315df29-5cd5-4693-913d-c3a91e97af9e',
    'cookieconsent_preferences_disabled': '',
    '_shopify_y': '384b4cab-fa51-4936-b6cd-c0b70b5233aa',
    '_shopify_analytics': ':AaAXoaigAAEANaE-c_XfchRL7S1zd28wWMnIgAqfgH5_eoIWDgpRiq4PXxLKfihaAVKK7bezdycGv21i9n3R8B1K_PfwfS5hy70vzaMIc3qEKwZqsD8BAx0PIP3r8AxlTD0rLUoBRFJQTvxx:',
    '_shopify_marketing': ':AaAXoailAAEAEyvJBQtbr0DmGdf3islMbgGGGsI0_M3xLuXdq6LiHZ2yAiWlCCHq2Jy2q8XlhyHhJcrnLYkWXV0u2EcU0HTG4lUw0Ut48LJerk79IQo3HLNr5pvQLQU1XsxH:',
    '_rsession': 'ecfdbf1647f88937',
    '_ruid': 'eyJ1dWlkIjoiMTkwZmFlZTgtMmFlZC00ODFlLWI0OWQtYjYxZmY1NjUyYTIzIn0%3D',
    '__kla_id': 'eyJjaWQiOiJaamsxWldJek16QXROVFl5TmkwMFpUWTBMV0V6TldZdFpESTFZVEl3TTJWaFpHVmsifQ==',
    '_shopify_s': '81c3d01e-50f9-4247-9f7d-635f28bd9884',
    'repSid': '31393035-96a6-4331-a220-58b700bf6222',
    '_shopify_client_id': '384b4cab-fa51-4936-b6cd-c0b70b5233aa',
    'shopify_client_id': '384b4cab-fa51-4936-b6cd-c0b70b5233aa',
    'wm_cv': '1.0.7',
    'vyg-session-id': '55d2f25d-2dd1-d01c-921e-c906062cb182',
    'wm_frt': '2026-08-19T01:27:49.652Z',
    'growi_visitor_uid': '999ef0d7-fcd5-49bd-9aec-fed1bb807965',
    'ca_session': 'bv21BbEzzctAuJwEkqmOz',
    '_gcl_au': '1.1.780996198.1787102862',
    '_ga_BK76DMBHKH': 'GS2.1.s1787102861$o1$g1$t1787102874$j47$l0$h805616119',
    'ede-r': 'https://aroma360.com/',
    'discount_code': 'EXTRA20',
    'ede-c': 'stash-hit',
    'ede-p': '/products/free-diffuser',
    '_shopify_essential': ':AaAXoZDaAAEAYpBdogeru-4K9nvtiDgsrIz77bh2Iq2FXqsjNQow-BC2Y35dAF5gsTcabRXjTrM5pvQXIfpMPXuetZFP5dmphtNqWQ71Y3UuL-ZMIxCsdHl-Njb-j1jUaHBsM9PiWydx2edWdzB58dTW0I5gboBOTZTIHQ9s0_DL060SHpgIcMZvO73zR3EAw1NwodHTfkn0emxKUgdst_HvJO9H1ho7P5uBXQ3AlnQbv6Ucdi6csWUb-WKxlc7KkIkyluZwLjnCK38U5q03AUDK1lxYWezg1RCcs4fjM47S-bJy1J9P-F2EYr20xfSxbhR6VzyCaTnBHuoJN5iysA_CY4vu6omRDZqOs5J7nXGMTquILljFNHrSLFhNx-tqNrSR2yIbCvC4hnns04-EEOXGptze6GVDdPHu8ehmS2aRYxelhf6gZH4FaoehsbbDiINMRUJPmlIPrxKbP9tSBEMCc6HqrLX5a9n5-CKhk4ZBqcjph3pNgPDR67vjzBDaDZPW9SmHhsU_Q0I98Ef_t6Rd-jBj2twH_u45xlIs5l7zso7v25Bf7RyTj3NQA8BalfIzSBsDEbZRktfsTGcJR2zXmB45BAp5oujNNCo502WzZNP_j40PVCzXCi2T9IidJEMeWod5mmVEGbp1j0nyFX2z7l7CyEBI4PTxGnhT9qxxBhhZL8WMZr0b4y0PGnzn4l7KGyHtZiotKfDqhIGIBp0Md6kc_VgGo0cJ-InGaGT1B91E9Q:',
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
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    # 'cookie': '__cf_bm=pMmDhKfLk2FhwIFyv9_mNuW5fRvTHppP65yNOJNezz0-1787102691.4471073-1.0.1.1-6MySa6OIJNlV15wCpX798o7MvVYNit.q4l2nYOlT0gzpPxvHK96qkbcAAZ_Pj0PUj7T7T_JHwlgKrYNaBZSXhHBgit278e6.51DeBrl4LMyXMyGpdLX1jxAZw1SqzffV; localization=US; cart_currency=USD; ede-s=a73235c8-e7c8-4301-8d71-105e76057fdd; ede-i=babf8a35-3f05-4bb6-ac2a-ee82b8f79056; ede-expid=d3c0a12b-502e-4448-977c-dc1d4d028809; ede-expvar=Edge Delivery Enabled; og_session_id=0e1238e24e6d11ee8ec0320baddbf188.156430.1787102859; current-store=Aroma; landing_url=https://aroma360.com/; _ga=GA1.1.2040956108.1787102862; tag_user_id=f2501f97-644e-4023-ae53-c926f32c9bba-1787102861854; tag_session=0de1438d-f236-4adb-b43a-7be3d243b179-9c8c45b4-0b72-476d-8f4d-b93381c856bf-1787102863232; cart=hWNFokR28h4n7Z0zqVTc4PkW%3Fkey%3Dff572acb10b5856d46787cbf2ed58cf1; tatari-cookie-test=22531231; tatari-session-cookie=9db79f3b-f06e-090b-1125-fab4fe24ba06; _pin_unauth=dWlkPU16YzNNVEk0WkdJdE5tVXhNUzAwTkRVNExUa3pZbVF0WVRNM1lURXdaR00yTldRdw; alia-jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsYXN0VXNlcklEIjo2OTY0MjI4MDM3LCJpYXQiOjE3ODcxMDI4NjN9.KzZdH0vZUn2R-xUNH4_TPUWulBNbKm2bAm7x9dfiLNQ; safe-ship-in-cart=no; mystery-item-in-cart=no; __uidcei=4315df29-5cd5-4693-913d-c3a91e97af9e; osid=4315df29-5cd5-4693-913d-c3a91e97af9e; cookieconsent_preferences_disabled=; _shopify_y=384b4cab-fa51-4936-b6cd-c0b70b5233aa; _shopify_analytics=:AaAXoaigAAEANaE-c_XfchRL7S1zd28wWMnIgAqfgH5_eoIWDgpRiq4PXxLKfihaAVKK7bezdycGv21i9n3R8B1K_PfwfS5hy70vzaMIc3qEKwZqsD8BAx0PIP3r8AxlTD0rLUoBRFJQTvxx:; _shopify_marketing=:AaAXoailAAEAEyvJBQtbr0DmGdf3islMbgGGGsI0_M3xLuXdq6LiHZ2yAiWlCCHq2Jy2q8XlhyHhJcrnLYkWXV0u2EcU0HTG4lUw0Ut48LJerk79IQo3HLNr5pvQLQU1XsxH:; _rsession=ecfdbf1647f88937; _ruid=eyJ1dWlkIjoiMTkwZmFlZTgtMmFlZC00ODFlLWI0OWQtYjYxZmY1NjUyYTIzIn0%3D; __kla_id=eyJjaWQiOiJaamsxWldJek16QXROVFl5TmkwMFpUWTBMV0V6TldZdFpESTFZVEl3TTJWaFpHVmsifQ==; _shopify_s=81c3d01e-50f9-4247-9f7d-635f28bd9884; repSid=31393035-96a6-4331-a220-58b700bf6222; _shopify_client_id=384b4cab-fa51-4936-b6cd-c0b70b5233aa; shopify_client_id=384b4cab-fa51-4936-b6cd-c0b70b5233aa; wm_cv=1.0.7; vyg-session-id=55d2f25d-2dd1-d01c-921e-c906062cb182; wm_frt=2026-08-19T01:27:49.652Z; growi_visitor_uid=999ef0d7-fcd5-49bd-9aec-fed1bb807965; ca_session=bv21BbEzzctAuJwEkqmOz; _gcl_au=1.1.780996198.1787102862; _ga_BK76DMBHKH=GS2.1.s1787102861$o1$g1$t1787102874$j47$l0$h805616119; ede-r=https://aroma360.com/; discount_code=EXTRA20; ede-c=stash-hit; ede-p=/products/free-diffuser; _shopify_essential=:AaAXoZDaAAEAYpBdogeru-4K9nvtiDgsrIz77bh2Iq2FXqsjNQow-BC2Y35dAF5gsTcabRXjTrM5pvQXIfpMPXuetZFP5dmphtNqWQ71Y3UuL-ZMIxCsdHl-Njb-j1jUaHBsM9PiWydx2edWdzB58dTW0I5gboBOTZTIHQ9s0_DL060SHpgIcMZvO73zR3EAw1NwodHTfkn0emxKUgdst_HvJO9H1ho7P5uBXQ3AlnQbv6Ucdi6csWUb-WKxlc7KkIkyluZwLjnCK38U5q03AUDK1lxYWezg1RCcs4fjM47S-bJy1J9P-F2EYr20xfSxbhR6VzyCaTnBHuoJN5iysA_CY4vu6omRDZqOs5J7nXGMTquILljFNHrSLFhNx-tqNrSR2yIbCvC4hnns04-EEOXGptze6GVDdPHu8ehmS2aRYxelhf6gZH4FaoehsbbDiINMRUJPmlIPrxKbP9tSBEMCc6HqrLX5a9n5-CKhk4ZBqcjph3pNgPDR67vjzBDaDZPW9SmHhsU_Q0I98Ef_t6Rd-jBj2twH_u45xlIs5l7zso7v25Bf7RyTj3NQA8BalfIzSBsDEbZRktfsTGcJR2zXmB45BAp5oujNNCo502WzZNP_j40PVCzXCi2T9IidJEMeWod5mmVEGbp1j0nyFX2z7l7CyEBI4PTxGnhT9qxxBhhZL8WMZr0b4y0PGnzn4l7KGyHtZiotKfDqhIGIBp0Md6kc_VgGo0cJ-InGaGT1B91E9Q:',
}

@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):
    res = Tool.get(base_url, cookies=cookies, headers=headers)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)
    parse_menu(html, url_dic)
    return url_dic

def parse_menu(html, url_dic):
    menu_items = html.xpath(
        '//ul[contains(concat(" ", normalize-space(@class), " "), " list-menu ")]/li'
    )
    for item in menu_items:
        link = get_item_link(item)
        if not link:
            continue

        name, url = link
        if not is_collection_url(url):
            continue

        url_dic[name] = {'url': Tool.URL.add_site(url), 'child': {}}
        menu_id = item.xpath(
            './div[contains(concat(" ", normalize-space(@class), " "), " toggle-menu ")]'
            '/div[contains(concat(" ", normalize-space(@class), " "), " tree-menu-nav ")]/@id'
        )
        if not menu_id:
            continue

        templates = html.xpath('//template[@x-teleport="#%s"]' % menu_id[0])
        if templates:
            child_items = templates[0].xpath('./template/ul/div/li')
            add_collection_nodes(url_dic[name]['child'], child_items)


def add_collection_nodes(dic, items):
    for item in items:
        link = get_item_link(item)
        child_items = get_child_items(item)

        if not link:
            add_collection_nodes(dic, child_items)
            continue

        name, url = link
        if is_product_url(url):
            # Product entries are never catalog directories. Preserve only any
            # collection descendants that may be nested beneath them.
            add_collection_nodes(dic, child_items)
            continue

        dic[name] = {
            'url': Tool.URL.add_site(url) if is_collection_url(url) else '',
            'child': {},
        }
        add_collection_nodes(dic[name]['child'], child_items)


def get_item_link(item):
    links = item.xpath('./div[1]//a[@href][1]')
    if not links:
        links = item.xpath('./a[@href][1]')
    if not links:
        return None

    link = links[0]
    name = ''.join(link.xpath('.//text()[not(ancestor::style)]')).strip()
    url = link.get('href', '').strip()
    return (name, url) if name and url else None


def get_child_items(item):
    return item.xpath(
        './div[contains(concat(" ", normalize-space(@class), " "), " tree-menu-child ")]/ul/li'
    )


def is_collection_url(url):
    normalized_url = url.lower()
    return '/collections' in normalized_url and '/product' not in normalized_url


def is_product_url(url):
    return '/product' in url.lower()


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    run()



