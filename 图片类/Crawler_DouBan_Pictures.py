import requests
from os import mkdir
from time import sleep
from faker import Faker
from lxml.etree import HTML
from os.path import exists, join
from multiprocessing import Pool, Manager


class DouBanPictureSpider:
    """
    豆瓣图集爬虫类。
    """

    # 代理IP
    proxies = [{'http': 'http://{}'.format(line.rstrip())} for line in open('proxies_2019_08_23.txt')]

    web_headers = {'Host': 'movie.douban.com',
                   'Referer': 'https://movie.douban.com/',
                   'Upgrade-Insecure-Requests': '1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/55.0.2883.87 Safari/537.36'}

    img_headers = {'dnt': '1',
                   'referer': 'https://movie.douban.com/',
                   'upgrade-insecure-requests': '1'}

    def __init__(self, url, process_num, sleep_time=7, img_quality=3):
        """
        :param url: 豆瓣图集网址。
        :param process_num: 子进程数量。
        :param sleep_time: 子进程最大休眠时间。
        :param img_quality: 图片质量。
        """
        if not isinstance(process_num, int) or 1 > process_num:
            raise ValueError('子进程数必须是正整数！')
        if not isinstance(sleep_time, int) or 2 > sleep_time:
            raise ValueError('休眠时间必须是大于1正整数！')
        if 'movie.douban.com' not in url or 'photos' not in url:
            raise ValueError('网址格式错误！')
        if 'all_photos' in url:
            raise ValueError('网址中包含多个图集，请输入具体图集网址！')
        if 'type=' in url:
            self.base_url = url[:url.find('type=') + 6]
        elif 'celebrity' in url:
            self.base_url = url.strip() + '?type=C'
        else:
            raise TypeError('网址格式错误！')
        if 1 == img_quality:
            self.img_quality = 'm'
        elif 2 == img_quality:
            self.img_quality = 'l'
        elif 3 == img_quality:
            self.img_quality = 'r'
        else:
            raise TypeError('图片质量格式错误！')
        self.title = ''
        self.process_num = process_num
        self.sleep_time = sleep_time
        self._queue = Manager().Queue()
        self._pool = Pool(process_num)

    @classmethod
    def img_download(cls, title, queue, sleep_time):
        """
        图片下载方法。
        :param title: 图集名称。
        :param queue: 队列。
        :param sleep_time: 最大休眠时间。
        """
        f = Faker()
        while True:
            if queue.empty():
                sleep(1)
                continue
            package = queue.get_nowait()
            if 0 == package:
                return
            url = package.get('url')
            name = package.get('name')
            img_headers = cls.img_headers
            img_headers['user-agent'] = f.user_agent()
            while True:
                try:
                    img_res = requests.get(url, headers=img_headers,
                                           proxies=cls.proxies[f.random_int(max=len(cls.proxies) - 1)], timeout=7)
                except Exception as e:
                    print('【下载失败】{}，错误信息：{}，尝试重新下载......'.format(name, e))
                    continue
                if img_res.status_code in (200, 304):
                    with open(join(title, name), 'wb') as file:
                        file.write(img_res.content)
                    print('【下载成功】{}'.format(name))
                    break
                print('【下载失败】{}，状态码：{}，尝试重新下载......'.format(name, img_res.status_code))
                continue
            sleep(f.random_int(1, sleep_time))

    def parse_album(self, url):
        """
        图集解析方法。
        :param url: 网址。
        """
        f = Faker()
        while True:
            try:
                response = requests.get(url, headers=self.web_headers,
                                        proxies=self.proxies[f.random_int(max=len(self.proxies) - 1)], timeout=7)
            except Exception as e:
                print('【页面加载失败】{}，错误信息：{}\n尝试重新加载……'.format(url, e))
                continue
            if response.status_code not in (200, 304):
                print('【页面加载失败】{}，状态码：{}\n尝试重新加载……'.format(url, response.status_code))
                continue
            break
        html = HTML(response.content.decode('utf-8'))
        package = {}
        for item in html.xpath('//*[@id="content"]/div/div[1]/ul/li/div[1]/a/img/@src'):
            img_url = item.replace('photo/m/public', 'photo/{}/public'.format(self.img_quality))
            if 'r' != self.img_quality:
                img_url = img_url.replace('.jpg', '.webp')
            filename = img_url.split('/')[-1]
            if exists(join(self.title, filename)):
                continue
            package['url'] = img_url
            package['name'] = filename
            self._queue.put_nowait(package)

    def run(self):
        while True:
            try:
                response = requests.get(self.base_url, headers=self.web_headers, timeout=10)
            except Exception as e:
                print('【页面加载失败】错误信息：{}\n尝试重新加载……'.format(e))
                continue
            if response.status_code not in (200, 304):
                print('【页面加载失败】状态码：{}\n尝试重新加载……'.format(response.status_code))
                continue
            break
        html = HTML(response.content.decode('utf-8'))
        self.title = html.xpath('//*[@id="content"]/h1/text()')[0].replace('*', '_')
        if not exists(self.title):
            mkdir(self.title)
        try:
            max_page = int(html.xpath('//*[@id="content"]/div/div[1]/div[2]/a[last()]/text()')[0])
        except IndexError:
            max_page = 1
        urls = ['{}&start={}&sortby=like&size=a&subtype=a'.format(self.base_url, i * 30) for i in range(max_page)]
        for _ in range(self.process_num):
            self._pool.apply_async(self.img_download, [self.title, self._queue, self.sleep_time])
        print('——————————————Start downloading...——————————————')
        for url in urls:
            self.parse_album(url)
            sleep(self.sleep_time)
        for _ in range(self.process_num):
            self._queue.put_nowait(0)
        self._pool.close()
        self._pool.join()
        print('——————————————All Done~!——————————————')


def main():
    picture_url = input('输入图集网址：').strip()
    process_number = int(input('输入子进程数量：'))
    process_sleep_time = int(input('输入最大休眠时间（秒）：'))
    while True:
        quality = input('输入图片质量（1、2、3分别代表中、高、原图，按回车默认下载原图）：')
        if quality in ('1', '2', '3', ''):
            quality = int(quality) if quality else 3
            break
        print('格式错误！')
        continue
    spider = DouBanPictureSpider(picture_url, process_number, process_sleep_time, quality)
    spider.run()


if __name__ == '__main__':
    main()
    input()
