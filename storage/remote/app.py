from flask import Flask

from cc_key import cc_key
from cc_ip import cc_ip
from cc_upload import cc_upload

app = Flask(__name__)

app.register_blueprint(cc_key, url_prefix='/cryptocontracts/key')
app.register_blueprint(cc_ip, url_prefix='/cryptocontracts/ip')
app.register_blueprint(cc_upload, url_prefix='/cryptocontracts/upload')

