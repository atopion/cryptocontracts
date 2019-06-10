import configparser

configFilePath = './config.ini'

conf = configparser.ConfigParser()
conf.read(configFilePath)


def get(section, key):
	if section not in conf:
		raise KeyError('Section not found: ' + section)
	if key not in conf[section]:
		raise KeyError('Key not found in %s: %s' %(section, key))
	return conf[section][key]


def set(section, key, value):
	if section not in conf:
		conf.add_section(section)
	conf.set(section, key, value)


def save():
	with open(configFilePath, 'w') as configfile:
		conf.write(configfile)
	
