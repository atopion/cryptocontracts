##### Seems to work for a single computer. Only client_peer.py required, no Server.


### How to create a peer and connect to the network:

from network import client_peer

client = client_peer.Peer()

client.connect_to_net()

#### If a peer is the first one in the network it is going to print his address to a local file and wait for connections. When a second peer is created it checks that file and connects to the first peer. Therefore, it works locally but not yet on different machines

#### All to all connectivity is implemented


