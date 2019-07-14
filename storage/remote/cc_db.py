import mysql.connector as mysql
import config

def exec(query, params=None):
	conn = mysql.connect(host=config.get('db.host'), user=config.get('db.user'), password=config.get('db.pass'), database=config.get('db.name'))
	c = conn.cursor()
	c.execute(query, params)
	if query.startswith('select'):
		data = c.fetchall()
		c.close()
		conn.close()
		return data
	else:
		conn.commit()
		c.close()
		conn.close()

