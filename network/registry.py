from storage import config
import requests
import json

server_addr = config.get('registry', 'addr')
server_auth = (config.get('registry', 'user'), config.get('registry', 'pass'))

def _raise_exception(response):
	raise Exception('%i: %s' %(response.status_code, response.text))

def key_exists(key):
	r = requests.get(server_addr, auth=server_auth, json={'key': key})
	if r.status_code == 200:
		return True
	if r.status_code == 404:
		return False
	_raise_exception(r)

def put_key(name, key):
	r = requests.post(server_addr, auth=server_auth, json={'key': key, 'id': name})
	if r.status_code != 200:
		_raise_exception(r)


def get_all():
	r = requests.get(server_addr + 'all', auth=server_auth)
	if r.status_code != 200:
		_raise_exception(r)
	return json.loads(r.text)

def delete_all():
	r = requests.delete(server_addr + 'all', auth=server_auth)
	if r.status_code != 200:
		_raise_exception(r)

