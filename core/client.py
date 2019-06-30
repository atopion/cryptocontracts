from core import core
from core.transmission import Transmission


class Client:
    # Dummy TODO

    def __init__(self):
        # Dummy implementation, to be replaced by calls to the actual network script
        self.server_address = ""

    def place_transmission(self, pub_keys: list, document_hash: str):
        # connect to server and get latest transmission
        latest_transmission = Transmission()

        own_transmission = core.produceTransmission(latest_transmission.transmission_hash, pub_keys, document_hash)

        # send own_transmission to all known peers
