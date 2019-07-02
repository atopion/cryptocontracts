import configparser

import os.path

configFilePath = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../config.ini')

conf = configparser.ConfigParser()
if(len(conf.read(configFilePath)) != 1):
	raise FileNotFoundError('Config file missing: ' + configFilePath)


# TODO move env overrides here

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
	
