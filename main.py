import config
import requests
import json
import logging
from utils import mail
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler


logging.basicConfig(
    level=logging.ERROR,
    filename='qc-remind.log',
    filemode='a',
    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
)
persons = config.persons

mail_content = '''
<div style="padding: 10px 20px;border-bottom: 1px solid rgba(0, 0, 0, .1);">
    <p>
      {authentication}商家：{nick_name}
    </p>
    <p>
      价格：{price}
    </p>
    <p>
      交易限额：{min_money} - {max_money}
    </p>
    <p>
      数量：{remain_amount}
    </p>
    <p>
      支付方式：{payways}
    </p>
    
    <p>
      备注：{remark}
    </p>

</div>
'''


def get_otc_data():
    headers = {'content-type': 'application/json',
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'}
    params = {
        'marketName': 'qc_cny',
        'type': 1,
        'numSort': 1,
        'priceSort': 1,
        'pageIndex': 1,
        'pageSize': 10,
        'amountRange': 0,
        'limitRange': 0
    }
    r = requests.get(config.url, params=params, headers=headers)
    try:
        res = json.loads(r.text)
        return res.get('datas')
    except Exception as e:
        logging.error(e)


def get_mail_content(otc_ad, pay_way_arr):
    price = otc_ad.get('price')
    min_money = otc_ad.get('minMoney')
    max_money = otc_ad.get('maxMoney')
    nick_name = otc_ad.get('nickName')
    remain_amount = otc_ad.get('remainAmount')
    remark = otc_ad.get('remark')
    user_type = otc_ad.get('userType')

    authentication = ''

    if user_type == 3:
        nick_name = '<b style="color: #e71f19">{}</b>'.format(nick_name)
        authentication = '认证'
    return mail_content.format(
        authentication=authentication,
        nick_name=nick_name,
        price=price,
        min_money=min_money,
        max_money=max_money,
        remain_amount=remain_amount,
        payways='， '.join(pay_way_arr),
        remark=remark
    )


def send_mail(email, mail_content, price):
    temp_file_obj = open('template/index.html')
    try:
        mail_template = temp_file_obj.read()
        mail.send_mail(
            email,
            'QC 价格 {}'.format(price),
            mail_template.format(mail_content),
            'html')
    except Exception as e:
        logging.error(e)
    finally:
        temp_file_obj.close()


def task():
    res = get_otc_data()
    if res is None:
        return

    otc_ads = res.get('list')
    for p in persons:
        mail_content = ''
        max_price = otc_ads[0].get('price')
        payways = p.get('payways')

        for otc_ad in otc_ads:
            pay_way = otc_ad.get('payWay')
            f_price = float(otc_ad.get('price'))

            pay_way_dict = {
                '1': '银行卡',
                '2': '微信',
                '3': '支付宝'
            }
            pay_way_arr = []
            for pw in pay_way.split(','):
                pay_way_arr.append(pay_way_dict[pw])

            if (payways is not None) and (len([val for val in payways if val in pay_way_arr]) == 0):
                continue
            if f_price >= p['higher'] or f_price <= p['lower']:
                now = datetime.now().timestamp()
                if (p.get('timestamp') is None) or (now - p.get('timestamp') > p.get('recheck') * 60):
                    mail_content += get_mail_content(otc_ad, pay_way_arr)

        p['timestamp'] = now
        send_mail(p['email'], mail_content, max_price)


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(task, 'cron', hour='8-23', minute='*/1')
    try:
        scheduler.start()
    except Exception as e:
        pass
