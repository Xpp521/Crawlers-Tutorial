import time
import requests
from pyperclip import copy
from bs4 import BeautifulSoup
from PyQt4 import QtGui, QtCore, QtWebKit


class Render(QtWebKit.QWebPage):

    def __init__(self, url):
        self.app = QtGui.QApplication([])
        QtWebKit.QWebPage.__init__(self)
        self.loadFinished.connect(self._loadFinished)
        self.mainFrame().load(QtCore.QUrl(url))
        self.app.exec_()

    def _loadFinished(self, result):
        self.frame = self.mainFrame()
        self.app.quit()

    def userAgentForUrl(self, QUrl):
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
        return user_agent


class IpSpider:
    url = 'http://www.goubanjia.com/'

    def test(self, socket):
        proxies = {'http': 'http://' + socket}
        try:
            response = requests.get('http://www.ip38.com/', proxies=proxies, timeout=5)
        except Exception:
            return False
        return True

    def run(self):
        begin_time = time.time()
        print('开始加载网页......')
        response = Render(self.url)
        content = response.frame.toHtml()
        print('网页加载成功。（用时' + str(time.time() - begin_time) + '秒）')
        print('开始测试ip......')
        bs = BeautifulSoup(content, 'lxml')
        ip_infos = bs.find_all('tr', style='')
        strr = ''
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
            if '透明' == flag or ('http' != protocol and 'http,https' != protocol) or '中国' != country:
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
            if self.test(socket):
                print(socket, flag, protocol, country, response_time, survival_time)
                strr += "{'http': 'http://%s'},\n" % socket
                result.append({'http': 'http://%s' % socket})
        if '' == strr:
            input('(⊙o⊙)...非常遗憾，本次没抓到可用的代理IP。')
        else:
            # f = open('代理IP.txt', 'a')
            # f.write(strr + '\n\n')
            # f.close()
            copy(strr)
            input('结果已复制到剪贴板~')
        return result


if __name__ == '__main__':
    IpSpider().run()
