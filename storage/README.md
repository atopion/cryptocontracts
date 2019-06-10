# Storage
Storage controller. Put blocks into / get blocks from the database.
```
from storage import storage
from storage.block import Block

storage.init_chain()
storage.put_block(Block('blockId1', ['key1','key2'], 'doc', 'docs', 'ROOT', 'pbs'))
storage.put_block(Block('blockId2', ['key1','key2'], 'doc', 'docs', 'blockId1', 'pbs'))
storage.put_block(Block('blockId3', ['key1','key2'], 'doc', 'docs', 'blockId2', 'pbs'))

newestBlockKeys = storage.get_block(storage.get_head()).keys
subchain = storage.get_subchain('id1') # [ head, ... , target]
storage.print_all()
```


# Config
Project configuration controller.
Loads **"config.ini"** from the project root directory.
```
from storage import config

addr = config.get('ip-server', 'addr')
```

