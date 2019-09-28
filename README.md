
## QC-Remind

![release](https://img.shields.io/github/v/release/ad-feiben/qc-remind)
![lisence](https://img.shields.io/github/license/ad-feiben/qc-remind?logo=github)
![travis](https://img.shields.io/travis/ad-feiben/qc-remind?logo=travis)

![logo](./assets/logo.png)

因为我经常需要买卖 QC，为了避免错过最佳的交易时机，所以写了该项目，用来提醒我 QC 市场价，争取获得最大收益。

该项目通过获取 ZB 网站 OTC 卖单来获取 QC 价格，根据用户的配置进行提醒。

### 使用

```bash
$ git clone git@github.com:AD-feiben/qc-remind.git

$ cd qc-remind

# 创建虚拟环境
$ ./create_venv.sh

# 激活虚拟环境
$ source venv/bin/activate

# 安装依赖
$ pip install -r requirements.txt
```

### 添加配置

```python
# config.py

mail_host = 'email smtp'
# 使用该邮件发送
mail_user = 'your email'
mail_pass = 'your authorization code'

# 用户配置
persons = [
    {
        'email': 'your email',
        # 小于等于该价格，发送提醒
        'lower': 0.992,
        # 大于等于该价格，发送提醒
        'higher': 1,
        # 发送邮件后 N 分钟内不再发送邮件
        'recheck': 5,
        # 收款方式
        'payways': ['银行卡', '微信', '支付宝']
    }
]
```

### 运行 & 停止

```bash
# 运行
$ ./bootstrap.sh start

# 停止
$ ./bootstrap.sh stop
```

### 运行效果

![](./assets/img1.png)