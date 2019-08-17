import requests
from os import mkdir
from enum import IntEnum
from time import sleep
from faker import Faker
from lxml.etree import HTML
from os.path import exists, join
from multiprocessing import Pool, Manager


class PackageType(IntEnum):
    """
    数据包类型。
    """
    EMPTY = 0       # 空包
    ALBUM = 1       # 图集
    IMG = 2         # 图片


class Package:
    """
    队列数据包类。
    """
    def __init__(self, package_type, name='', url='', channel=''):
        """
        :param package_type: 数据类型。
        :param name: 名称。
        :param url: 网址。
        :param channel: 图片类型。
        """
        if not isinstance(package_type, PackageType):
            raise TypeError('数据包类型错误。')
        if PackageType.EMPTY != package_type and (not name or not channel or not url.startswith(('http://',
                                                                                                 'https://'))):
            raise ValueError('数据格式错误。')
        self._type = package_type
        self._name = name
        self._url = url
        self._channel = channel

    @property
    def name(self):
        return self._name

    @property
    def url(self):
        return self._url

    @property
    def type(self):
        return self._type

    @property
    def channel(self):
        return self._channel

    def __repr__(self):
        return '''\n=====================
type: {}
name: {}
url: {}
channel: {}
====================='''.format(self.type, self.name, self.url, self.channel)


