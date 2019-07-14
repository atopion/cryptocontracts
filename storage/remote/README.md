# Remote Storage

Flask app with sub-modules for central registry, ip_server and testing-file upload API.
Modify app.py to enable or disable the three sub-apps.

## Requirements
Assumes a working SSL proxy that sets the `X-Forwarded-For` header as well as a mysql/mariadb server setup.
Fill in the database & registry authorization data + the upload path in the config.yaml file.

