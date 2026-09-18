import sys
import traceback
from lxml import etree

from playwright.sync_api import sync_playwright
from loguru import logger

from config import base_url, Tool as tool, zs

Tool = tool
save_path = Tool.File.path_add_site('data/ml.json')

# 启用 loguru 输出到 stderr
logger.remove()
logger.add(sys.stderr, level='INFO')


def f(dic,childs):
    for child in childs:
        name, url = Tool.HTML.get_a_text_and_url(child)
        url = Tool.URL.add_site(url)
        if 'https://baboontothemoon.com/pages' in url:
            continue
        dic[name] = url


    return dic




@zs('支持二级分类，三级未实现,数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):
    global Tool

    url = base_url
    url_dic['Shop'] = {'url':base_url,'child':{}}

    global Tool

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/142.0.0.0 Safari/537.36'
                )
            )
            page = context.new_page()

            logger.info('正在加载页面...')
            page.goto(base_url, wait_until='load', timeout=60000)
            page.wait_for_timeout(3000)
            logger.info('页面加载完成')

            html_content = page.content()

            Tool.HTML.save(html_content)
            html = etree.HTML(html_content)
            browser.close()
    except Exception as e:
        logger.error(f'执行异常: {e}')
        logger.error(traceback.format_exc())

    nav = html.xpath('//nav[@class="overflow-hidden"]')[0]
    a_ls = nav.xpath('./a')


    url_dic = f(url_dic['Shop']['child'],a_ls)
    print(url_dic)
    return url_dic



def run():
    url_dic = {}
    f1(url_dic)
    logger.info(f'最终 url_dic: {list(url_dic.keys())}')
    Tool.to_ml_json(url_dic, save_path)


if __name__ == '__main__':
    run()