class MziTuSpider:
    """
    www.mzitu.com爬虫类。
    """
    channels = {'首页': 'https://www.mzitu.com/',
                '性感': 'https://www.mzitu.com/xinggan/',
                '日本': 'https://www.mzitu.com/japan/',
                '台湾': 'https://www.mzitu.com/taiwan/',
                '清纯': 'https://www.mzitu.com/mm/',
                '自拍': 'https://www.mzitu.com/zipai/',
                '街拍': 'https://www.mzitu.com/jiepai/',
                '所有': 'https://www.mzitu.com/all/'}

    web_headers = {'Upgrade-Insecure-Requests': '1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/55.0.2883.87 Safari/537.36'}

    img_headers = {'referer': 'https://www.mzitu.com/',
                   'Upgrade-Insecure-Requests': '1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/55.0.2883.87 Safari/537.36'}

    # 代理IP，没有就改成proxies = [None]
    proxies = [{'http': 'http://120.210.219.73:8080'},
               {'http': 'http://222.66.94.130:80'},
               {'http': 'http://117.191.11.74:80'},
               {'http': 'http://39.105.229.239:8080'}]

    def __init__(self, channel, page_num, process_num, sleep_time, timeout=7):
        """
        :param channel: 图片类型。
        :param page_num: 爬取的页数。
        :param process_num: 子进程数量。
        :param sleep_time: 睡眠时间。
        :param timeout: 超时等待时间。
        """
        if not isinstance(process_num, int) or not isinstance(sleep_time, float)\
                or not isinstance(timeout, (float, int)):
            raise TypeError('参数类型错误。')
        if channel not in self.channels.keys() or 1 > page_num or 1 > process_num or 1 > sleep_time:
            raise ValueError('参数值错误。')
        self.channel = channel
        self.page_num = page_num
        self.process_num = process_num
        self.sleep_time = sleep_time
        self.timeout = timeout
        self._url = self.channels.get(channel)
        self._queue = Manager().Queue()
        self._pool = ''

    @classmethod
    def download_img(cls, url, img_path, timeout=7):  # 图片下载方法
        """
        图片下载方法。
        :param url: 图片网址。
        :param img_path: 图片储存路径。
        :param timeout: 超时等待时间。
        :return: 若成功则返回1，否则返回状态码，0代表加载失败。
        """
        faker = Faker()
        headers = cls.img_headers
        proxies = cls.proxies
        headers['User-Agent'] = faker.user_agent()
        try:
            img = requests.get(url, headers=headers, proxies=proxies[faker.random_digit() % len(proxies)],
                               timeout=timeout)
        except Exception as e:
            print('【下载失败】{}，失败信息：{}，尝试重新下载……'.format(img_path, e))
            return 0
        if 200 == img.status_code:
            with open(img_path, 'wb') as f:
                f.write(img.content)
            print('【下载成功】{}'.format(img_path))
            return 1
        print('【下载失败】{}，状态码：{}'.format(img_path, img.status_code))
        return img.status_code

    @classmethod
    def handle_package(cls, queue, sleep_time, timeout):
        """
        子进程的数据包处理方法。从队列获取数据包，解析并下载其中的图片。
        :param queue: 队列。
        :param sleep_time: 每次下载后的休眠时间。
        :param timeout: 超时等待时间。
        """
        while True:
            # 若队列为空，休眠1秒
            if queue.empty():
                sleep(1)
                continue
            # 从队列中取出数据包
            package = queue.get_nowait()
            # print(package)
            name = package.name
            url = package.url
            channel = package.channel
            # 如果是空包，结束当前进程
            if PackageType.EMPTY == package.type:
                return
            # 图集包处理方法
            elif PackageType.ALBUM == package.type:
                if not exists(channel):
                    mkdir(channel)
                if not exists(join(channel, name)):
                    mkdir(join(channel, name))
                while True:
                    try:
                        response = requests.get(url, headers=cls.web_headers, timeout=timeout)
                    except Exception as e:
                        print('【图集加载失败】{}，失败信息：{}，尝试重新加载……'.format(name, e))
                        continue
                    if 200 == response.status_code:
                        break
                    print('【图集加载失败】{}，状态码：{}，尝试重新加载……'.format(name, response.status_code))
                img_url = HTML(response.text).xpath('/html/body/div[2]/div[1]/div[3]/p/a/img/@src')[0]
                img_url = img_url[: img_url.rfind('/') + 4]
                print('【开始下载图集】', name)
                for i in range(1, 100):
                    sleep(sleep_time)
                    num = '0{}'.format(i) if 0 < i < 10 else i
                    while True:
                        if exists(join(channel, name, '{}.jpg'.format(num))):
                            flag = -1
                            break
                        flag = cls.download_img('{}{}.jpg'.format(img_url, num),
                                                join(channel, name, '{}.jpg'.format(num)), timeout)
                        if flag:
                            break
                    if -1 == flag:
                        continue
                    if 404 == flag:
                        break
                print('【图集下载成功】', name)
            # 图片包处理方法
            elif PackageType.IMG == package.type:
                if not exists(channel):
                    mkdir(channel)
                while True:
                    if exists(join(channel, '{}.jpg'.format(name))):
                        break
                    flag = cls.download_img(url, join(channel, '{}.jpg'.format(name)), timeout)
                    if flag:
                        break

    def parse_album(self, url):
        """
        解析图集方法。将其中的图片或图集打包成数据包，输入到队列中。
        :param url: 图集网址。
        :return: 成功返回1，若网址不存在返回0。
        """
        while True:
            try:
                response = requests.get(url, headers=self.web_headers, timeout=self.timeout)
            except Exception as e:
                print('【图集加载失败】{}，失败信息：{}，尝试重新加载……'.format(url, e))
                continue
            if 200 == response.status_code:
                break
            if 404 == response.status_code:
                print('【图集加载失败】{}，状态码：404'.format(url))
                return 0
            print('【图集加载失败】{}，状态码：{}，尝试重新加载……'.format(url, response.status_code))
        content = HTML(response.text)
        base_url = content.xpath('/html/body/div[2]/div[1]/div[3]/p/a/img/@src')[0]
        base_url = base_url[: base_url.rfind('/') + 4]
        try:
            page_num = int(content.xpath('/html/body/div[2]/div[1]/div[4]/a[last()-1]/span/text()')[0])
        except ValueError:
            print('【图集解析失败】{}，失败原因：页码解析失败。'.format(url))
            return 0
        for i in range(1, page_num + 1):
            num = '0{}'.format(i) if 0 < i < 10 else '{}'.format(i)
            self._queue.put_nowait(Package(PackageType.IMG, num, '{}{}.jpg'.format(base_url, num),
                                           content.xpath('/html/body/div[2]/div[1]/div[3]/p/a/img/@alt')[0]))
        print('【图集解析完成】{}，数据包数量：{}'.format(url, self._queue.qsize()))
        return 1

    def parse_html(self, url):
        """
        解析网页方法。将其中的图片或图集打包成数据包，输入到队列中。
        :param url: 网址。
        :return: 成功返回1，若网址不存在返回0。
        """
        while True:
            try:
                response = requests.get(url, headers=self.web_headers, timeout=self.timeout)
            except Exception as e:
                print('【网页加载失败】{}，失败信息：{}，尝试重新加载……'.format(url, e))
                continue
            if 200 == response.status_code:
                break
            if 404 == response.status_code:
                return 0
        content = HTML(response.text)
        channel = self.channel
        # 不同的分类对应不同的解析方法
        if '所有' == channel:
            for a_tag in content.xpath('/html/body/div[2]/div[1]/div[2]/ul/li/p[2]/a'):
                self._queue.put_nowait(Package(PackageType.ALBUM, a_tag.xpath('text()')[0], a_tag.xpath('@href')[0],
                                               channel))
        elif channel in ('自拍', '街拍'):
            for div_tag in content.xpath('//*[@id="comments"]/ul/li/div'):
                url = div_tag.xpath('p/img/@data-original')[0]
                name = '{}_{}'.format(div_tag.xpath('div[2]/a/text()')[0].strip().replace('/', '.').replace(':', '.'),
                                      url[url.rfind('/') + 1: url.rfind('.')])
                self._queue.put_nowait(Package(PackageType.IMG, name, url, channel))
        else:
            for a_tag in content.xpath('//*[@id="pins"]/li/a'):
                self._queue.put_nowait(Package(PackageType.ALBUM, a_tag.xpath('img/@alt')[0], a_tag.xpath('@href')[0],
                                               channel))
        print('【网页加载完成】{}，数据包数量：{}'.format(url, self._queue.qsize()))
        return 1

    def run(self, album_url=''):
        """
        运行爬虫。若存在图集地址则爬取指定图集，否则按照设置爬取分类图片。
        :param album_url: 图集地址。
        """
        print('——————————————开始(⊙o⊙)下载——————————————')
        # 初始化进程池
        self._pool = Pool(self.process_num)
        for _ in range(self.process_num):
            self._pool.apply_async(self.__class__.handle_package, [self._queue, self.sleep_time, self.timeout])
        # 爬取指定图集
        if album_url:
            self.parse_album(album_url)
        # 按照设置爬取分类图片
        else:
            # 构造url列表
            if '所有' == self.channel:
                urls = [self._url]
            elif self.channel in ('自拍', '街拍'):
                urls = ['{}comment-page-{}'.format(self._url, page) for page in range(1, self.page_num + 1)]
            else:
                urls = ['{}page/{}'.format(self._url, page) for page in range(1, self.page_num + 1)]
            # 解析url
            for url in urls:
                if not self.parse_html(url):
                    break
                sleep(self.sleep_time)
        # 向队列中输入空包，子进程收到空包就会结束进程
        for _ in range(self.process_num):
            self._queue.put_nowait(Package(PackageType.EMPTY))
        # 关闭进程池
        self._pool.close()
        # 等待子进程结束
        self._pool.join()
        print('——————————————下载O(∩_∩)O完成——————————————')


def main():
    for k in MziTuSpider.channels.keys():
        print('\t{}'.format(k), end='')
    channel = input('\n请选择图片类型：')
    page_num = int(input('请输入下载的页数：'))
    process_num = int(input('请输入子进程数：'))
    sleep_time = float(input('请输入休眠时间：'))
    spider = MziTuSpider(channel, page_num, process_num, sleep_time)
    spider.run()


if __name__ == '__main__':
    main()
    input()
