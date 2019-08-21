# 文字类爬虫

### 项目简介
- Crawler_DouBan_Top250.py：豆瓣Top250爬虫。可爬取豆瓣Top250中的电影信息并储存到Excel表格中。

- Crawler_GouBanJia_IP.py：爬取网站：www.goubanjia.com 中代理IP的爬虫。结果会自动复制到剪贴板，可以直接将结果粘贴到本项目其它爬虫脚本中使用。  
（PS：使用PyQt4渲染网页，获得执行JS脚本后的DOM树）

- Crawler_IP138_Post.py：中国各省市的邮编区号爬虫。爬取网站：www.ip138.com/post 中各省市的邮编和区号信息，并将结果储存到Excel表格中。  
（PS：使用pandas库解析网页中的表格）
