import requests
from os import mkdir
from re import search
from time import sleep
from faker import Faker
from enum import IntEnum
from lxml.etree import HTML
from os.path import exists, join
from multiprocessing import Pool, Manager


class PackageType(IntEnum):
    """
    数据包类型枚举类。
    """
    EMPTY = 0       # 空包
    ALBUM = 1       # 图集
    IMG = 2         # 图片


class Package:
    """
    数据包类。
    """
    def __init__(self, package_type, name='', url='', channel=''):
        """
        :param package_type: 数据包类型。
        :param name: 名称。
        :param url: 网址。
        :param channel: 图片分类。
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
====================='''.format(self._type, self._name, self._url, self._channel)


class MziTuSpider:
    """
    www.mzitu.com爬虫类。
    """
    channels = {'最新': 'https://www.mzitu.com/',
                '最热': 'https://www.mzitu.com/hot/',
                '推荐': 'https://www.mzitu.com/best/',
                '性感': 'https://www.mzitu.com/xinggan/',
                '日本': 'https://www.mzitu.com/japan/',
                '台湾': 'https://www.mzitu.com/taiwan/',
                '清纯': 'https://www.mzitu.com/mm/',
                '自拍': 'https://www.mzitu.com/zipai/',
                '街拍': 'https://www.mzitu.com/jiepai/',
                '所有': 'https://www.mzitu.com/all/'}

    zhuanti_channels = {'COSPLAY': 'https://www.mzitu.com/tag/cosplay/',
                        'Carry': 'https://www.mzitu.com/tag/carry/',
                        'Cheryl青树': 'https://www.mzitu.com/tag/cheryl-qingshu/',
                        'Egg尤妮丝': 'https://www.mzitu.com/tag/egg-younisi/',
                        'Evelyn艾莉': 'https://www.mzitu.com/tag/evelyn-aili/',
                        'Miki兔': 'https://www.mzitu.com/tag/miki-tu/',
                        'Miko酱': 'https://www.mzitu.com/tag/miko-jiang/',
                        'Milk楚楚': 'https://www.mzitu.com/tag/milk-chuchu/',
                        'M梦Baby': 'https://www.mzitu.com/tag/meng-baby/',
                        'OL诱惑': 'https://www.mzitu.com/tag/ol/',
                        'SOLO尹菲': 'https://www.mzitu.com/tag/solo-yifei/',
                        'Sukki': 'https://www.mzitu.com/tag/sukki/',
                        'Wendy智秀': 'https://www.mzitu.com/tag/wendy-zhixiu/',
                        'luvian本能': 'https://www.mzitu.com/tag/luvian/',
                        'toro羽住': 'https://www.mzitu.com/tag/toro-yuzhu/',
                        '丁筱南': 'https://www.mzitu.com/tag/dingxiaonian/',
                        '丝袜': 'https://www.mzitu.com/tag/siwa/',
                        '丹丹': 'https://www.mzitu.com/tag/dandan/',
                        '乐乐Mango': 'https://www.mzitu.com/tag/lele-mango/',
                        '乔依琳': 'https://www.mzitu.com/tag/qiaoyilin/',
                        '于大小姐': 'https://www.mzitu.com/tag/yudaxiaojie/',
                        '于姬una': 'https://www.mzitu.com/tag/yuji-una/',
                        '亚里沙': 'https://www.mzitu.com/tag/yalisha/',
                        '今野杏南': 'https://www.mzitu.com/tag/jinyexingnan/',
                        '伊小七': 'https://www.mzitu.com/tag/yixiaoqi-momo/',
                        '何嘉颖': 'https://www.mzitu.com/tag/hejiaying/',
                        '何晨曦': 'https://www.mzitu.com/tag/hechenxi/',
                        '佟蔓': 'https://www.mzitu.com/tag/tongman/',
                        '冯木木': 'https://www.mzitu.com/tag/fengmumu-lris/',
                        '凯竹BuiBui': 'https://www.mzitu.com/tag/kaizhu-buibui/',
                        '刘奕宁': 'https://www.mzitu.com/tag/liuyining/',
                        '刘娅希': 'https://www.mzitu.com/tag/liuyaxi/',
                        '刘钰儿': 'https://www.mzitu.com/tag/liuyuer/',
                        '刘飞儿': 'https://www.mzitu.com/tag/liufeier/',
                        '制服诱惑': 'https://www.mzitu.com/tag/zhifu/',
                        '前凸后翘': 'https://www.mzitu.com/tag/tugirl/',
                        '卓娅祺': 'https://www.mzitu.com/tag/zhuoyaqi/',
                        '南湘baby': 'https://www.mzitu.com/tag/nanxiang-baby/',
                        '卤蛋luna': 'https://www.mzitu.com/tag/ludan-luna/',
                        '原干惠': 'https://www.mzitu.com/tag/yuanganhui/',
                        '叶佳颐': 'https://www.mzitu.com/tag/yejiayi/',
                        '吉木梨纱': 'https://www.mzitu.com/tag/jimulisha/',
                        '周于希': 'https://www.mzitu.com/tag/zhouyuxi-dummy/',
                        '唐婉儿': 'https://www.mzitu.com/tag/tangwaner/',
                        '唐思琪': 'https://www.mzitu.com/tag/tangsiqi/',
                        '唐琪儿': 'https://www.mzitu.com/tag/tangqier-beauty/',
                        '唐雨辰': 'https://www.mzitu.com/tag/tangyuchen/',
                        '喜屋武千秋': 'https://www.mzitu.com/tag/xiwuwuqianqiu/',
                        '嘉嘉Tiffany': 'https://www.mzitu.com/tag/jiajia-tiffany/',
                        '嘉宝贝儿': 'https://www.mzitu.com/tag/jiabaobei/',
                        '嘉琳winna': 'https://www.mzitu.com/tag/jialin-winna/',
                        '土肥圆矮挫穷': 'https://www.mzitu.com/tag/tufeiyuanai/',
                        '夏瑶baby': 'https://www.mzitu.com/tag/xiayao-baby/',
                        '夏笑笑': 'https://www.mzitu.com/tag/xiaoxiao/',
                        '夏美酱': 'https://www.mzitu.com/tag/xiameijiang/',
                        '夏茉GIGI': 'https://www.mzitu.com/tag/xiamo-gigi/',
                        '妲己Toxic': 'https://www.mzitu.com/tag/daji-toxic/',
                        '姐妹花': 'https://www.mzitu.com/tag/jiemeihua/',
                        '娜依灵儿': 'https://www.mzitu.com/tag/nayilinger/',
                        '娜露Selena': 'https://www.mzitu.com/tag/selena/',
                        '子纯儿annie': 'https://www.mzitu.com/tag/zhichuner-annie/',
                        '孙梦瑶': 'https://www.mzitu.com/tag/sunmengyao/',
                        '孟狐狸foxyini': 'https://www.mzitu.com/tag/foxyini/',
                        '宅兔兔': 'https://www.mzitu.com/tag/zhaitutu/',
                        '宋-KiKi': 'https://www.mzitu.com/tag/song-kiki/',
                        '宋梓诺': 'https://www.mzitu.com/tag/songzinuo/',
                        '小九月': 'https://www.mzitu.com/tag/xiaojiuyue/',
                        '小尤奈': 'https://www.mzitu.com/tag/xiaoyounai/',
                        '小清新': 'https://www.mzitu.com/tag/qingxin/',
                        '小热巴': 'https://www.mzitu.com/tag/xiaoreba/',
                        '小狐狸Sica': 'https://www.mzitu.com/tag/xiaohuli-sica/',
                        '尤美Yumi': 'https://www.mzitu.com/tag/youmei-ann/',
                        '岸明日香': 'https://www.mzitu.com/tag/hanmingrixiang/',
                        '廿十': 'https://www.mzitu.com/tag/nianshi/',
                        '张优': 'https://www.mzitu.com/tag/zhangyou/',
                        '张栩菲': 'https://www.mzitu.com/tag/zhangxufei/',
                        '张美荧': 'https://www.mzitu.com/tag/zhangmeiying/',
                        '张雨萌': 'https://www.mzitu.com/tag/zhangyumeng/',
                        '徐cake': 'https://www.mzitu.com/tag/xu-cake/',
                        '徐微微': 'https://www.mzitu.com/tag/xuweiwei_mia/',
                        '心妍小公主': 'https://www.mzitu.com/tag/xinyanxiaogongzhu/',
                        '思淇Sukiii': 'https://www.mzitu.com/tag/siqi-sukiii/',
                        '性感内衣': 'https://www.mzitu.com/tag/xingganneiyi/',
                        '恩一': 'https://www.mzitu.com/tag/enyi/',
                        '情趣SM': 'https://www.mzitu.com/tag/sm/',
                        '慕羽茜': 'https://www.mzitu.com/tag/muyuqian/',
                        '护士': 'https://www.mzitu.com/tag/hushi/',
                        '旗袍': 'https://www.mzitu.com/tag/qipao/',
                        '易阳': 'https://www.mzitu.com/tag/yiyang/',
                        '晓茜sunny': 'https://www.mzitu.com/tag/xiaoqian-sunny/',
                        '月音瞳': 'https://www.mzitu.com/tag/yueyintong/',
                        '朱可儿': 'https://www.mzitu.com/tag/barbie-ker/',
                        '杉原杏璃': 'https://www.mzitu.com/tag/sanyuanxingli/',
                        '李七喜': 'https://www.mzitu.com/tag/liqixi/',
                        '李可可': 'https://www.mzitu.com/tag/likeke/',
                        '李宓儿': 'https://www.mzitu.com/tag/limier/',
                        '李梓熙': 'https://www.mzitu.com/tag/lizixi/',
                        '杜花花': 'https://www.mzitu.com/tag/duhuahua/',
                        '杨依': 'https://www.mzitu.com/tag/yangyi/',
                        '杨晨晨': 'https://www.mzitu.com/tag/xiaotianxin-gugar/',
                        '杨漫妮': 'https://www.mzitu.com/tag/yangmanni/',
                        '松果儿': 'https://www.mzitu.com/tag/songguoer/',
                        '林美惠子': 'https://www.mzitu.com/tag/leimeihuizi/',
                        '柳侑绮': 'https://www.mzitu.com/tag/liuyouqi/',
                        '栗子Riz': 'https://www.mzitu.com/tag/lizi-riz/',
                        '校花': 'https://www.mzitu.com/tag/xiaohua/',
                        '梓萱Crystal': 'https://www.mzitu.com/tag/zixuan-crystal/',
                        '梦心月': 'https://www.mzitu.com/tag/mengxinyue/',
                        '森下悠里': 'https://www.mzitu.com/tag/shenxiayouli/',
                        '楚恬Olivia': 'https://www.mzitu.com/tag/chutian_olivia/',
                        '比基尼': 'https://www.mzitu.com/tag/bikini/',
                        '沈佳熹': 'https://www.mzitu.com/tag/shenjiaxi/',
                        '沈梦瑶': 'https://www.mzitu.com/tag/shenmengyao/',
                        '沈蜜桃': 'https://www.mzitu.com/tag/shenmitao/',
                        '沫晓伊baby': 'https://www.mzitu.com/tag/moxiaoyi/',
                        '混血美女': 'https://www.mzitu.com/tag/hunxue/',
                        '清纯美女': 'https://www.mzitu.com/tag/qingchun/',
                        '温心怡': 'https://www.mzitu.com/tag/wenxinyi/',
                        '湿身诱惑': 'https://www.mzitu.com/tag/shishen/',
                        '潘娇娇': 'https://www.mzitu.com/tag/panjiaojiao/',
                        '热裤': 'https://www.mzitu.com/tag/reku/',
                        '熊吖BOBO': 'https://www.mzitu.com/tag/bobo/',
                        '熟女少妇': 'https://www.mzitu.com/tag/shunvshaofu/',
                        '爆乳': 'https://www.mzitu.com/tag/baoru/',
                        '爱丽莎': 'https://www.mzitu.com/tag/ailisha/',
                        '猩一': 'https://www.mzitu.com/tag/xingyi/',
                        '王婉悠': 'https://www.mzitu.com/tag/wangwanyou/',
                        '王梓童': 'https://www.mzitu.com/tag/wangzitong-doirs/',
                        '王雨纯': 'https://www.mzitu.com/tag/wangyuchun/',
                        '王馨瑶': 'https://www.mzitu.com/tag/wangxinyao/',
                        '玛鲁娜manuela': 'https://www.mzitu.com/tag/manuela/',
                        '琳琳ailin': 'https://www.mzitu.com/tag/linlin-ailin/',
                        '瑞瑞ruirui': 'https://www.mzitu.com/tag/ruirui/',
                        '瑞莎Trista': 'https://www.mzitu.com/tag/ruisha/',
                        '甜美女孩': 'https://www.mzitu.com/tag/tianmei/',
                        '田熙玥': 'https://www.mzitu.com/tag/tianxiyue/',
                        '睡衣诱惑': 'https://www.mzitu.com/tag/shuiyiyouhuo/',
                        '穆菲菲': 'https://www.mzitu.com/tag/mufeifei/',
                        '空姐': 'https://www.mzitu.com/tag/kongjie/',
                        '筱崎爱': 'https://www.mzitu.com/tag/xiaoqiai/',
                        '筱慧icon': 'https://www.mzitu.com/tag/xiaohui/',
                        '米妮大萌萌': 'https://www.mzitu.com/tag/minida/',
                        '米雪': 'https://www.mzitu.com/tag/mixue/',
                        '纯小希': 'https://www.mzitu.com/tag/chunxiaoxi/',
                        '绮里嘉ula': 'https://www.mzitu.com/tag/qilijia/',
                        '绯月樱': 'https://www.mzitu.com/tag/xiezhixin/',
                        '网袜': 'https://www.mzitu.com/tag/wangwa/',
                        '美女走光': 'https://www.mzitu.com/tag/zouguang/',
                        '美腿': 'https://www.mzitu.com/tag/leg/',
                        '美臀翘臀': 'https://www.mzitu.com/tag/meitun/',
                        '考拉koala': 'https://www.mzitu.com/tag/kaola-koala/',
                        '艺轩': 'https://www.mzitu.com/tag/yixuan/',
                        '艾小青': 'https://www.mzitu.com/tag/aixiaoqing/',
                        '艾栗栗': 'https://www.mzitu.com/tag/ailili/',
                        '芝芝Booty': 'https://www.mzitu.com/tag/zhizhi-booty/',
                        '萌汉药baby': 'https://www.mzitu.com/tag/menghanyao-baby/',
                        '萌琪琪': 'https://www.mzitu.com/tag/mengqiqi/',
                        '萌萌Vivian': 'https://www.mzitu.com/tag/mengmeng-vivian/',
                        '萝莉': 'https://www.mzitu.com/tag/luoli/',
                        '蔡文钰': 'https://www.mzitu.com/tag/caiwenyu-angle/',
                        '许诺sabrina': 'https://www.mzitu.com/tag/xunuo/',
                        '诗朵雅': 'https://www.mzitu.com/tag/shiduoya/',
                        '诗诗sissi': 'https://www.mzitu.com/tag/xiuren-sisi/',
                        '诱惑': 'https://www.mzitu.com/tag/youhuo/',
                        '赵伊彤': 'https://www.mzitu.com/tag/zhaoyitong/',
                        '赵小米': 'https://www.mzitu.com/tag/zhaoxiaomi/',
                        '车模': 'https://www.mzitu.com/tag/chemo/',
                        '邹晶晶': 'https://www.mzitu.com/tag/zoujingjing/',
                        '郭婉祈': 'https://www.mzitu.com/tag/guowanqi/',
                        '闵妮Mily': 'https://www.mzitu.com/tag/minni-mily/',
                        '陆梓琪': 'https://www.mzitu.com/tag/luziqi/',
                        '陆瓷': 'https://www.mzitu.com/tag/luchi/',
                        '陈思琪art': 'https://www.mzitu.com/tag/chensiqi/',
                        '陈思雨': 'https://www.mzitu.com/tag/chensiyu/',
                        '陈怡曼': 'https://www.mzitu.com/tag/chenyiman/',
                        '雪千寻': 'https://www.mzitu.com/tag/xueqianxun/',
                        '韩恩熙': 'https://www.mzitu.com/tag/hanenxi/',
                        '顾欣怡': 'https://www.mzitu.com/tag/guxinyi/',
                        '顾灿': 'https://www.mzitu.com/tag/gucan/',
                        '黄可christine': 'https://www.mzitu.com/tag/huangke/',
                        '黄楽然': 'https://www.mzitu.com/tag/huangleran/',
                        '黄歆苑': 'https://www.mzitu.com/tag/huangxinyuan/',
                        '黑丝': 'https://www.mzitu.com/tag/heisi/',
                        '齐B小短裙': 'https://www.mzitu.com/tag/duanqun/',
                        '龍籹cool': 'https://www.mzitu.com/tag/panpanlongnv-sunny/'}

    # 代理IP
    proxies = [None]

    web_headers = {'Upgrade-Insecure-Requests': '1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/65.0.3325.162 Safari/537.36'}

    img_headers = {'referer': 'https://www.mzitu.com/', 'Upgrade-Insecure-Requests': '1'}

    def __init__(self, process_num, channel='最新', page_num=1, sleep_time=2, timeout=5):
        """
        :param process_num: 子进程数量。
        :param channel: 图片分类。
        :param page_num: 爬取的页数。
        :param sleep_time: 休眠时间。
        :param timeout: 超时等待时间。
        """
        if not isinstance(process_num, int) or not isinstance(sleep_time, int)\
                or not isinstance(timeout, (float, int)):
            raise TypeError('参数类型错误。')
        if channel not in self.channels.keys() and channel not in self.zhuanti_channels.keys():
            raise ValueError('图片类型错误。')
        if 1 > page_num or 1 > process_num or 1 > sleep_time:
            raise ValueError('参数值错误。')
        self.channel = channel
        self.page_num = page_num
        self.process_num = process_num
        self.sleep_time = sleep_time
        self.timeout = timeout
        self._url = self.channels.get(channel) or self.zhuanti_channels.get(channel)
        self._queue = Manager().Queue()
        self._pool = ''

    @classmethod
    def download_img(cls, url, img_path, timeout=7):
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
        f = Faker()
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
                html = HTML(response.text)
                img_url = html.xpath('/html/body/div[2]/div[1]/div[3]/p/a/img/@src')[0]
                img_url = search('.*[a-z]\d', img_url).group()[:-1]
                count = int(html.xpath('/html/body/div[2]/div[1]/div[4]/a[last()-1]/span/text()')[0])
                print('【开始下载图集】{}（共{}张）'.format(name, count))
                for i in range(1, count + 1):
                    sleep(f.random_int(1, sleep_time))
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
                sleep(f.random_int(1, sleep_time))
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
        图集解析方法。将图集中的图片信息打包成数据包，输入到队列中。
        :param url: 图集网址。
        :rtype: bool。
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
                return False
            print('【图集加载失败】{}，状态码：{}，尝试重新加载……'.format(url, response.status_code))
        content = HTML(response.text)
        base_url = content.xpath('/html/body/div[2]/div[1]/div[3]/p/a/img/@src')[0]
        base_url = base_url[: base_url.rfind('/') + 4]
        try:
            page_num = int(content.xpath('/html/body/div[2]/div[1]/div[4]/a[last()-1]/span/text()')[0])
        except ValueError:
            print('【图集解析失败】{}，失败原因：页码解析失败。'.format(url))
            return False
        for i in range(1, page_num + 1):
            num = '0{}'.format(i) if 0 < i < 10 else '{}'.format(i)
            self._queue.put_nowait(Package(PackageType.IMG, num, '{}{}.jpg'.format(base_url, num),
                                           content.xpath('/html/body/div[2]/div[1]/div[3]/p/a/img/@alt')[0]))
        print('【图集解析完成】{}，数据包数量：{}'.format(url, self._queue.qsize()))
        return True

    def parse_html(self, url):
        """
        网页解析方法。将网页的图片或图集信息打包成数据包，输入到队列中。
        :param url: 网址。
        :rtype: bool。
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
                return False
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
        return True

    def run(self, album_url=''):
        """
        运行爬虫。若存在图集地址则爬取指定图集，否则按照设置爬取分类图片。
        :param album_url: 图集网址。
        """
        print('——————————————开始(⊙o⊙)下载——————————————')
        # 初始化进程池
        self._pool = Pool(self.process_num)
        for _ in range(self.process_num):
            self._pool.apply_async(self.handle_package, [self._queue, self.sleep_time, self.timeout])
        # 爬取指定图集
        if album_url:
            self.parse_album(album_url)
        # 爬取分类图片
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
        # 向队列中输入空包，子进程收到空包会自动结束进程
        for _ in range(self.process_num):
            self._queue.put_nowait(Package(PackageType.EMPTY))
        # 关闭进程池
        self._pool.close()
        # 等待子进程结束
        self._pool.join()
        print('——————————————下载O(∩_∩)O完成——————————————')


def main():
    while True:
        c = input('选择爬虫类型：\n1\t爬取分类图集\n2\t爬取指定图集\n输入对应序号（按“回车”选择爬取指定图集）：').strip()
        if c not in ('1', '2', ''):
            print('序号错误，重新输入！\n')
            continue
        c = int(c) if c else 2
        break
    process_num = int(input('输入子进程数量：').strip())
    sleep_time = int(input('输入最大休眠时间：').strip())
    if 1 == c:
        channels = list(MziTuSpider.channels.keys())
        channels.append('专题')
        print('图集分类：', channels)
        album_type = input('输入图集类型：').strip()
        if '专题' == album_type:
            print('专题图集分类：', list(MziTuSpider.zhuanti_channels.keys()))
        album_type = input('输入专题图集类型：').strip()
        page = int(input('输入爬取页数：').strip())
        spider = MziTuSpider(process_num, album_type, page, sleep_time)
        spider.run()
    else:
        album_url = input('输入图集网址：').strip()
        spider = MziTuSpider(process_num, sleep_time=sleep_time)
        spider.run(album_url)


if __name__ == '__main__':
    main()
    input()
