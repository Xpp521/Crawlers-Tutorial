from os import mkdir
from sys import path
from re import findall
from faker import Faker
from requests import get
from getpass import getpass
from time import time, sleep
from os.path import exists, join
from multiprocessing import Pool, Manager
path.append('../')
from 文字类.Crawler_Sina_Weibo_Login import WeiboLogin

img_headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'Accept-Encoding': 'gzip, deflate, sdch',
               'Accept-Language': 'zh-CN,zh;q=0.8',
               'Cache-Control': 'no-cache',
               'Pragma': 'no-cache',
               'DNT': '1',
               'Connection': 'keep-alive',
               # 'Host': 'wx1.sinaimg.cn',
               'Upgrade-Insecure-Requests': '1'}

headers = {'Accept': '*/*',
           'Accept-Encoding': 'gzip, deflate, sdch, br',
           'Accept-Language': 'zh-CN,zh;q=0.8',
           'Connection': 'keep-alive',
           'Content-Type': 'application/x-www-form-urlencoded',
           'DNT': '1',
           'Host': 'weibo.com',
           'X-Requested-With': 'XMLHttpRequest',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/55.0.2883.87 Safari/537.36 '}

# 代理IP
proxies = [None]


def download_img(queue, sleep_time, folder):
    """
    图片下载方法。
    :param queue: 队列。
    :param sleep_time: 休眠时间。
    :param folder: 文件夹名称。
    """
    global proxies, img_headers
    f = Faker()
    buffer_size = 1024
    while True:
        # 若队列为空，休眠1秒
        if queue.empty():
            sleep(1)
            continue
        # 从队列中取出数据包
        package = queue.get_nowait()
        # 若数据包为0，结束当前进程
        if 0 == package:
            return
        url = package.get('url')
        title = package.get('title')
        if exists(join(folder, title)):
            continue
        img_headers['user-agent'] = f.user_agent()
        # img_headers['Host'] = url.split('/')[2]
        while True:
            try:
                response = get(url, headers=img_headers, proxies=proxies[f.random_digit() % len(proxies)],
                               timeout=(11, None), stream=True)
            except Exception as e:
                print('【下载失败】{}，错误信息：{}，尝试重新下载......'.format(url, e))
                continue
            if response.status_code in (200, 304):
                with open(join(folder, title), 'wb') as file:
                    # 图片的体积较大，采用流方式写入
                    for chunk in response.iter_content(buffer_size):
                        if chunk:
                            file.write(chunk)
                print('【下载成功】{}'.format(url))
                break
            elif 404 == response.status_code:
                continue
            print('【下载失败】{}，状态码：{}，尝试重新下载......'.format(url, response.status_code))
            continue
        # 休眠
        sleep(f.random_int(1, sleep_time))


def set_params(action_data, params_dict):
    """
    设置ajax请求的参数。
    :param action_data: 数据。
    :param params_dict: 参数字典。
    """
    for item in action_data.split('&'):
        a = item.split('=')
        params_dict[a[0]] = a[1]
    # 页数+1
    params_dict['page'] = params_dict.get('page', 1) + 1
    params_dict['__rnd'] = str(round(time() * 1000))


def main():
    global proxies
    session = WeiboLogin(input('用户名：').strip(), getpass('密码：').strip()).login()
    if not session:
        print('登录失败。')
        return
    url = input('输入照片墙网址：').strip()
    page_num = int(input('输入页数：'))
    process_num = int(input('输入子进程数量：'))
    sleep_time = float(input('输入子进程休眠时间（秒）：'))
    # 队列
    queue = Manager().Queue()
    # 进程池
    pool = Pool(process_num)
    faker = Faker()
    # ajax请求的参数
    params = {'ajwvr': '6',
              'page_id': url.split('/')[4],
              'ajax_call': 1}
    package = {}
    for i in range(1, page_num + 1):
        sleep(faker.random_int(1, sleep_time))
        # 第1页解析方法
        if 1 == i:
            while True:
                try:
                    response = session.get(url, proxies=proxies[faker.random_digit() % len(proxies)], timeout=11)
                except Exception as e:
                    print('第1页加载失败，错误信息：{}\n尝试重新加载……'.format(e))
                    continue
                if response.status_code not in (200, 304):
                    print('第1页加载失败，状态码：{}\n尝试重新加载……'.format(response.status_code))
                    continue
                break
            text = response.text
            folder = text[text.find('<title>') + 7: text.find('</title>')].replace('微博_微博', '照片墙')
            if not exists(folder):
                mkdir(folder)
            # 初始化进程池
            for _ in range(process_num):
                pool.apply_async(download_img, [queue, sleep_time, folder])
            print('——————————————开始下载——————————————')
            for img_data in findall(r'<a class=\\"ph_ar_box.*?src=(.*?)>',
                                    text[text.rfind('html":"') + 7: text.rfind('"')]):
                img_data = img_data.replace('/', '').split('\\')
                package['title'] = img_data[-3][:img_data[-3].rfind('?')]
                package['url'] = 'http://{}/large/{}'.format(img_data[3], package.get('title'))
                queue.put_nowait(package)
        # 其它页解析方法
        else:
            while True:
                try:
                    # 模拟发送ajax请求
                    response = session.get('https://weibo.com/p/aj/album/loading', params=params,
                                           proxies=proxies[faker.random_digit() % len(proxies)], timeout=11)
                except Exception as e:
                    print('第{}页加载失败，错误信息：{}\n尝试重新加载……'.format(i, e))
                    continue
                if response.status_code not in (200, 304):
                    print('第{}页加载失败，状态码：{}\n尝试重新加载……'.format(i, response.status_code))
                    continue
                json = response.json()
                if '100000' != json.get('code'):
                    print('第{}页加载失败，失败原因：{}\n尝试重新加载……'.format(i, json.get('msg')))
                    continue
                break
            text = json.get('data')
            for img_data in findall(r'<a class="ph_ar_box.*?src="(.*?)>', text):
                img_data = img_data.split('/')
                package['title'] = img_data[-2][:img_data[-2].rfind('?')]
                package['url'] = 'http://{}/large/{}'.format(img_data[2], package.get('title'))
                queue.put_nowait(package)
        temp = text[text.rfind('WB_cardwrap S_bg2'):]
        action_data = temp[temp.find('"type') + 1: temp.find(r'\">')]
        # 设置下一页ajax请求时的参数
        set_params(action_data, params)
        print('第{}页解析完成。'.format(i))
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
