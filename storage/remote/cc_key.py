from flask import Blueprint, request, Response, jsonify, abort
from functools import wraps
from base64 import b64encode
import mysql.connector as mysql

import cc_db as db
import config

cc_key = Blueprint('cc_key', __name__, template_folder='templates')

basicAuth = 'Basic ' + b64encode(bytes(config.get('cryptocontracts.user') + ':' + config.get('cryptocontracts.pw'), "ascii")).decode('ascii')

db.exec('create table if not exists pkeys (id text, created datetime, pkey varchar(2000), primary key(pkey));')


def auth_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if request.headers.get('Authorization') is not None and request.headers.get('Authorization') == basicAuth:
			return f(*args, **kwargs)
		abort(401)
	return wrap


@cc_key.route('/', methods=['POST'])
@auth_required
def post():
	try:
		db.exec('insert into pkeys (id, created, pkey) values (%s, NOW(), %s);', (request.json['id'], request.json['key']))
		return Response('ok\n', status=200, mimetype='text/plain')
	except mysql.Error as e:
		return Response('Error: {}\n'.format(e), status=500, mimetype='text/plain')

@cc_key.route('/', methods=['GET'])
@auth_required
def get():
	try:
		res = db.exec('select id, created, pkey from pkeys where pkey=%s;', (request.json['key'],))
		if res == []:
			return Response('key not found\n', status=404, mimetype='text/plain')
		rid, rcreated, rkey = res[0]
		result = {'id': rid, 'created': rcreated, 'key': rkey}
		return jsonify(result)
	except mysql.Error as e:
		return Response('Error: {}\n'.format(e), status=500, mimetype='text/plain')

@cc_key.route('/', methods=['DELETE'])
@auth_required
def delete():
	try:
		db.exec('delete from pkeys where pkey=%s;', (request.json['key'],))
		return Response('ok\n', status=200, mimetype='text/plain')
	except mysql.Error as e:
		return Response('Error: {}\n'.format(e), status=500, mimetype='text/plain')


@cc_key.route('/all', methods=['GET'])
@auth_required
def get_all():
	try:
		result = [{'id': i[0], 'created': i[1], 'key': i[2]} for i in db.exec('select id, created, pkey from pkeys;')]
		return jsonify(result)
	except mysql.Error as e:
		return Response('Error: {}\n'.format(e), status=500, mimetype='text/plain')

@cc_key.route('/all', methods=['DELETE'])
@auth_required
def delete_all():
	try:
		db.exec('delete from pkeys;')
		return Response('ok\n', status=200, mimetype='text/plain')
	except mysql.Error as e:
		return Response('Error: {}\n'.format(e), status=500, mimetype='text/plain')

