from storage import config
import requests
import json

server_addr = config.get('ip-server', 'addr')

def _raise_exception(response):
	raise Exception('%i: %s' %(response.status_code, response.text))

def add_self(port):
	r = requests.post(server_addr, json={'port': port})
	if r.status_code != 200:
		_raise_exception(r)

def add_self_internal(ip, port):
	r = requests.post(server_addr + 'internal', json={'ip': ip, 'port': port})
	if r.status_code != 200:
		_raise_exception(r)

def get_all():
	r = requests.get(server_addr)
	if r.status_code != 200:
		_raise_exception(r)
	return json.loads(r.text)

def delete(ip):
	r = requests.delete(server_addr, json={'ip': ip})
	if r.status_code != 200:
		_raise_exception(r)

def delete_all():
	r = requests.delete(server_addr)
	if r.status_code != 200:
		_raise_exception(r)

