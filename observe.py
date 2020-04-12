import logging
from datetime import datetime

import config
from utils import mail

pay_way_dict = {
	'1': '银行卡',
	'2': '微信',
	'3': '支付宝'
}

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

temp_file_obj = open('template/index.html')
try:
	mail_template = temp_file_obj.read()
except Exception as e:
	logging.error(e)
	mail_template = '{}'
finally:
	temp_file_obj.close()


def get_mail_content(ad, pay_way_arr):
	params = ad
	nick_name = ad.get('nickName')
	user_type = ad.get('userType')

	params['authentication'] = ''
	params['payways'] = '， '.join(pay_way_arr)

	if user_type == 3:
		params['nickName'] = '<b style="color: #e71f19">{}</b>'.format(nick_name)
		params['authentication'] = '认证'
	return mail_content.format(**params)


class Observer(object):
	"""
	监听对象
	email   接收邮件通知的邮箱地址
	lower   市场买入价低于等于该价格时触发通知
	higher  市场卖出价高于等于该价格触发通知
	recheck 发送邮件后 N 分钟内不再发送邮件
	payways 收付款方式
	hour_range    指定时间范围内允许发邮件
	"""

	def __init__(self, *args, **kwargs):
		self.email = kwargs['email']
		self.lower = kwargs.get('lower')
		self.higher = kwargs.get('higher')
		self.recheck = 30 if kwargs.get('recheck') is None else kwargs['recheck']
		self.payways = kwargs.get('payways')
		self.hour_range = kwargs['hour'].split('-')
		self.authentication = False if kwargs.get('isOnlyAuthBusiness') is None else kwargs['isOnlyAuthBusiness']
		self.timestamp = None

	def update(self, ad_list):
		now = datetime.now()
		timestamp = now.timestamp()
		hour = now.hour
		content = ''
		sell_price = ''
		buy_price = ''

		hour_r0 = max(int(self.hour_range[0]), 0)
		hour_r1 = min(int(self.hour_range[1]), 23)

		# 不在允许通知时间范围内
		if hour < hour_r0 or hour > hour_r1:
			return

		# 未达到重新发送邮件时间
		if (self.timestamp is not None) and (timestamp - self.timestamp < self.recheck * 60):
			return

		for ad in ad_list:
			ad_pay_way = ad.get('payWay')
			ad_price = ad.get('price')
			f_ad_price = float(ad_price)
			ad_type = ad.get('type')
			user_type = ad.get('userType')

			if self.authentication is True and user_type != 3:
				continue

			# 将收付款方式转为文字
			pay_way_arr = []
			for pw in ad_pay_way.split(','):
				if pay_way_dict.get(pw) is not None:
					pay_way_arr.append(pay_way_dict[pw])

			# 用户付款方式不为空，且与广告中的付款方式不存在交集，则跳过该广告
			if (self.payways is not None) and (len([val for val in self.payways if val in pay_way_arr]) == 0):
				continue

			if ad_type == 1:
				# 未设置卖出价或价格未匹配
				if self.higher is None or f_ad_price < self.higher:
					continue
				if sell_price == '':
					sell_price = f_ad_price
				content += get_mail_content(ad, pay_way_arr)

			if ad_type == 2:
				# 未设置买入价或价格未匹配
				if self.lower is None or f_ad_price > self.lower:
					continue
				if buy_price == '':
					buy_price = f_ad_price
				content += get_mail_content(ad, pay_way_arr)

		if content != '':
			self.timestamp = timestamp
			mail_from = 'QC'
			if buy_price != '':
				mail_from += ' 买入价 {}'.format(buy_price)
			if sell_price != '':
				mail_from += ' 卖出价 {}'.format(sell_price)
			mail.send_mail(self.email, mail_from, mail_template.format(content), 'html')


class Observable:
	def __init__(self):
		self.__ad_list = None
		self.__ob_list = []

	def add_observe(self, observe: Observer):
		self.__ob_list.append(observe)

	def remove_observe(self, observe: Observer):
		self.__ob_list.remove(observe)

	def set_ad_list(self, ad_list):
		self.__ad_list = ad_list
		self.notify()

	def notify(self):
		for ob in self.__ob_list:
			ob.update(self.__ad_list)
