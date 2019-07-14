import yaml

conf_f = open('./config.yaml')
conf = yaml.safe_load(conf_f)
conf_f.close()

# search config for key in form 'category.subcategory.var' etc.
def get(key):
    try:
        return _lookup(conf, key)
    except KeyError:
        return None

def _lookup(dct, key):
    if '.' in key:
        key, node = key.split('.', 1)
        return _lookup(dct[key], node)
    else:
        return dct[key]
