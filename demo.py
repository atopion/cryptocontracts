from core.core import Core
from storage import storage, config

#print('db path: ' + config.get('database','path'))

storage.init_chain()

t1 = Core.produceTransmission(storage.get_head(), ['key1','key2'], 'document1_hash')
storage.put_block(t1)
t2 = Core.produceTransmission(storage.get_head(), ['key3','key4'], 'document2_hash')
storage.put_block(t2)

#print(storage.get_block(storage.get_head()).to_json())

subchain = storage.get_subchain(t1.transmission_hash) # [ head, ... , target]
storage.print_chain(subchain)

#storage.print_all()

