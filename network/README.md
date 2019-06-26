##### Slightly advanced network model. Right now Server function is still required to establish network but soon there will only be a peer class self-managing the case where there is no server yet.

### How to create the server peer for the network:

from network import server_peer

server = server_peer.ServerPeer()

### How to create a client peer for the network:

from network import client_peer

client = client_peer.Peer(*server_address*)

## After every session the client-peer stores the addresses of the latest active peers in the net. If no server address is specified, the peer tries to connect to one of these nodes

client.connect_to_net()

### Synchronization efforts are integrated in latest network version but not tested yet
