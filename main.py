import config
import requests
import json
import logging
from utils import mail
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

persons = config.persons


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


def task():
    res = get_otc_data()
    if res is None:
        return

    otc_ad = res.get('list')[0]
    price = otc_ad.get('price')
    min_money = otc_ad.get('minMoney')
    max_money = otc_ad.get('maxMoney')
    nick_name = otc_ad.get('nickName')
    remain_amount = otc_ad.get('remainAmount')
    f_price = float(price)

    remind = '【QC-Remind】当前 QC 价格：{}, 商家：{}, 最低成交：{}, 最高成交：{}, 剩余：{}'\
        .format(price, nick_name, min_money, max_money, remain_amount)

    for p in persons:
        if f_price >= p['higher'] or f_price <= p['lower']:
            now = datetime.now().timestamp()
            if (p.get('timestamp') is None) or (now - p.get('timestamp') > p.get('recheck') * 60):
                p['timestamp'] = now
                mail.send_mail(p['email'], 'QC 价格 {}'.format(price), remind)


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(task, 'cron', hour='8-23', minute='*/1')
    try:
        scheduler.start()
    except Exception as e:
        pass
