import requests
import pandas as pd
from time import sleep
from lxml import etree
from faker import Faker
from multiprocessing import Pool

headers = {'Host': 'www.ip138.com',
           'Referer': 'http://www.ip138.com/post/',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/55.0.2883.87 Safari/537.36'}

# 代理IP
proxies = [None]


def get_post(msg):
    """
    抓取每个省的邮编和区号信息。
    :param msg: 省市信息。
    :return: 表格对象。
    :rtype: (str, pandas.DataFrame)。
    """
    name = msg.get('name')
    url = msg.get('url')
    global headers, proxies
    f = Faker()
    # 随机休眠
    sleep(f.random_int(1, 6))
    while True:
        try:
            response = requests.get(url, headers=headers,
                                    proxies=proxies[f.random_int(max=len(proxies) - 1)], timeout=5)
        except Exception as e:
            print('【加载失败】{}页面加载失败，失败信息：{}，尝试重新加载……'.format(name, e))
            continue
        if 200 == response.status_code:
            break
        print('【加载失败】{}页面加载失败，状态码：{}，尝试重新加载……'.format(name, response.status_code))
    # 从网页中抓取表格
    table = etree.HTML(response.content.decode('GBK')).xpath('/html/body/table[4]')[0]
    print('【{}】抓取成功。'.format(name))
    # 使用pandas库解析表格并返回
    return name, pd.read_html(etree.tostring(table, encoding='utf8').decode())[0]


def get_province(url):
    """
    获取各个省的名称和网址。
    :param url: 网址。
    :return: 各个省的信息列表。
    """
    global headers
    while True:
        try:
            response = requests.get(url, headers=headers, timeout=5)
        except Exception as e:
            print('【加载失败】主页面加载失败，失败信息：{}，尝试重新加载……'.format(e))
            continue
        if 200 == response.status_code:
            break
        print('【加载失败】主页面加载失败，状态码：{}，尝试重新加载……'.format(response.status_code))
    html = etree.HTML(response.content.decode('GBK'))
    result = []
    for item in html.xpath('//*[@id="newAlexa"]/table/tr/td/a'):
        result.append({'name': item.xpath('text()')[0], 'url': url.replace('/post/', item.xpath('@href')[0])})
    print('省市信息获取成功，开始抓取各省市的邮编和区号……')
    return result


def main():
    filename = '全国邮编区号大全.xlsx'
    # 进程池
    pool = Pool()
    items = pool.map(get_post, get_province('http://www.ip138.com/post/'))
    with pd.ExcelWriter(filename) as writer:
        for item in items:
            item[1].to_excel(writer, sheet_name=item[0], header=False, index=False)
    print('抓取完毕，结果已保存到“{}”中。'.format(filename))


if __name__ == '__main__':
    main()
    input()
