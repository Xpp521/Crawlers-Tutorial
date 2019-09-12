import execjs
from re import search
from time import sleep
from requests.sessions import Session


class BaiduTranslator:
    """
    百度翻译类。
    """
    _api = 'https://fanyi.baidu.com/v2transapi'
    _js_file = 'Baidu_Translation_js.js'
    lang_list = {'zh': '中文', 'jp': '日语', 'jpka': '日语假名', 'th': '泰语', 'fra': '法语', 'en': '英语', 'spa': '西班牙语',
                 'kor': '韩语',
                 'tr': '土耳其语', 'vie': '越南语', 'ms': '马来语', 'de': '德语', 'ru': '俄语', 'ir': '伊朗语', 'ara': '阿拉伯语',
                 'est': '爱沙尼亚语', 'be': '白俄罗斯语', 'bul': '保加利亚语', 'hi': '印地语', 'is': '冰岛语', 'pl': '波兰语', 'fa': '波斯语',
                 'dan': '丹麦语', 'tl': '菲律宾语', 'fin': '芬兰语', 'nl': '荷兰语', 'ca': '加泰罗尼亚语', 'cs': '捷克语', 'hr': '克罗地亚语',
                 'lv': '拉脱维亚语', 'lt': '立陶宛语', 'rom': '罗马尼亚语', 'af': '南非语', 'no': '挪威语', 'pt_BR': '巴西语', 'pt': '葡萄牙语',
                 'swe': '瑞典语', 'sr': '塞尔维亚语', 'eo': '世界语', 'sk': '斯洛伐克语', 'slo': '斯洛文尼亚语', 'sw': '斯瓦希里语', 'uk': '乌克兰语',
                 'iw': '希伯来语', 'el': '希腊语', 'hu': '匈牙利语', 'hy': '亚美尼亚语', 'it': '意大利语', 'id': '印尼语', 'sq': '阿尔巴尼亚语',
                 'am': '阿姆哈拉语', 'as': '阿萨姆语', 'az': '阿塞拜疆语', 'eu': '巴斯克语', 'bn': '孟加拉语', 'bs': '波斯尼亚语', 'gl': '加利西亚语',
                 'ka': '格鲁吉亚语', 'gu': '古吉拉特语', 'ha': '豪萨语', 'ig': '伊博语', 'iu': '因纽特语', 'ga': '爱尔兰语', 'zu': '祖鲁语',
                 'kn': '卡纳达语', 'kk': '哈萨克语', 'ky': '吉尔吉斯语', 'lb': '卢森堡语', 'mk': '马其顿语', 'mt': '马耳他语', 'mi': '毛利语',
                 'mr': '马拉提语', 'ne': '尼泊尔语', 'or': '奥利亚语', 'pa': '旁遮普语', 'qu': '凯楚亚语', 'tn': '塞茨瓦纳语', 'si': '僧加罗语',
                 'ta': '泰米尔语', 'tt': '塔塔尔语', 'te': '泰卢固语', 'ur': '乌尔都语', 'uz': '乌兹别克语', 'cy': '威尔士语', 'yo': '约鲁巴语',
                 'yue': '粤语', 'wyw': '文言文', 'cht': '中文繁体'}
    lang_map = {
        'zh': ['en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
               'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'en': ['zh', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
               'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'ara': ['zh', 'en', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
                'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'est': ['zh', 'en', 'ara', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
                'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'bul': ['zh', 'en', 'ara', 'est', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
                'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'pl': ['zh', 'en', 'ara', 'est', 'bul', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
               'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'dan': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
                'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'de': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
               'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'ru': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
               'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'fra': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
                'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'fin': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'kor', 'nl', 'cs', 'rom', 'pt', 'jp',
                'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'kor': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'nl', 'cs', 'rom', 'pt', 'jp',
                'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'nl': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'cs', 'rom', 'pt', 'jp',
               'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'cs': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'rom', 'pt', 'jp',
               'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'rom': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'pt', 'jp',
                'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'pt': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'jp',
               'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'jp': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
               'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'jpka', 'vie'],
        'swe': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
                'jp', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'slo': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
                'jp', 'swe', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'th': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
               'jp', 'swe', 'slo', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'wyw': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
                'jp', 'swe', 'slo', 'th', 'spa', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'spa': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
                'jp', 'swe', 'slo', 'th', 'wyw', 'el', 'hu', 'it', 'yue', 'cht', 'vie'],
        'el': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
               'jp', 'swe', 'slo', 'th', 'wyw', 'spa', 'hu', 'it', 'yue', 'cht', 'vie'],
        'hu': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
               'jp', 'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'it', 'yue', 'cht', 'vie'],
        'it': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
               'jp', 'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'yue', 'cht', 'vie'],
        'yue': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
                'jp', 'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'cht', 'vie'],
        'cht': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
                'jp', 'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'vie'],
        'vie': ['zh', 'en', 'ara', 'est', 'bul', 'pl', 'dan', 'de', 'ru', 'fra', 'fin', 'kor', 'nl', 'cs', 'rom', 'pt',
                'jp', 'swe', 'slo', 'th', 'wyw', 'spa', 'el', 'hu', 'it', 'yue', 'cht']}

    def __init__(self, source='en', target='zh', timeout=5, proxies=None):
        """
        :param source: 源语言。
        :param target: 目标语言。
        :param timeout: 超时时间。
        :param proxies: 代理IP。
        """
        if source not in self.lang_list.keys():
            raise ValueError('Invalid source language.')
        if target not in self.lang_map.get(source, []):
            raise ValueError('Invalid target language.')
        self._data = {'from': source,
                      'to': target,
                      'transtype': 'realtime',
                      'simple_means_flag': '3'}
        self.timeout = timeout
        self._session = Session()
        self.proxies = proxies
        self._session.headers['user-agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, ' \
                                              'like Gecko) Chrome/65.0.3325.162 Safari/537.36 '
        try:
            # 需要请求2次，因为第一次百度会发一个错误的token
            # 这里研究了好长时间，百度用心何其毒也（＃￣～￣＃）
            self._session.get('https://fanyi.baidu.com/', timeout=self._timeout)
            sleep(0.5)
            response = self._session.get('https://fanyi.baidu.com/', timeout=self._timeout)
        except Exception as e:
            raise ('Translator init fail. fail message : {}'.format(e))
        if 200 != response.status_code:
            raise ('Translator init fail. fail code : {}'.format(response.status_code))
        text = response.content.decode('utf8')
        self._data['token'] = search("token: '(.*?)',", text).groups()[0]
        self._gtk = search("window.gtk = '(.*?)';", text).groups()[0]
        self._js = execjs.compile(open(self._js_file).read())
        # print('token =', self._data.get('token'))
        # print('gtk =', self._gtk)

    def translate(self, text):
        """
        翻译方法。
        :param text: 待翻译文本。
        :rtype: TranslationResult。
        """
        if not text or not isinstance(text, str):
            return TranslationResult(False, msg='Invalid text.')
        self._data['query'] = text
        self._data['sign'] = self._js.call('e', text, self._gtk)  # 计算sign
        try:
            response = self._session.post(self._api, self._data, timeout=self._timeout)
        except Exception as e:
            return TranslationResult(False, msg='Network error, msg:{}'.format(e))
        if 200 == response.status_code:
            json = response.json()
            if json.get('error'):
                return TranslationResult(False, msg='Error code:{}'.format(json.get('error')))
            else:
                return TranslationResult(True, json.get('trans_result').get('data')[0].get('dst'))
        return TranslationResult(False, msg='Network error, Status code:{}'.format(response.status_code))

    @property
    def source(self):
        return self._data.get('from')

    @source.setter
    def source(self, text):
        if text in self.lang_list.keys():
            self._data['from'] = text
        else:
            self._data['from'] = 'en'

    @property
    def target(self):
        return self._data.get('to')

    @target.setter
    def target(self, text):
        if text in self.lang_map.get(self._data.get('from')):
            self._data['to'] = text
        else:
            self._data['to'] = 'zh'

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, t):
        self._timeout = t if isinstance(t, (float, int)) and 1 < t else 5

    @property
    def proxies(self):
        return self._session.proxies

    @proxies.setter
    def proxies(self, p):
        if isinstance(p, dict):
            self._session.proxies = p
        else:
            self._session.proxies = {}


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


def get_first_key(d, value):
    """
    通过值反向获取字典中的第一个键。
    :param d: 字典对象。
    :param value: 值。
    :return: 找到则返回键，否则返回None。
    """
    for k, v in d.items():
        if value == v:
            return k
    return None


def create_translator():
    """
    创建翻译器。
    :return: 翻译器对象、源语言、目标语言。
    """
    print('源语言：', BaiduTranslator.lang_list.values())
    source_language = get_first_key(BaiduTranslator.lang_list, input('\n输入源语言：').strip())
    print('\n支持的目标语言：', end='')
    for lang in BaiduTranslator.lang_map.get(source_language, []):
        print('{}'.format(BaiduTranslator.lang_list.get(lang)), end=' ')
    target_language = get_first_key(BaiduTranslator.lang_list, input('\n\n输入目标语言：').strip())
    # timeout = input('输入超时时间（秒，按回车默认5秒）：').strip() or 5
    return BaiduTranslator(source_language, target_language), source_language, target_language


if __name__ == '__main__':
    translator, _, _ = create_translator()
    while True:
        print('翻译结果：{}'.format(translator.translate(input('\n输入待翻译文字：')).result))
