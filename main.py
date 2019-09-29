import config
import requests
import json
import logging
from utils import mail
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--log-file-prefix', help='log-file-prefix 日志文件名')
args = parser.parse_args()

if args.log_file_prefix is not None:
    logging.basicConfig(
        level=logging.WARNING,
        filename=args.log_file_prefix,
        filemode='a',
        format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
    )
persons = config.Persons

mail_content = '''
<div style="padding: 10px 20px;border-bottom: 1px solid rgba(0, 0, 0, .1);">
    <p>
      {authentication}商家：{nickName}
    </p>
    <p>
      价格：{price}
    </p>
    <p>
      交易限额：{minMoney} - {maxMoney}
    </p>
    <p>
      数量：{remainAmount}
    </p>
    <p>
      支付方式：{payways}
    </p>
    
    <p>
      备注：{remark}
    </p>

</div>
'''

pay_way_dict = {
    '1': '银行卡',
    '2': '微信',
    '3': '支付宝'
}

temp_file_obj = open('template/index.html')
try:
    mail_template = temp_file_obj.read()
except Exception as e:
    logging.error(e)
    mail_template = ''
finally:
    temp_file_obj.close()


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
    r = requests.get(config.URL, params=params, headers=headers)
    try:
        res = json.loads(r.text)
        return res.get('datas')
    except Exception as e:
        logging.error(e)


def get_mail_content(otc_ad, pay_way_arr):
    params = otc_ad
    nick_name = otc_ad.get('nickName')
    user_type = otc_ad.get('userType')

    params['authentication'] = ''
    params['payways'] = '， '.join(pay_way_arr)

    if user_type == 3:
        params['nickName'] = '<b style="color: #e71f19">{}</b>'.format(nick_name)
        params['authentication'] = '认证'
    return mail_content.format(**params)


def task():
    res = get_otc_data()
    if res is None:
        return

    otc_ads = res.get('list')
    max_price = ''
    now = datetime.now().timestamp()

    for p in persons:
        mail_content = ''
        person_payways = p.get('payways')
        person_timestamp = p.get('timestamp')

        # 距离上次发送邮件的时间，小于设置的时间，则跳过提醒
        if (person_timestamp is not None) and (now - person_timestamp < p.get('recheck') * 60):
            continue

        for otc_ad in otc_ads:
            pay_way = otc_ad.get('payWay')
            price = otc_ad.get('price')
            f_price = float(price)

            pay_way_arr = []
            for pw in pay_way.split(','):
                pay_way_arr.append(pay_way_dict[pw])

            # 用户付款方式不为空，且与广告中的付款方式不存在交集，则跳过该广告
            if (person_payways is not None) and (len([val for val in person_payways if val in pay_way_arr]) == 0):
                continue

            if f_price >= p['higher'] or f_price <= p['lower']:
                if max_price == '':
                    max_price = price
                mail_content += get_mail_content(otc_ad, pay_way_arr)

        if mail_content != '':
            p['timestamp'] = now
            mail.send_mail(p['email'], 'QC 价格 {}'.format(max_price), mail_template.format(mail_content), 'html')


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(task, 'cron', hour='8-23', minute='*/1')
    try:
        scheduler.start()
    except Exception as e:
        pass
