import config
import requests
import json
from utils import mail
import logging


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
        return res['datas']
    except Exception as e:
        logging.error(e)


def task():
    res = get_otc_data()
    if res is not None:
        otc_ad = res['list'][0]
        price = otc_ad['price']
        min_money = otc_ad['minMoney']
        max_money = otc_ad['maxMoney']
        nick_name = otc_ad['nickName']
        remain_amount = otc_ad['remainAmount']
        f_price = float(price)

    remind = '【QC-Remind】当前 QC 价格：{}, 商家：{}, 最低成交：{}, 最高成交：{}, 剩余：{}'\
        .format(price, nick_name, min_money, max_money, remain_amount)

    for p in config.persons:
        if f_price >= p['higher'] or f_price <= p['lower']:
            mail.send_mail(p['email'], 'QC 价格 {}'.format(price), remind)


if __name__ == '__main__':
    task()
