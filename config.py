import os

URL = 'https://vip.zb.plus/api/web/otc/V1_0_0/getOnlineAdList'

Env_mail_host = os.environ['mail_host']
Env_mail_user = os.environ['mail_user']
Env_mail_pass = os.environ['mail_pass']

Mail_host = Env_mail_host if Env_mail_host is not None else ''
Mail_user = Env_mail_user if Env_mail_user is not None else ''
Mail_pass = Env_mail_pass if Env_mail_pass is not None else ''

Persons = [
    {
        'email': Mail_user,
        # 小于等于该价格，发送提醒
        'lower': 0.992,
        # 大于等于该价格，发送提醒
        'higher': 0.998,
        # 发送邮件后 N 分钟内不再发送邮件
        'recheck': 5,
        # 收款方式
        'payways': ['银行卡', '微信', '支付宝']
    }
]


