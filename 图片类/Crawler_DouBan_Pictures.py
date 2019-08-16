from lxml import etree
import requests
import os
import time
from faker import Faker
from multiprocessing import Pool, Manager


class DouBanPictureSpider:

    proxies = [None]  # 代理ip

    web_headers = {
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        #            'Accept-Encoding': 'gzip, deflate, sdch, br',
        #            'Accept-Language': 'zh-CN,zh;q=0.8',
        #            'Cache-Control': 'max-age=0',
        #            'Connection': 'keep-alive',
        #            'DNT': '1',
                   'Host': 'movie.douban.com',
                   'Referer': 'https://movie.douban.com/',
                   # 'Upgrade-Insecure-Requests': '1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/55.0.2883.87 Safari/537.36'}

    img_headers = {  # 'authority': 'img3.doubanio.com',
        'method': 'GET',
        # 'path': '/view/photo/l/public/p2221721921.webp',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, sdch, br',
        'accept-language': 'zh-CN,zh;q=0.8',
        'cache-control': 'max-age=0',
        # 'cookie': 'bid=CdblCOeRvVw',
        'dnt': '1',
        'if-modified-since': 'Wed, 21 Jan 2004 19:51:30 GMT',
        # 'referer': 'https://movie.douban.com/',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/55.0.2883.87 Safari/537.36'}

    def __init__(self, base_url, process_num, sleep_time=1., img_quality=3):
        """
        :param base_url: 豆瓣图集网址
        :param process_num: 子进程数量
        :param sleep_time: 子进程休眠时间
        :param img_quality: 图片质量
        """
        if not isinstance(process_num, int):
            raise ValueError('子进程数必须是正整数！')
        if not isinstance(sleep_time, float):
            raise ValueError('休眠时间必须是正数！')
        if img_quality not in (1, 2, 3):
            raise ValueError('图片质量必须是1、2或3')
        if not isinstance(base_url, str):
            raise ValueError('网址必须是字符串！')
        if 'movie.douban.com' not in base_url:
            raise ValueError('非豆瓣网址！')
        if 'all_photos' in base_url:
            raise ValueError('网址中包含多个图集，请输入具体图集网址！')
        if 'type=' in base_url:
            self.base_url = base_url[:base_url.find('type=') + 6]
        elif 'celebrity' in base_url:
            self.base_url = base_url.strip() + '?type=C'
        self.process_num = process_num
        self.sleep_time = sleep_time
        if 1 == img_quality:
            self.img_quality = 'm'
        if 2 == img_quality:
            self.img_quality = 'l'
        if 3 == img_quality:
            self.img_quality = 'r'
        self.title = ''
        self.q = Manager().Queue()
        self.pool = Pool(process_num)
        self.f = Faker()

    @classmethod
    def img_download(cls, q, sleep_time):  # 图片下载方法
        f = Faker()
        while True:
            if q.empty():
                time.sleep(1)
                continue
            package = q.get_nowait()
            if 0 == package:
                return
            url = package['url']
            title = package['title']
            name = url[46:-5]
            img_headers = cls.img_headers
            # url: https://img1.doubanio.com/view/photo/l/public/p976209989.webp
            # img_headers['authority'] = url[9:26]
            # img_headers['path'] = url[26:]
            while True:
                try:
                    img = requests.get(url, proxies=cls.proxies[f.random_digit() % len(cls.proxies)], timeout=7)
                except Exception as e:
                    print(url, '下载失败，错误信息：{}，尝试重新下载......'.format(e))
                    continue
                if img.status_code in (200, 304):
                    with open('{}/{}.webp'.format(title, name), 'wb') as file:
                        file.write(img.content)
                    print(url, '下载完成。')
                    break
                print(url, '下载失败，错误码：{}，尝试重新下载......'.format(img.status_code))
                continue
            time.sleep(sleep_time)

    def get_stills(self, url):
        while True:
            try:
                response = requests.get(url, headers=self.web_headers,
                                        proxies=self.proxies[self.f.random_digit() % len(self.proxies)], timeout=7)
            except Exception as e:
                print('加载页面出错，错误信息：{}\n尝试重新加载……'.format(e))
                continue
            if response.status_code not in (200, 304):
                print('加载页面出错，错误码：{}\n尝试重新加载……'.format(response.status_code))
                continue
            break
        html = response.content.decode('utf-8')
        selector = etree.HTML(html)
        package = {}
        for i in range(1, 31):
            still_url = selector.xpath('//*[@id="content"]/div/div[1]/ul/li[%d]/div[1]/a/img/@src' % i)
            try:
                img_url = still_url[0].replace(r'photo/m/public', r'photo/{}/public'.format(self.img_quality))
            except IndexError:
                break
            # url: https://img1.doubanio.com/view/photo/r/public/p976209989.webp
            if os.path.exists('{}/{}.webp'.format(self.title, img_url[46:-5])):
                continue
            package['url'] = img_url
            package['title'] = self.title
            self.q.put_nowait(package)

    def run(self):
        while True:
            try:
                response = requests.get(self.base_url, headers=self.web_headers,
                                        proxies=self.proxies[self.f.random_digit() % len(self.proxies)], timeout=10)
            except Exception as e:
                print('加载页面出错，错误信息：{}\n尝试重新加载……'.format(e))
                continue
            if response.status_code not in (200, 304):
                print('加载页面出错，错误码：{}\n尝试重新加载……'.format(response.status_code))
                continue
            break
        # print(response.content)
        html = response.content.decode('utf-8')
        selector = etree.HTML(html)
        self.title = selector.xpath('//*[@id="content"]/h1/text()')[0].replace('*', '_')
        if not os.path.exists(self.title):
            os.mkdir(self.title)
        try:
            max_page = int(selector.xpath('//*[@id="content"]/div/div[1]/div[2]/a[last()]/text()')[0])
        except IndexError:
            max_page = 0
        p = [x for x in range(max_page)]
        url_list = list(map(lambda i: '{}&start={}&sortby=like&size=a&subtype=a'.format(self.base_url, i * 30), p))
        # if -1 != self.base_url.find('celebrity'):
        #     url_list = list(
        #         map(lambda j: '%s?type=C&start=%d&sortby=like&size=a&subtype=a' % (self.base_url, j * 30), p))
        # else:
        #     url_list = list(map(lambda j: '%s&start=%d&sortby=like&size=a&subtype=a' % (self.base_url, j * 30), p))
        for _ in range(self.process_num):
            self.pool.apply_async(self.__class__.img_download, [self.q, self.sleep_time])
            time.sleep(1)
        for url in url_list:
            self.get_stills(url)
            time.sleep(self.sleep_time)
        for _ in range(self.process_num):
            self.q.put_nowait(0)
        self.pool.close()
        self.pool.join()


if __name__ == '__main__':
    picture_url = input('请输入图集网址：')
    while True:
        try:
            process_number = int(input('请输入下载的进程数：'))
        except ValueError:
            print('输入格式错误！必须是正整数，请重新输入。')
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
    while True:
        picture_quality = input('请输入图片质量（1、2、3分别代表中、高、原图，按回车默认下载原图）：')
        if picture_quality not in ('1', '2', '3', ''):
            print('输入格式错误！请重新输入1、2、3或按回车。')
            continue
        if '' == picture_quality:
            picture_quality = 3
        picture_quality = int(picture_quality)
        break
    try:
        spider = DouBanPictureSpider(picture_url, process_number, process_sleep_time, picture_quality)
    except Exception as e:
        input('\n程序初始化失败！错误信息：{}'.format(e))
        exit(-1)
    else:
        spider.run()
        input('——————————————All Done~!——————————————')
