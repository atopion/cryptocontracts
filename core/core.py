import random
import os
import time

from core.cryptoHashes import CryptoHashes

from core import core, signing
from core.transmission import Transmission
from network import registry

''' Nothing jet

version = "0.00.2"
hash_algorithm = "whirlpool|keccak|blake"

' Testing
print( hex(Core.checksum(path="./README.md")) )
print( hex(Core.checksum(s=open("./README.md", "r").read())))
print( hex(Core.checksum(bytes=bytearray(open("./README.md", "r").read(), "utf-8"))))

print("Compare result: ", Core.compare(Core.checksum(path="./README.md"), Core.checksum(bytes=bytearray(open("./README.md", "r").read(), "utf-8"))))
'''


def checksum(path = None, s = None, byte = None):
    if path is None and byte is None and s is None:
        raise ValueError('No input given.')

    if path is not None:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        print("core.checksum :: read bytes from file " + path)
        byte = open(path, "rb").read()

    elif s is not None:
        s = str(s)
        byte = s.encode("utf-8")

    byte = bytearray(byte)

    # Produce checksum
    hexstr = ""
    start_time = time.time()
    hexstr += CryptoHashes.whirlpool(byte)
    hexstr += CryptoHashes.sha3_512(byte)
    #hexstr += CryptoHashes.blake(byte)
    print("Execution: ", time.time() - start_time, " s")
    return int(hexstr, 16)


def compare(checksum_a, checksum_b):
    if checksum_a == checksum_b:
        return True
    return False


def lookup(checksum): return None


def produce_transmission(previous_hash: str, pub_keys: list, document_hash: str):
    if previous_hash is None or document_hash is None or pub_keys is None or len(pub_keys) == 0:
        return None

    transmission = Transmission()
    transmission.previous_hash = previous_hash
    transmission.timestamp = hex(int(time.time()))[2:]
    transmission.pub_keys = pub_keys
    transmission.hash = document_hash
    transmission.signed_hash = signing.sign(document_hash, pub_keys)
    transmission.sign_self()
    return transmission


def verify_transmission(transmission: Transmission):
    if transmission is None or not transmission.is_valid():
        return False

    if not compare(signing.unsign(transmission.signed_hash, transmission.pub_keys), transmission.hash):
        return False

    if not transmission.check_self():
        return False

    #for key in transmission.pub_keys:
    #    if not registry.key_exists(key):
    #        return False

    return True

