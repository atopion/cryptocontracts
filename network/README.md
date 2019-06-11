#####First solution for a network. Still based on Server-Client model. For now , Server address has to be given when creating a Client Peer and wanting to connect to the network.

### How to create the server peer for the network:

from network import server_peer

server = server_peer.ServerPeer()

### How to create a client peer for the network:

from network import client_peer

client = client_peer.Peer(*server_address*)
client.connectToNet()
