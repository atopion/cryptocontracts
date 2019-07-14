"""import miniupnpc

upnp = miniupnpc.UPnP()
upnp.discoverdelay = 10
upnp.discover()

upnp.selectigd()


def add_port(port: int):
    upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, 'cryptocontracts/1.0', '')

def rm_port(port: int):
    upnp.deleteportmapping(port, 'TCP', upnp.lanaddr)

if __name__ == '__main__':
    print(dir(upnp))
    print("ADDR: ", upnp.lanaddr)
    port = 43210

    # addportmapping(external-port, protocol, internal-host, internal-port, description, remote-host)
    #upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, 'testing', '')
    rm_port(port)"""


import upnpclient
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
internal_ip = s.getsockname()[0]
s.close()

devices = upnpclient.discover()

def add_port(port: int):
    for d in devices:
        d.WANIPConn1.AddPortMapping(
            NewRemoteHost='0.0.0.0',
            NewExternalPort=port,
            NewProtocol='TCP',
            NewInternalPort=port,
            NewInternalClient=internal_ip,
            NewEnabled='1',
            NewPortMappingDescription='cryptocontracts/1.0',
            NewLeaseDuration=10000)

def rm_port(port: int):
    for d in devices:
        d.WANIPConn1.DeletePortMapping(
            NewRemoteHost='0.0.0.0',
            NewExternalPort=port,
            NewProtocol='TCP',
        )