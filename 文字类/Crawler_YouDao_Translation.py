from time import time
from hashlib import md5
from random import random
from requests.sessions import Session


class YouDaoTranslator:
    """
    有道翻译类。
    """
    _api = 'http://fanyi.youdao.com/translate_o'
    lang_list = {'ar': '阿拉伯语',
                 'de': '德语',
                 'en': '英语',
                 'es': '西班牙语',
                 'fr': '法语',
                 'id': '印尼语',
                 'it': '意大利语',
                 'ja': '日语',
                 'ko': '韩语',
                 'pt': '葡萄牙语',
                 'ru': '俄语',
                 'vi': '越南语',
                 'zh-CHS': '中文',
                 'AUTO': '自动'}
    lang_map = ['AUTO',
                'zh-CHS2en',
                'en2zh-CHS',
                'zh-CHS2ja',
                'ja2zh-CHS',
                'zh-CHS2ko',
                'ko2zh-CHS',
                'zh-CHS2fr',
                'fr2zh-CHS',
                'zh-CHS2de',
                'de2zh-CHS',
                'zh-CHS2ru',
                'ru2zh-CHS',
                'zh-CHS2es',
                'es2zh-CHS',
                'zh-CHS2pt',
                'pt2zh-CHS',
                'zh-CHS2it',
                'it2zh-CHS',
                'zh-CHS2vi',
                'vi2zh-CHS',
                'zh-CHS2id',
                'id2zh-CHS',
                'zh-CHS2ar',
                'ar2zh-CHS']

    def __init__(self, source='AUTO', target='AUTO', timeout=5):
        """
        :param source: 源语言。
        :param target: 目标语言。
        :param timeout: 超时时间。
        """
        if 'AUTO' == source and 'AUTO' == target or '{}2{}'.format(source, target) in self.lang_map:
            pass
        else:
            raise ValueError('Invalid language.')
        self._data = {'smartresult': 'dict', 'client': 'fanyideskweb', 'doctype': 'json', 'version': '2.1',
                      'keyfrom': 'fanyi.web', 'action': 'FY_BY_REALTlME', 'from': source, 'to': target}
        self.timeout = timeout
        self._appVersion = '5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 ' \
                           'Safari/537.36'
        self._session = Session()
        self._session.headers = {'Referer': 'http://fanyi.youdao.com/',
                                 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, '
                                               'like Gecko) Chrome/65.0.3325.162 Safari/537.36'}
        try:
            # 访问有道翻译页面，获取Cookie。
            response = self._session.get('http://fanyi.youdao.com/', timeout=self._timeout)
        except Exception as e:
            raise ('Translator init fail. fail message : {}'.format(e))
        if 200 != response.status_code:
            raise ('Translator init fail. fail code : {}'.format(response.status_code))

    def translate(self, text):
        """
        翻译方法。
        :param text: 待翻译文本。
        :return: TranslationResult。
        """
        if not text or not isinstance(text, str):
            return TranslationResult(False, msg='Invalid text.')
        # 算法来源：http://shared.ydstatic.com/fanyi/newweb/v1.0.20/scripts/newweb/fanyi.min.js
        t = md5(self._appVersion.encode()).hexdigest()
        r = str(int(time() * 1000))
        i = '{}{}'.format(r, int(10 * random()))
        self._data['i'] = text
        self._data['salt'] = i
        self._data['sign'] = md5('fanyideskweb{}{}n%A-rKaT5fb[Gy?;N5@Tj'.format(text, i).encode()).hexdigest()
        self._data['ts'] = r
        self._data['bv'] = t
        try:
            response = self._session.post(self._api, data=self._data, timeout=self._timeout)
        except Exception as e:
            return TranslationResult(False, msg='Network error, msg:{}'.format(e))
        if 200 == response.status_code:
            json = response.json()
            if 0 == json.get('errorCode'):
                return TranslationResult(True, json.get('translateResult')[0][0].get('tgt'))
            else:
                return TranslationResult(False, msg='Error code:{}'.format(json.get('errorCode')))
        return TranslationResult(False, msg='Network error, Status code:{}'.format(response.status_code))

    @property
    def source(self):
        return self._data.get('from')

    @source.setter
    def source(self, s):
        if s in self.lang_list.keys():
            if 'AUTO' == s:
                self._data['from'] = 'AUTO'
                self._data['to'] = 'AUTO'
            else:
                self._data['from'] = s

    @property
    def target(self):
        return self._data.get('to')

    @target.setter
    def target(self, t):
        if 'AUTO' == t:
            self._data['from'] = 'AUTO'
            self._data['to'] = 'AUTO'
        elif '{}2{}'.format(self._data.get('from'), t) in self.lang_map:
            self._data['to'] = t

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, t):
        self._timeout = t if isinstance(t, (float, int)) and 1 < t else 5


class TranslationResult:
    """
    翻译结果类。
    """
    def __init__(self, status, result='', msg=''):
        """
        :param status: 状态，True或False。
        :param result: 翻译结果。
        :param msg: 错误信息。
        """
        if not isinstance(status, bool):
            raise TypeError('Status must be bool.')
        self._status = status
        self._result = result
        self._msg = msg

    @property
    def status(self):
        return self._status

    @property
    def result(self):
        return self._result

    @property
    def msg(self):
        return self._msg

    def __repr__(self):
        return self._result


def get_first_key(d, value):
    """
    通过值反向获取字典中对应的的第一个键。
    :param d: 字典对象。
    :param value: 值。
    :return: 找到则返回第一个符合的键，否则返回None。
    """
    for k, v in d.items():
        if value == v:
            return k
    return None


def create_translator():
    """
    创建翻译器对象。
    :rtype: YouDaoTranslator。
    """
    print('源语言：{}\nPS：“自动”代表中英互译。'.format(', '.join(YouDaoTranslator.lang_list.values())))
    source_language = get_first_key(YouDaoTranslator.lang_list, input('\n选择源语言：').strip())
    if 'AUTO' == source_language:
        return YouDaoTranslator()
    elif 'zh-CHS' == source_language:
        languages = list(YouDaoTranslator.lang_list.values())
        languages.remove('中文')
        languages.remove('自动')
        print('\n目标语言：{}'.format(', '.join(languages)))
        target_language = get_first_key(YouDaoTranslator.lang_list, input('\n选择目标语言：').strip())
        return YouDaoTranslator(source_language, target_language)
    else:
        return YouDaoTranslator(source_language, 'zh-CHS')


if __name__ == '__main__':
    translator = create_translator()
    while True:
        print('翻译结果：{}'.format(translator.translate(input('\n输入待翻译文字：'))))
