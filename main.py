import config
import requests
import json
import logging

from observe import Observable, Observer
from utils import mail
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

ob_ad_list = Observable()


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


def task():
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
    res_sell = get_otc_data(params)

    params['type'] = 2
    params['priceSort'] = 2

    res_buy = get_otc_data(params)

    otc_sell_ads = res_sell.get('list')
    otc_buy_ads = res_buy.get('list')

    otc_ads = []
    if otc_sell_ads is not None:
        otc_ads.extend(otc_sell_ads)
    if otc_buy_ads is not None:
        otc_ads.extend(otc_buy_ads)
    ob_ad_list.set_ad_list(otc_ads)


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
    gh_range = hour.split('-')
    # 全局配置时间
    ghr0 = int(gh_range[0])
    ghr1 = int(gh_range[1])

    for person in persons:
        if person.get('hour') is None:
            person['hour'] = hour

        # 个人配置时间
        h_range = person['hour'].split('-')
        hr0 = int(h_range[0])
        hr1 = int(h_range[1])

        # 设置时间范围
        ghr0 = max(min(ghr0, hr0), 0)
        ghr1 = min(max(ghr1, hr1), 23)

        observer_person = Observer(**person)
        ob_ad_list.add_observe(observer_person)

    scheduler = BlockingScheduler()
    scheduler.add_job(task, 'cron', hour='{}-{}'.format(ghr0, ghr1), minute=minute)
    try:
        scheduler.start()
    except Exception as e:
        print('*' * 100)
        print('QC-Remind was stop')
        print('*' * 100)
