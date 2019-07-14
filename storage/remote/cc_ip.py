from flask import Blueprint, request, Response, jsonify, abort
from functools import wraps
from base64 import b64encode
import mysql.connector as mysql

import cc_db as db

cc_ip = Blueprint('cc_ip', __name__, template_folder='templates')

db.exec('create table if not exists ips (ip varchar(39), port int, joined datetime, primary key(ip));')

#TODO cron timeout

@cc_ip.route('/', methods=['POST'])
def ip_post():
	try:
		if request.json is None or 'port' not in request.json:
			return Response(status=400)

		db.exec('replace into ips (ip, port, joined) values (%s, %s, NOW());', (request.headers['X-Forwarded-For'], request.json['port']))
		return Response('ok\n', status=200, mimetype='text/plain')
	except mysql.Error as e:
		return Response('Error: {}\n'.format(e), status=500, mimetype='text/plain')

@cc_ip.route('/internal', methods=['POST'])
def ip_internal_post():
	try:
		if request.json is None or 'port' not in request.json or 'ip' not in request.json:
			return Response(status=400)

		db.exec('replace into ips (ip, port, joined) values (%s, %s, NOW());', (request.json['ip'], request.json['port']))
		return Response('ok\n', status=200, mimetype='text/plain')
	except mysql.Error as e:
		return Response('Error: {}\n'.format(e), status=500, mimetype='text/plain')

@cc_ip.route('/', methods=['GET'])
def ip_get():
	try:
		result = [{'ip': i[0], 'port': i[1], 'joined': i[2]} for i in db.exec('select ip, port, joined from ips;')]
		return jsonify(result)
	except mysql.Error as e:
		return Response('Error: {}\n'.format(e), status=500, mimetype='text/plain')

# TODO rm deleteall, replace with x-forwarded-for
@cc_ip.route('/', methods=['DELETE'])
def ip_delete():
	try:
		if request.json is not None and 'ip' in request.json:
			db.exec('delete from ips where ip=%s;', (request.json['ip'],))
		else:
			db.exec('delete from ips;') # where ip=?;', (request.headers['X-Forwarded-For'],))
		return Response('ok\n', status=200, mimetype='text/plain')
	except mysql.Error as e:
		return Response('Error: {}\n'.format(e), status=500, mimetype='text/plain')


