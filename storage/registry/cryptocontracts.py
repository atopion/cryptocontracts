from flask import Blueprint, request, Response, jsonify, abort
from functools import wraps
from base64 import b64encode
import yaml
import sqlite3

cryptocontracts = Blueprint('cryptocontracts', __name__, template_folder='templates')

conf_f = open('/app/config.yaml')
conf = yaml.safe_load(conf_f)
conf_f.close()

basicAuth = 'Basic ' + b64encode(bytes(conf['data']['cryptocontracts']['user'] + ':' + conf['data']['cryptocontracts']['pw'], "ascii")).decode('ascii')
dbFilename='/db.sqlite3'


#TODO split modules, build standalone base-app

#sqlite doesn't multi-thread between db and cursors -> recreate connection on request on every route
db = sqlite3.connect(dbFilename)
c = db.cursor()
c.execute('create table if not exists keys (id text, created datetime, key text primary key);')
c.execute('create table if not exists ips (ip text primary key, port text, joined datetime);')
db.commit()
c.close()
db.close()


def auth_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if request.headers.get('Authorization') is not None and request.headers.get('Authorization') == basicAuth:
			return f(*args, **kwargs)
		abort(401)
	return wrap


@cryptocontracts.route('/', methods=['POST'])
@auth_required
def post():
	try:
		db = sqlite3.connect(dbFilename)
		c = db.cursor()
		c.execute('insert into keys (id, created, key) values (?, datetime("now"), ?);', (request.json['id'], request.json['key']))
		db.commit()
		c.close()
		db.close()
		return Response('ok\n', status=200, mimetype='text/plain')
		
	except sqlite3.Error as e:
		return Response(str(e)+'\n', status=500, mimetype='text/plain')

@cryptocontracts.route('/', methods=['GET'])
@auth_required
def get():
	try:
		db = sqlite3.connect(dbFilename)
		c = db.cursor()
		c.execute('select id, created, key from keys where key=?;', (request.json['key'],))
		rid, rcreated, rkey = c.fetchone()
		result = {'id': rid, 'created': rcreated, 'key': rkey}
		c.close()
		db.close()
		return jsonify(result)
	except sqlite3.Error as e:
		return Response(str(e)+'\n', status=500, mimetype='text/plain')

@cryptocontracts.route('/', methods=['DELETE'])
@auth_required
def delete():
	try:
		db = sqlite3.connect(dbFilename)
		c = db.cursor()
		c.execute('delete from keys where key=?;', (request.json['key'],))
		db.commit()
		c.close()
		db.close()
		return Response('ok\n', status=200, mimetype='text/plain')
	except sqlite3.Error as e:
		return Response(str(e)+'\n', status=500, mimetype='text/plain')



@cryptocontracts.route('/all', methods=['GET'])
@auth_required
def get_all():
	try:
		db = sqlite3.connect(dbFilename)
		c = db.cursor()
		c.execute('select id, created, key from keys;')
		result = [{'id': i[0], 'created': i[1], 'key': i[2]} for i in c.fetchall()]
		c.close()
		db.close()
		return jsonify(result)
	except sqlite3.Error as e:
		return Response(str(e)+'\n', status=500, mimetype='text/plain')

@cryptocontracts.route('/all', methods=['DELETE'])
@auth_required
def delete_all():
	try:
		db = sqlite3.connect(dbFilename)
		c = db.cursor()
		c.execute('delete from keys;')
		db.commit()
		c.close()
		db.close()
		return Response('ok\n', status=200, mimetype='text/plain')
	except sqlite3.Error as e:
		return Response(str(e)+'\n', status=500, mimetype='text/plain')




#========== IP ================

#TODO cron timeout


@cryptocontracts.route('/ip', methods=['POST'])
@auth_required
def ip_post():
	try:
		if request.args.get('port') is None:
			return Response('', status=400)

		db = sqlite3.connect(dbFilename)
		c = db.cursor()
		c.execute('insert or replace into ips (ip, port, joined) values (?, ?, datetime("now"));', (request.headers['X-Forwarded-For'], request.args.get('port')))
		db.commit()
		c.close()
		db.close()
		return Response('ok\n', status=200, mimetype='text/plain')
		
	except sqlite3.Error as e:
		return Response(str(e)+'\n', status=500, mimetype='text/plain')

@cryptocontracts.route('/ip', methods=['GET'])
@auth_required
def ip_get():
	try:
		db = sqlite3.connect(dbFilename)
		c = db.cursor()
		c.execute('select ip, port, joined from ips;')
		result = [{'ip': i[0], 'port': i[1], 'joined': i[2]} for i in c.fetchall()]
		c.close()
		db.close()
		return jsonify(result)
	except sqlite3.Error as e:
		return Response(str(e)+'\n', status=500, mimetype='text/plain')

@cryptocontracts.route('/ip', methods=['DELETE'])
@auth_required
def ip_delete():
	try:
		db = sqlite3.connect(dbFilename)
		c = db.cursor()
		c.execute('delete from ips;') # where ip=?;', (request.headers['X-Forwarded-For'],))
		db.commit()
		c.close()
		db.close()
		return Response('ok\n', status=200, mimetype='text/plain')
	except sqlite3.Error as e:
		return Response(str(e)+'\n', status=500, mimetype='text/plain')



