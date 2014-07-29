蜘蛛基于Python [Scrapy项目](http://scrapy.org/)搭建

# Python 安装

__1. 安装easy_install__

    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python

__2. 安装pip包管理工具__

    easy_install pip

pip国外源比较慢，建议切换到国内源

    vi ~/.pip/pip.conf 

内容为

```
[global]
index-url = http://pypi.douban.com/simple
```

__3. 安装Python 虚拟环境，方便管理依赖__

    pip install virtualenvwrapper

然后让虚拟环境脚本自动加载

    vi   ~/.bash_profile

添加

    source /usr/local/bin/virtualenvwrapper.sh 

### virtualenvwrapper 用法

新建一个名为scrapy的虚拟环境

    mkvirtualenv scrapy

显示该环境中所安装的包 

    lssitepackages

切换到scrapy虚拟环境

    workon scrapy

退出虚拟环境

    deactivate

# 安装蜘蛛的所有依赖

    apt-get install libjpeg-dev libfreetype6 libfreetype6-dev zlib1g-dev python-mysqldb libmysqlclient-dev


切换到蜘蛛专用的虚拟环境

    workon scrapy

登录蜘蛛服务器，Clone 项目到任意路径，建议与其他项目统一在`/opt/htdocs`下

    cd /opt/htdocs
    clone https://github.com/wallstreetcn/spider.git
    
通过`pip -r`读取文本文件安装所有依赖的包

    cd spider
    pip install -r requirements.txt

# 编写蜘蛛
