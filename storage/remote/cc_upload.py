from flask import Blueprint, request, Response, jsonify, abort
from werkzeug.utils import secure_filename
from functools import wraps
from base64 import b64encode

import config

cc_upload = Blueprint('cc_upload', __name__, template_folder='templates')

basicAuth = 'Basic ' + b64encode(bytes(config.get('cryptocontracts.user') + ':' + config.get('cryptocontracts.pw'), "ascii")).decode('ascii')


def auth_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if request.headers.get('Authorization') is not None and request.headers.get('Authorization') == basicAuth:
			return f(*args, **kwargs)
		abort(401)
	return wrap

# upload for tests
@cc_upload.route('/', methods=['PUT'])
@auth_required
def upload():
	f = request.files['file']
	f.save(config.get('cryptocontracts.file_upload_dir') + secure_filename(f.filename))
	return Response('ok\n', status=200, mimetype='text/plain')

