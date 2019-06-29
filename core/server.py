
from storage import storage
from core import core
from core.transmission import Transmission

class Server:
    # Dummy TODO

    def __init__(self):
        # Dummy implementation, to be replaced by calls to the actual network script
        self.server = "A server ..."
        head = storage.get_head()
        # connect to network, retrieve latest graph
        # now wait for transmissions from clients, verify them and append them to local chain

    def got_transmission(self, transmission: Transmission):
        # don't resend if transmission is already in graph

        if storage.block_exists(transmission.transmission_hash):
            return


        if not core.verifyTransmission(transmission):
            # send REFUSE package to network
            return

        # check if previous hash is correct
        if not core.compare(transmission.previous_hash, self.graph[-1].transmission_hash):
            # maybe the graph is not the latest version. Get latest graph and try again
            # getLatestGraph()
            if not core.compare(transmission.previous_hash, self.graph[-1].transmission_hash):
                # send REFUSE package to network
                return

        storage.put_block(transmission)

        # send SUCCESS package to network
        # send the transmission to all known peers in network
