import random
import os
import time
import json
import requests

import storage.storage
from core.CryptoHashes import CryptoHashes


class Transmission:

    def __init__(self):
        self.previous_hash:str = ""
        self.timestamp:str = ""
        self.pub_keys:list = []
        self.hash:str = ""
        self.signed_hash:str = ""
        self.transmission_hash:str = ""

    def sign_self(self):
        prev = bytearray(self.previous_hash, "utf-8")
        time = bytearray(self.timestamp, "utf-8")
        pubs = bytearray("".join(self.pub_keys), "utf-8")
        hash = bytearray(self.hash, "utf-8")
        sign = bytearray(self.signed_hash, "utf-8")
        comb = prev + time + pubs + hash + sign
        self.transmission_hash = CryptoHashes.sha3_512(comb)

    def check_self(self):
        prev = bytearray(self.previous_hash, "utf-8")
        time = bytearray(self.timestamp, "utf-8")
        pubs = bytearray("".join(self.pub_keys), "utf-8")
        hash = bytearray(self.hash, "utf-8")
        sign = bytearray(self.signed_hash, "utf-8")
        comb = prev + time + pubs + hash + sign
        own_hash = CryptoHashes.sha3_512(comb)
        return Core.compare(own_hash, self.transmission_hash)

    def to_json(self):
        x = {
            "previous_hash" : self.previous_hash,
            "timestamp" : self.timestamp,
            "pub_keys" : self.pub_keys,
            "hash" : self.hash,
            "signed_hash" : self.signed_hash,
            "transmission_hash" : self.transmission_hash
        }
        return json.dumps(x)

    @staticmethod
    def from_json(json_str: str):
        x = json.loads(json_str)
        transmission = Transmission()
        transmission.previous_hash = x["previous_hash"]
        transmission.timestamp = x["timestamp"]
        transmission.pub_keys = x["pub_keys"]
        transmission.hash = x["hash"]
        transmission.signed_hash = x["hash"]
        transmission.transmission_hash = x["transmission_hash"]
        return transmission

    def is_valid(self):
        if self.previous_hash is None or self.previous_hash == "":
            return False
        if self.pub_keys is None or len(self.pub_keys) == 0:
            return False
        if self.hash is None or self.hash == "":
            return False
        if self.signed_hash is None or self.signed_hash == "":
            return False
        if self.transmission_hash is None or self.transmission_hash == "":
            return False
        return True

    def compare(self, transmission):
        return self.previous_hash == transmission.previous_hash and self.timestamp == transmission.timestamp and \
            self.pub_keys == transmission.pub_keys and self.hash == transmission.hash and self.signed_hash == transmission.signed_hash and \
            self.transmission_hash == transmission.transmission_hash


class Signing:
    # Dummy

    @staticmethod
    def sign(value, keys):
        return ""

    @staticmethod
    def unsign(value, keys):
        return ""


class Server:
    # Dummy TODO

    def __init__(self):
        # Dummy implementation, to be replaced by calls to the actual network script
        self.server = "A server ..."
        head = storage.storage.get_head()
        # connect to network, retrieve latest graph
        # now wait for transmissions from clients, verify them and append them to local chain

    def got_transmission(self, transmission: Transmission):
        # don't resend if transmission is already in graph

        if storage.storage.exists(transmission.transmission_hash):
            return


        if not Core.verifyTransmission(transmission):
            # send REFUSE package to network
            return

        # check if previous hash is correct
        if not Core.compare(transmission.previous_hash, self.graph[-1].transmission_hash):
            # maybe the graph is not the latest version. Get latest graph and try again
            # getLatestGraph()
            if not Core.compare(transmission.previous_hash, self.graph[-1].transmission_hash):
                # send REFUSE package to network
                return

        storage.storage.put_block(transmission)

        # send SUCCESS package to network
        # send the transmission to all known peers in network


class Client:
    # Dummy TODO

    def __init__(self):
        # Dummy implementation, to be replaced by calls to the actual network script
        self.server_address = ""

    def place_transmission(self, pub_keys: list, document_hash: str):
        # connect to server and get latest transmission
        latest_transmission = Transmission()

        own_transmission = Core.produceTransmission(latest_transmission.transmission_hash, pub_keys, document_hash)

        # send own_transmission to all known peers



class Core:

    def __init__(self):
        ''' Nothing jet '''

        version = "0.00.2"
        hash_algorithm = "whirlpool|keccak|blake"

        ''' Testing '''
        print( hex(Core.checksum(path="./README.md")) )
        print( hex(Core.checksum(s=open("./README.md", "r").read())))
        print( hex(Core.checksum(bytes=bytearray(open("./README.md", "r").read(), "utf-8"))))

        print("Compare result: ", Core.compare(Core.checksum(path="./README.md"), Core.checksum(bytes=bytearray(open("./README.md", "r").read(), "utf-8"))))

    @staticmethod
    def checksum(path = None, s = None, bytes = None):
        if path is None and bytes is None and s is None:
            return int(random.getrandbits(512))

        if path is not None:
            if not os.path.isfile(path):
                return -1
            file = open(path, "r").read()
            bytes = file.encode("utf-8")

        elif s is not None:
            s = str(s)
            bytes = s.encode("utf-8")
        bytes = bytearray(bytes)

        # Produce checksum
        hexstr = ""
        start_time = time.time()
        hexstr += CryptoHashes.whirlpool(bytes)
        hexstr += CryptoHashes.sha3_512(bytes)
        hexstr += CryptoHashes.blake(bytes)
        print("Execution: ", time.time() - start_time, " s")
        return int(hexstr, 16)


    @staticmethod
    def compare(checksum_a, checksum_b):
        if checksum_a == checksum_b:
            return 1
        else:
            return 0

    @staticmethod
    def lookup(checksum):
        return None

    @staticmethod
    def produceTransmission(previous_hash: str, pub_keys: list, document_hash: str):
        if previous_hash is None or document_hash is None or pub_keys is None or len(pub_keys) == 0:
            return None

        transmission = Transmission()
        transmission.previous_hash = previous_hash
        transmission.timestamp = hex(int(time.time()))[2:]
        transmission.pub_keys = pub_keys
        transmission.hash = document_hash
        transmission.signed_hash = Signing.sign(document_hash, pub_keys)
        transmission.sign_self()
        return transmission

    @staticmethod
    def verifyTransmission(transmission: Transmission):
        if transmission is None or not transmission.is_valid():
            return 0

        if not Core.compare(Signing.unsign(transmission.signed_hash, transmission.pub_keys), transmission.hash):
            return 0

        if not transmission.check_self():
            return 0

        for key in transmission.pub_keys:
            r = requests.get('https://api.zipixx.com/cryptocontracts/', header="Content-Type: application/json", data="{key: " + key + "}")
            if not r.status_code == 200:
                return 0

        return 1


if __name__ == "__main__":
    Core()

