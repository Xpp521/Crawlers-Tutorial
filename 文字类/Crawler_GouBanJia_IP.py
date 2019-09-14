from time import time
from json import dumps
from requests import get
from pyperclip import copy
from bs4 import BeautifulSoup
from PyQt4 import QtGui, QtCore, QtWebKit


class Render(QtWebKit.QWebPage):
    """
    网页渲染类。可执行JS脚本。
    """
    def __init__(self, url):
        self.app = QtGui.QApplication([])
        QtWebKit.QWebPage.__init__(self)
        self.loadFinished.connect(self.load_finished_handler)
        self.mainFrame().load(QtCore.QUrl(url))
        self.app.exec_()

    def load_finished_handler(self, result):
        self.frame = self.mainFrame()
        self.app.quit()

    def userAgentForUrl(self, QUrl):
        return 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 ' \
               'Safari/537.36 '


class IpSpider:
    _url = 'http://www.goubanjia.com/'

    @staticmethod
    def test(proxy):
        """
        测试代理IP是否有效。
        :param proxy: 代理IP。
        :return: 有效返回True，否则返回False。
        """
        if proxy.get('http'):
            url = 'http://icanhazip.com/'
        elif proxy.get('https'):
            url = 'https://www.ip.cn/'
        else:
            return False
        try:
            get(url, proxies=proxy, timeout=5)
        except Exception:
            return False
        return True

    def run(self):
        begin_time = time()
        print('开始加载网页......')
        # 使用Render类渲染网页
        content = Render(self._url).frame.toHtml()
        print('网页加载成功，用时{}秒。'.format(time() - begin_time))
        print('开始测试ip......\n')
        bs = BeautifulSoup(content, 'lxml')
        ip_infos = bs.find_all('tr', style='')
        result = []
        for ip_info in ip_infos:
            contents = ip_info.contents
            flag = contents[3].string
            protocol = contents[5].string
            country = contents[7].a.string
            # country1 = contents[7].a.next_sibling.string
            # country2 = contents[7].a.next_sibling.next_sibling.string
            response_time = contents[11].string
            survival_time = contents[15].string
            if '透明' == flag or protocol not in ('http', 'https', 'http,https') or '中国' != country:
                continue
            ip_tag = contents[1]
            socket = ''
            for tag in ip_tag:
                try:
                    if 'display: none;' != tag.attrs['style'] and 'display:none;' != tag.attrs['style']:
                        socket += str(tag.string)
                except KeyError:
                    if tag.string is not None:
                        socket += tag.string
                except AttributeError:
                    socket += tag
            socket = socket.replace('None', '')
            proxies = []
            if 'http,https' == protocol:
                proxies.append({'http': 'http://{}'.format(socket)})
                proxies.append({'https': 'https://{}'.format(socket)})
            else:
                proxies.append({protocol: '{}://{}'.format(protocol, socket)})
            for proxy in proxies:
                if self.test(proxy):
                    result.append(proxy)
                    print(socket, flag, protocol, country, response_time, survival_time)
        return result

    @property
    def url(self):
        return self._url


def main():
    filename = '代理IP.txt'
    proxies = IpSpider().run()
    if proxies:
        text = '\n'.join(['{},'.format(dumps(proxy)) for proxy in proxies])
        with open(filename, 'a') as f:
            f.write('{}\n\n'.format(text))
        print('\n结果已保存到“{}”中。'.format(filename))
        copy(text)
        print('结果已复制到剪贴板~\n')
        print(text)
    else:
        print('非常遗憾，没抓到可用的代理IP(⊙o⊙)...')


if __name__ == '__main__':
    main()
    input()
