import requests
from os import mkdir
from faker import Faker
from lxml.etree import HTML
from time import time, sleep
from os.path import exists, join
from multiprocessing import Pool, Manager

img_headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'accept-encoding': 'gzip, deflate, sdch, br',
               'accept-language': 'zh-CN,zh;q=0.8',
               'cache-control': 'no-cache',
               'pragma': 'no-cache',
               'dnt': '1',
               # 'Host': 'wx1.sinaimg.cn',
               # 'Referer': 'http://photo.weibo.com/',
               'upgrade-insecure-requests': '1'}

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
proxies = [{'http': 'http://117.191.11.109:80'},
           {'http': 'http://183.146.213.198:80'},
           {'http': 'http://183.146.213.157:80'},
           {'http': 'http://39.137.69.10:8080'},
           {'http': 'http://39.137.69.7:8080'}]


def download_img(queue, sleep_time, folder):
    """
    图片下载方法。
    :param queue: 队列。
    :param sleep_time: 休眠时间。
    :param folder: 文件夹名称。
    """
    global proxies
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
                response = requests.get(url, headers=img_headers, proxies=proxies[f.random_digit() % len(proxies)],
                                        timeout=(11, None), stream=True)
            except Exception as e:
                print(url, '下载失败，错误信息：{}，尝试重新下载......'.format(e))
                continue
            if response.status_code in (200, 304):
                with open(join(folder, title), 'wb') as file:
                    # file.write(response.content)
                    # 图片的体积较大，采用流方式写入
                    for chunk in response.iter_content(buffer_size):
                        if chunk:
                            file.write(chunk)
                print(url, '下载完成。')
                break
            print(url, '下载失败，错误码：{}，尝试重新下载......'.format(response.status_code))
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
    # url = 'https://weibo.com/p/1004061393786362/photos?from=page_100406&mod=TAB'
    url = input('请输入照片墙网址：').strip()
    # 需要先登录微博，然后在任意微博页面打开开发者工具（按F12），刷新页面
    # 在Network标签\里找到第一个请求，在请求的Request Headers里边复制Cookie即可。
    # PS：模拟登录功能正在编写中，敬请期待……
    cookie = input('请输入Cookie：').strip()
    headers['Referer'] = url
    headers['Cookie'] = cookie
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
        sleep(sleep_time)
        # 第1页解析方法
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
            content = HTML(text[text.rfind('html":"') + 7: text.rfind('"')])
            folder = text[text.find('<title>') + 7: text.find('</title>')].replace('微博_微博', '照片墙')
            if not exists(folder):
                mkdir(folder)
            # 初始化进程池
            for _ in range(process_num):
                pool.apply_async(download_img, [queue, sleep_time, folder])
            print('——————————————开始下载——————————————')
            for img in content.xpath("//a[@class='\\\"ph_ar_box\\\"']/img/@src"):
                img_data = img.split('/')
                package['title'] = img_data[-2][:img_data[-2].rfind('?')]
                package['url'] = 'https://{}/large/{}'.format(img_data[2][:img_data[2].find('\\')],
                                                              package.get('title'))
                queue.put_nowait(package)
            temp = text[text.rfind('WB_cardwrap S_bg2'):]
            action_data = temp[temp.find('action-data') + 14: temp.find(r'\">')]
            set_params(action_data, params)
            continue
        # 其它页解析方法
        while True:
            try:
                # 模拟发送ajax请求
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
            print('第{}页加载失败，失败原因：{}'.format(params.get('page'), json.get('msg')))
            break
        content = HTML(json.get('data'))
        for img in content.xpath('/html/body/div/ul/li/div/a[@class="ph_ar_box"]/img/@src'):
            img_data = img.split('/')
            package['title'] = img_data[-1][:img_data[-1].rfind('?')]
            package['url'] = 'https://{}/large/{}'.format(img_data[2], package.get('title'))
            queue.put_nowait(package)
        action_data = content.xpath('//div[@class="WB_cardwrap S_bg2"]/@action-data')[0]
        # 设置下一页ajax请求时的参数
        set_params(action_data, params)
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
