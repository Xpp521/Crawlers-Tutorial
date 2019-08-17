import requests
from time import sleep
from faker import Faker
from time import strftime
from lxml.etree import HTML
from openpyxl import Workbook


def parse(html, li):
    """
    从html中解析电影信息，并添加到li中。
    """
    for item in html.xpath('//*[@id="content"]/div/div[1]/ol/li/div'):
        num = item.xpath('div[1]/em/text()')[0]
        name = ''.join(item.xpath('div[2]/div[1]/a/span/text()')).replace('&bnsp;', ' ')
        staff = item.xpath('div[2]/div[2]/p[1]/text()')[0].strip()
        other_msg = item.xpath('div[2]/div[2]/p[1]/text()')[1].strip()
        score = item.xpath('div[2]/div[2]/div/span[2]/text()')[0]
        quote = item.xpath('div[2]/div[2]/p[2]/span/text()')
        li.append([num, name, staff, other_msg, score, quote[0] if quote else ''])


if __name__ == '__main__':
    # 代理IP
    proxies = [{'http': 'http://119.179.165.82:8060'},
               {'http': 'http://119.179.133.44:8060'}]
    faker = Faker()
    headers = {'Referer': 'https://movie.douban.com/top250',
               'Upgrade-Insecure-Requests': '1',
               'User-Agent': faker.user_agent()}
    # 构造url列表
    urls = ['https://movie.douban.com/top250?start={}'.format(page * 25) for page in range(10)]
    # 储存电影信息
    msg = [['影片排名', '影片名称', '演职员信息', '年代/地区/类型', '影片评分', '影片简介']]
    for index, url in enumerate(urls, 1):
        sleep(1.5)
        while True:
            try:
                response = requests.get(url, headers=headers,
                                        proxies=proxies[faker.random_digit() % len(proxies)], timeout=7)
            except Exception as e:
                print('第{}页加载出错，错误信息：{}，尝试重新加载……'.format(index, e))
                continue
            if 200 == response.status_code:
                break
            print('第{}页加载出错，状态码：{}，尝试重新加载……'.format(index, response.status_code))
        print('开始爬取第{}页。'.format(index))
        parse(HTML(response.text), msg)
    wb = Workbook()
    ws = wb.active
    for m in msg:
        ws.append(m)  # 将数据写入表格
    file_name = '豆瓣Top250(截止{}).xlsx'.format(strftime("%Y-%m-%d"))
    wb.save(file_name)
    input('豆瓣Top250信息已保存到“{}”中。'.format(file_name))
