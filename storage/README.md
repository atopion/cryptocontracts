# Storage
Storage controller. Put blocks into / get blocks from the database.
```
from storage import storage

storage.init_chain()
storage.put_block(Transmission(...))

subchain = storage.get_subchain(targetBlockHash) # [ head, ... , target]
storage.print_all()
```


# Config
Project configuration controller.
Loads **"config.ini"** from the project root directory.
```
from storage import config

dbPath = config.get('database', 'path')
```

