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

def compare(checksum_a, checksum_b):
    if checksum_a == checksum_b:
        return True
    return False

def lookup(checksum):
	return None

def produceTransmission(previous_hash: str, pub_keys: list, document_hash: str):

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

def verifyTransmission(transmission: Transmission):
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

