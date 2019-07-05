from storage import config
import requests
import json

reg_addr = config.get('ip-server', 'addr')
reg_auth = (config.get('ip-server', 'user'), config.get('ip-server', 'pass'))

def _raise_exception(response):
	raise Exception('%i: %s' %(response.status_code, response.text))

def add_self(port):
	r = requests.post(reg_addr, auth=reg_auth, json={'port': port})
	if r.status_code != 200:
		_raise_exception(r)

def add_self_internal(ip, port):
	r = requests.post(reg_addr + '_internal', auth=reg_auth, json={'ip': ip, 'port': port})
	if r.status_code != 200:
		_raise_exception(r)

def get_all():
	r = requests.get(reg_addr, auth=reg_auth)
	if r.status_code != 200:
		_raise_exception(r)
	return json.loads(r.text)

def delete_all():
	r = requests.delete(reg_addr, auth=reg_auth)
	if r.status_code != 200:
		_raise_exception(r)

