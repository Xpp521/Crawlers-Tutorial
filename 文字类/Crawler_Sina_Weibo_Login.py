import rsa
from re import search
from time import time
from json import loads
from random import randint
from base64 import b64encode
# from Crypto.PublicKey import RSA
# from Crypto.Cipher import PKCS1_v1_5
from binascii import b2a_hex
from requests.sessions import Session
from urllib.parse import quote, unquote


class WeiboLogin:
    """
    微博登录类。
    """

    def __init__(self, name, pwd, timeout=5):
        """
        :param name: 用户名。
        :param pwd: 密码。
        :param timeout: 超时时间。
        """
        self._name = name
        self._pwd = pwd
        self._nonce = ''
        self._pubkey = ''
        self._rsakv = ''
        self._servertime = ''
        self._su = b64encode(quote(self._name).encode())
        self._sp = ''
        self._session = Session()
        self._session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, ' \
                                              'like Gecko) Chrome/55.0.2883.87 Safari/537.36 '
        self._timeout = timeout if isinstance(timeout, int) and 1 < timeout else 5

    def _pre_login(self):
        """
        预登录方法，获取部分登录所需参数。
        :rtype: bool。
        """
        params = {'entry': 'weibo',
                  'callback': 'sinaSSOController.preloginCallBack',
                  'su': self._su,
                  'rsakt': 'mod',
                  'client': 'ssologin.js(v1.4.19)',
                  '_': int(time() * 1000)}
        try:
            res = self._session.get('https://login.sina.com.cn/sso/prelogin.php', params=params, timeout=self._timeout)
        except Exception:
            return False
        if 200 == res.status_code:
            data = res.text
            data = loads(data[data.find('{'): data.rfind('}') + 1])
            self._nonce = data.get('nonce')
            self._pubkey = data.get('pubkey')
            self._rsakv = data.get('rsakv')
            self._servertime = data.get('servertime')
            # rsa_key = RSA.import_key(b64decode(self._pubkey))
            # cipher = PKCS1_v1_5.new(rsa_key)
            # self._sp=cipher.encrypt(('{}\n{}'.format('\t'.join([self._servertime, self._nonce]), self._pwd)).encode())
            key = rsa.PublicKey(int(self._pubkey, 16), int('10001', 16))
            self._sp = b2a_hex(rsa.encrypt(('{}\t{}\n{}'.format(self._servertime, self._nonce, self._pwd)).encode(),
                                           key))
            # print(self._sp)
            return True
        return False

    def login(self):
        """
        登录方法，登录成功返回Session，否则返回None。
        :rtype: requests.sessions.Session or None。
        """
        if not self._pre_login():
            return None
        data = {'entry': 'weibo',
                'gateway': '1',
                'from': '',
                'savestate': '7',
                'qrcode_flag': 'false',
                'useticket': '1',
                'pagerefer': 'https://login.sina.com.cn/crossdomain2.php',
                'vsnf': '1',
                'su': self._su,
                'service': 'miniblog',
                'servertime': self._servertime + randint(1, 20),
                'nonce': self._nonce,
                'pwencode': 'rsa2',
                'rsakv': self._rsakv,
                'sp': self._sp,
                'sr': '1475*830',
                'encoding': 'UTF-8',
                'prelt': '412',
                'url': 'https://www.weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController'
                       '.feedBackUrlCallBack',
                'returntype': 'META'}
        res = self._session.post('https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)', data=data,
                                 allow_redirects=False, timeout=self._timeout)
        if 200 == res.status_code:
            redirect_url = search(r'replace\("(.*?)"', res.text).groups()[0]
            res = self._session.get(redirect_url, allow_redirects=False, timeout=self._timeout)
            if 200 == res.status_code:
                ticket, ssosavestate = search(r'ticket=(.*?)&ssosavestate=(.*?)"', res.text).groups()
                params = {'ticket': unquote(ticket),
                          'ssosavestate': ssosavestate,
                          'callback': 'sinaSSOController.doCrossDomainCallBack',
                          'scriptId': 'ssoscript0',
                          'client': 'ssologin.js(v1.4.19)',
                          '_': int(time() * 1000)}
                res = self._session.get('https://passport.weibo.com/wbsso/login', params=params,
                                        timeout=self._timeout)
                if 200 == res.status_code:
                    # print(res.content.decode('gbk'))
                    if search('uniqueid":"(.*?)"', res.text):
                        return self._session
        return None


if __name__ == '__main__':
    if WeiboLogin(input('用户名：').strip(), input('密码：').strip()).login():
        input('登录成功。')
    else:
        input('登录失败。')
