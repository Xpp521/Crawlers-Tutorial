# 文字类爬虫

### 项目简介
- Crawler_Baidu_Translation.py：百度翻译爬虫。破解的接口是：https://fanyi.baidu.com/v2transapi  
（PS：使用PyExecJS执行JS脚本）

- Crawler_DouBan_Top250.py：豆瓣Top250爬虫。可爬取豆瓣Top250中的电影信息并储存到Excel表格中。

- Crawler_GouBanJia_IP.py：爬取网站：www.goubanjia.com 中代理IP的爬虫。结果会自动复制到剪贴板，可以直接将结果粘贴到本项目其它爬虫脚本中使用。  
（PS：使用PyQt4渲染动态网页）

- Crawler_IP138_Post.py：中国各省市的邮编区号爬虫。爬取网站：www.ip138.com/post 中各省市的邮编和区号信息，并将结果储存到Excel表格中。  
（PS：使用pandas解析网页中的表格）

- Crawler_Sina_Weibo_Login.py：模拟登录新浪微博。  
（PS：RSA加密算法）

- Crawler_Yesterday_Weather.py：天气爬虫。爬取当天天气并在凌晨发送邮件，这样第二天即可查看昨天的天气情况。  
（PS：使用schedule执行定时任务）
