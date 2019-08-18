from core import core, cryptoHashes, signing
import json


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
        self.transmission_hash = cryptoHashes.CryptoHashes.sha3_512(comb)

    def check_self(self):
        prev = bytearray(self.previous_hash, "utf-8")
        time = bytearray(self.timestamp, "utf-8")
        pubs = bytearray("".join(self.pub_keys), "utf-8")
        hash = bytearray(self.hash, "utf-8")
        sign = bytearray(self.signed_hash, "utf-8")
        comb = prev + time + pubs + hash + sign
        own_hash = cryptoHashes.CryptoHashes.sha3_512(comb)
        return core.compare(own_hash, self.transmission_hash)

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

    def get_transmission_hash(self):
        prev = bytearray(self.previous_hash, "utf-8")
        time = bytearray(self.timestamp, "utf-8")
        pubs = bytearray("".join(self.pub_keys), "utf-8")
        hash = bytearray(self.hash, "utf-8")
        sign = bytearray(self.signed_hash, "utf-8")
        comb = prev + time + pubs + hash + sign
        return cryptoHashes.CryptoHashes.sha3_512(comb)

    @staticmethod
    def generate(previous_hash:str, timestamp, pub_keys, hash, signed_hash, transmission_hash):
        transmission = Transmission()
        transmission.previous_hash = previous_hash
        transmission.timestamp = timestamp
        transmission.pub_keys = pub_keys
        transmission.hash = hash
        transmission.signed_hash = signed_hash
        transmission.transmission_hash = transmission_hash
        return transmission

    @staticmethod
    def from_json(json_str: str):
        x = json.loads(json_str)
        transmission = Transmission()
        transmission.previous_hash = x["previous_hash"]
        transmission.timestamp = x["timestamp"]
        transmission.pub_keys = x["pub_keys"]
        transmission.hash = x["hash"]
        transmission.signed_hash = x["signed_hash"]
        transmission.transmission_hash = x["transmission_hash"]
        return transmission

    @staticmethod
    def list_from_json(json_str: str):
        l = json.loads(json_str)
        result = [Transmission.generate(**x) for x in l]
#        print("RESULT: ", result)
        #for entry in l:
        #    print("ENTRY: ", entry)
        #    result.append(Transmission.from_json(entry))
        return result

    @staticmethod
    def list_to_json(l: list):
        xl = []
        for m in l:
            x = {
                "previous_hash": m.previous_hash,
                "timestamp": m.timestamp,
                "pub_keys": m.pub_keys,
                "hash": m.hash,
                "signed_hash": m.signed_hash,
                "transmission_hash": m.transmission_hash
            }
            xl.append(x)
        return json.dumps(xl)

    """
    def unsigned_transmission_hash(self):
        return signing.unsign(self.transmission_hash, self.pub_keys)
    """
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
