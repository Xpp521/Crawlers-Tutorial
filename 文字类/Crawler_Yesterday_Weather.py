import time
import smtplib
import requests
import schedule
from lxml.etree import HTML
from email.utils import formataddr
from email.mime.text import MIMEText


def send_mail(receiver_addr, subject, body):
    """
    发送邮件。
    :param receiver_addr: 收件人邮箱地址。
    :param subject: 主题。
    :param body: 内容。
    :return: 成功返回True，否则返回False。
    """
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = formataddr(['黄花菜天气委员会', '987654321@qq.com'])
        msg['To'] = receiver_addr
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login('987654321@qq.com', '授权码')
        server.sendmail('987654321@qq.com', [receiver_addr, ], msg.as_string())
        server.quit()
    except Exception as e:
        print('【{}】邮件发送失败！失败信息：{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), e))
        return False
    print('【{}】邮件发送成功。'.format(time.strftime('%Y-%m-%d %H:%M:%S')))
    return True


def send_weather(addr, day, night):
    """
    整合天气信息并发送邮件。
    :param addr: 收件人邮件地址。
    :param day: 白天天气。
    :param night: 夜间天气。
    :return: 成功返回True，否则返回False。
    """
    body = '温度:{}℃({})~{}℃({}) 风速:{}{}~{}{} 日长:{}~{}'.format(night.get('temp'), night.get('weather'),
                                                             day.get('temp'), day.get('weather'), day.get('wind'),
                                                             day.get('wind_speed'), night.get('wind'),
                                                             night.get('wind_speed'), day.get('sun'), night.get('sun'))
    # 发送邮件
    return send_mail(addr, '{}天气情况'.format(day.get('date')), body)


def get_weather(url, weather):
    """
    抓取天气。
    :param url: 网址。
    :param weather: 储存天气信息的对象。
    """
    while True:
        try:
            response = requests.get(url, headers={'Host': 'www.weather.com.cn',
                                                  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                                                                'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                                'Chrome/55.0.2883.87 Safari/537.36'},
                                    timeout=7)
        except Exception as e:
            print('【{}】抓取天气失败，失败信息：{}，尝试重新加载……'.format(time.strftime('%Y-%m-%d %H:%M:%S'), e))
            continue
        if 200 == response.status_code:
            break
        print('【{}】抓取天气失败，状态码：{}，尝试重新加载……'.format(time.strftime('%Y-%m-%d %H:%M:%S'),
                                                  response.status_code))
    li = HTML(response.content.decode('utf8')).xpath('//*[@id="today"]/div[1]/ul/li[1]')[0]
    weather['date'] = li.xpath('h1/text()')[0]
    weather['weather'] = li.xpath('p[1]/text()')[0]
    weather['temp'] = li.xpath('p[2]/span/text()')[0].replace('-', '—')
    weather['wind'] = li.xpath('p[3]/span/@title')[0]
    weather['wind_speed'] = li.xpath('p[3]/span/text()')[0].replace('-', '~')
    sun = li.xpath('p[last()]/span/text()')[0]
    weather['sun'] = sun[sun.find(' ') + 1:]


def main():
    print('【{}】开始执行脚本……'.format(time.strftime('%Y-%m-%d %H:%M:%S')))
    # 目前只支持景点类页面的天气抓取
    url = 'http://www.weather.com.cn/weather1d/10111010119A.shtml'
    day_weather = {}
    night_weather = {}
    # 收件人邮箱地址
    receiver_addr = '123456789@qq.com'
    # 抓取白天天气
    schedule.every().day.at('17:30').do(get_weather, url, day_weather)
    # 抓取夜间天气
    schedule.every().day.at('23:30').do(get_weather, url, night_weather)
    # 发送邮件
    schedule.every().day.at('23:59').do(send_weather, receiver_addr, night_weather, night_weather)
    while True:
        schedule.run_pending()
        # 每30秒检测一次
        time.sleep(30)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        input('【{}】脚本出现异常：{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), e))
