
url = 'https://vip.zb.plus/api/web/otc/V1_0_0/getOnlineAdList'

mail_host = ''
mail_user = ''
mail_pass = ''

persons = [
    {
        'email': '',
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


