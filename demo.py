#!/usr/bin/env python3

from core import core
from storage import storage, config
from network import registry, ip_server

#print('db path: ' + config.get('database','path'))

registry.delete_all()
registry.put_key('myname', 'mykey')
registry.put_key('mynameaswell', 'mykeyaswell')
print('yea') if registry.key_exists('notmykey') else print('no')
print(registry.get_all())

ip_server.delete_all()
port=config.get('server', 'port')
ip_server.add_self(port)
print(ip_server.get_all())



t1 = core.produce_transmission(storage.get_head(), ['key1', 'key2'], 'document1_hash')
storage.put_block(t1)
t2 = core.produce_transmission(storage.get_head(), ['key3', 'key4'], 'document2_hash')
storage.put_block(t2)

#print(storage.get_block(storage.get_head()).to_json())

#subchain = storage.get_subchain(t1.transmission_hash) # [ head, ... , target]
#storage.print_chain(subchain)

storage.print_all()

