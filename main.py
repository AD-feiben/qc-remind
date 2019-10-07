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
        level=logging.INFO,
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
    mail_template = '{}'
finally:
    temp_file_obj.close()


def get_otc_data(params):
    headers = {'content-type': 'application/json',
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'}

    try:
        r = requests.get(config.URL, params=params, headers=headers)
        res = json.loads(r.text)
        return res.get('datas')
    except Exception as e:
        logging.error(e)
        email = config.get('Owner_email')
        if email is not None:
            mail.send_mail(email, '请求异常', str(e))


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
    res_sell = get_otc_data(
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
    )
    res_buy = get_otc_data(
        params = {
            'marketName': 'qc_cny',
            'type': 2,
            'numSort': 1,
            'priceSort': 2,
            'pageIndex': 1,
            'pageSize': 10,
            'amountRange': 0,
            'limitRange': 0
       }
    )

    otc_sell_ads = res_sell.get('list')
    otc_buy_ads = res_buy.get('list')

    otc_ads = []
    if otc_sell_ads is not None:
        otc_ads.extend(otc_sell_ads)
    if otc_buy_ads is not None:
        otc_ads.extend(otc_buy_ads)
    sell_price = ''
    buy_price = ''
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
            ad_type = otc_ad.get('type')

            pay_way_arr = []
            for pw in pay_way.split(','):
                pay_way_arr.append(pay_way_dict[pw])

            # 用户付款方式不为空，且与广告中的付款方式不存在交集，则跳过该广告
            if (person_payways is not None) and (len([val for val in person_payways if val in pay_way_arr]) == 0):
                continue

            if (ad_type == 1 and f_price >= p['higher']) or (ad_type == 2 and f_price <= p['lower']):
                if ad_type == 1 and sell_price == '':
                    sell_price = price
                if ad_type == 2 and buy_price == '':
                    buy_price = price
                mail_content += get_mail_content(otc_ad, pay_way_arr)

        if mail_content != '':
            p['timestamp'] = now
            mail_from = 'QC'
            if buy_price != '':
                mail_from += ' 买入价 {}'.format(buy_price)
            if sell_price != '':
                mail_from += ' 卖出价 {}'.format(sell_price)
            mail.send_mail(p['email'], mail_from, mail_template.format(mail_content), 'html')


if __name__ == '__main__':
    logging.info('*' * 100)
    logging.info('QC-Remind is running')
    logging.info('*' * 100)

    print('*' * 100)
    print('QC-Remind is running')
    print('*' * 100)

    scheduler_config = config.Scheduler
    hour = scheduler_config.get('hour') if scheduler_config.get('hour') is not None else '8-23'
    minute = scheduler_config.get('minute') if scheduler_config.get('minute') is not None else '*/1'

    scheduler = BlockingScheduler()
    scheduler.add_job(task, 'cron', hour=hour, minute=minute)
    try:
        scheduler.start()
    except Exception as e:
        print('*' * 100)
        print('QC-Remind was stop')
        print('*' * 100)
