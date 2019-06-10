# Registry
Flask blueprint for a central registry API for public keys and IP list server for network-joining.


Headers where necessary:
`Content-Type: application/json`
`Authorization: Basic $login`

Usage Example:
```
#!/usr/bin/env bash

# key-server endpoint data
#auth=""
#baseUrl=""
header='Content-Type: application/json'

# id register
curl -X DELETE -u $auth "${baseUrl}all"
curl -X POST -H "$header" -u $auth "$baseUrl" -d '{"id": "i1", "key": "k1"}'
curl -X POST -H "$header" -u $auth "$baseUrl" -d '{"id": "i2", "key": "k2"}'
curl -X POST -H "$header" -u $auth "$baseUrl" -d '{"id": "i3", "key": "k3"}'
curl -X GET -H "$header" -u $auth "$baseUrl" -d '{"key": "k2"}'
curl -X DELETE -H "$header" -u $auth "$baseUrl" -d '{"key": "k2"}'
curl -X GET -u $auth "${baseUrl}all"

# ip register
curl -X DELETE -u $auth "${baseUrl}ip"
curl -X POST -u $auth "${baseUrl}ip?port=9000"
curl -X POST -u $auth "${baseUrl}ip?port=9001"
curl -X GET -u $auth "${baseUrl}ip"
```

