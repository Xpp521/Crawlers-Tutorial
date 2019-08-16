from os import mkdir
from os.path import exists
import requests
from lxml import etree
from time import time, sleep
from faker import Faker
from multiprocessing import Pool, Manager

img_headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'accept-encoding': 'gzip, deflate, sdch, br',
               'accept-language': 'zh-CN,zh;q=0.8',
               'cache-control': 'no-cache',
               'pragma': 'no-cache',
               'dnt': '1',
               # 'Host': 'wx1.sinaimg.cn',
               # 'If-Modified-Since': 'Sat, 21 Jul 2018 13:18:01 GMT',
               # 'If-None-Match': "0A8B1918CFB14BD13EA4D819E568BE66",
               # 'Referer': 'http://photo.weibo.com/',
               # 'Referer': 'http://photo.weibo.com',
               'upgrade-insecure-requests': '1'}

headers = {'Accept': '*/*',
           'Accept-Encoding': 'gzip, deflate, sdch, br',
           'Accept-Language': 'zh-CN,zh;q=0.8',
           'Connection': 'keep-alive',
           'Content-Type': 'application/x-www-form-urlencoded',
           'Cookie': '',
           'DNT': '1',
           'Host': 'weibo.com',
           'Referer': '',
           'X-Requested-With': 'XMLHttpRequest',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/55.0.2883.87 Safari/537.36 '}

# 代理IP
proxies = [{'http': 'http://101.4.136.34:81'},
           {'http': 'http://120.210.219.73:8080'},
           {'http': 'http://117.191.11.74:80'},
           {'http': 'http://39.105.229.239:8080'},
           {'http': 'http://182.116.225.142:9999'}]


def download_img(q, sleep_time, folder):
    """
    图片下载方法。
    :param q: 队列。
    :param sleep_time: 休眠时间。
    :param folder: 文件夹。
    """
    print('method:img_download processing...')
    f = Faker()
    buffer_size = 1024
    while True:
        if q.empty():
            sleep(1)
            continue
        package = q.get_nowait()
        if 0 == package:
            print('package:{}, method end.'.format(package))
            return
        url = package.get('url')
        title = package.get('title')
        if exists('{}/{}'.format(folder, title)):
            continue
        img_headers['user-agent'] = f.user_agent()
        # img_headers['Host'] = url.split('/')[2]
        while True:
            try:
                response = requests.get(url, headers=img_headers, proxies=proxies[f.random_digit() % len(proxies)],
                                        timeout=(11, None), stream=True)
            except Exception as e:
                print(url, '下载失败，错误信息：{}，尝试重新下载......'.format(e))
                continue
            if response.status_code in (200, 304):
                with open('{}/{}'.format(folder, title), 'wb') as file:
                    # file.write(response.content)
                    for chunk in response.iter_content(buffer_size):
                        if chunk:
                            file.write(chunk)
                print(url, '下载完成。')
                break
            print(url, '下载失败，错误码：{}，尝试重新下载......'.format(response.status_code))
            continue
        sleep(sleep_time)


def main():
    # url = 'https://weibo.com/p/1004061393786362/photos?from=page_100406&mod=TAB'
    url = input('请输入照片墙网址：').strip()
    # 需要先登录微博
    # 然后照片墙页面打开开发者工具（按F12），在Network标签随便找一个请求，里边应该就有cookies。
    cookies = input('请输入Cookie：').strip()
    headers['Referer'] = url
    headers['Cookie'] = cookies
    while True:
        try:
            page_num = int(input('请输入页数：'))
        except ValueError:
            print('必须输入正整数！请重新输入。')
            continue
        if page_num <= 0:
            print('必须输入正整数！请重新输入。')
            continue
        break
    while True:
        try:
            process_num = int(input('请输入下载的进程数：'))
        except ValueError:
            print('输入格式错误！必须是≥1的数字，请重新输入。')
            continue
        if process_num < 1:
            print('输入格式错误！必须是≥1的数字，请重新输入。')
            continue
        break
    while True:
        try:
            process_sleep_time = input('请输入子进程的休眠时间（按回车默认休眠1秒）：')
            if '' == process_sleep_time:
                process_sleep_time = 1.
            else:
                process_sleep_time = float(process_sleep_time)
        except ValueError:
            print('输入格式错误！必须是正数，请重新输入。')
            continue
        if process_sleep_time < 0:
            print('输入格式错误！必须是正数，请重新输入。')
            continue
        break
    # 队列
    queue = Manager().Queue()
    # 进程池
    pool = Pool(process_num)
    faker = Faker()
    # 发送ajax请求时的参数
    params = {'ajwvr': '6',
              'page_id': url.split('/')[4],
              'page': '2',
              'ajax_call': 1}
    package = {}
    for i in range(1, page_num + 1):
        sleep(process_sleep_time)
        if 1 == i:
            while True:
                try:
                    response = requests.get(url, headers=headers,
                                            proxies=proxies[faker.random_digit() % len(proxies)], timeout=11)
                except Exception as e:
                    print('加载页面出错，错误信息：{}\n尝试重新加载……'.format(e))
                    continue
                if response.status_code not in (200, 304):
                    print('加载页面出错，错误码：{}\n尝试重新加载……'.format(response.status_code))
                    continue
                break
            text = response.text
            script = text[text.rfind('html":"') + 7: text.rfind('"')]
            content = etree.HTML(script)
            folder = text[text.find('<title>') + 7: text.find('</title>')].replace('微博_微博', '照片墙')
            if not exists(folder):
                mkdir(folder)
            for _ in range(process_num):
                pool.apply_async(download_img, [queue, process_sleep_time, folder])
            for img in content.xpath("//a[@class='\\\"ph_ar_box\\\"']/img/@src"):
                img_data = img.split('/')
                package['title'] = img_data[-2][:img_data[-2].rfind('?')]
                package['url'] = 'https://' + img_data[2][:img_data[2].find('\\')] + '/large/' + package['title']
                queue.put_nowait(package)
            temp = text[text.rfind('WB_cardwrap S_bg2'):]
            action_data = temp[temp.find('action-data') + 14: temp.find(r'\">')]
            # 从action_data中找出ajax请求的参数
            for dat in action_data.split('&'):
                a = dat.split('=')
                params[a[0]] = a[1]
            params['__rnd'] = str(round(time() * 1000))
            continue

        while True:
            try:
                response = requests.get('https://weibo.com/p/aj/album/loading', params=params, headers=headers,
                                        proxies=proxies[faker.random_digit() % len(proxies)], timeout=11)
            except Exception as e:
                print('加载页面出错，错误信息：{}\n尝试重新加载……'.format(e))
                continue
            if response.status_code not in (200, 304):
                print('加载页面出错，错误码：{}\n尝试重新加载……'.format(response.status_code))
                continue
            break
        json = response.json()
        if json.get('code') != '100000':
            print('第{}页加载失败，失败原因：{}'.format(i, json.get('msg')))
            continue
        content = etree.HTML(json.get('data'))
        # print(etree.tostring(content, pretty_print=True).decode('utf8'))
        for img in content.xpath('/html/body/div/ul/li/div/a[@class="ph_ar_box"]/img/@src'):
            img_data = img.split('/')
            package['title'] = img_data[-1][:img_data[-1].rfind('?')]
            package['url'] = 'https://' + img_data[2] + '/large/' + package['title']
            queue.put_nowait(package)
            print('{}已入列。'.format(package['url']))
        action_data = content.xpath('//div[@class="WB_cardwrap S_bg2"]/@action-data')[0]
        # 从action_data中找出ajax请求的参数
        for dat in action_data.split('&'):
            a = dat.split('=')
            params[a[0]] = a[1]
        params['page'] = i + 1
        params['__rnd'] = str(round(time() * 1000))
    # 向队列中输入0，通知子进程结束
    for _ in range(process_num):
        queue.put_nowait(0)
    # 关闭进程池
    pool.close()
    # 等待子进程结束
    pool.join()
    print('——————————————下载完成——————————————')


if __name__ == '__main__':
    main()
    input()
