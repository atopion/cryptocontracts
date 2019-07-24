import random
import os
import time
import datetime

from requests import get

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

def logging_date():
    t = datetime.datetime.now()
    return "[" + str(t.year) + "-" + str(t.month) + "-" + str(t.day) + " " + str(t.hour) + ":" + str(t.minute) +\
        ":" + str(t.second) + ":" + str(t.microsecond) + "] "


# Network log
external_ip = get('http://atopion.com/apps/helper/ip.php').text
network_file = open("network-log.txt", "a")
network_file.write("\n\n\t\tNew Log instance started at " + logging_date() + " at IP " + external_ip)
network_file.flush()


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
    hexstr += CryptoHashes.blake(byte)
    print("Produce checksum execution: ", time.time() - start_time, " s")
    return int(hexstr, 16)


def compare(checksum_a, checksum_b):
    print("A", checksum_a)
    print("B", checksum_b)
    if checksum_a == checksum_b:
        return True
    return False


def lookup(checksum): return None


def produce_transmission_fully(previous_hash: str, private_keys: list, pub_keys: list, document_hash: str):
    if previous_hash is None or document_hash is None or pub_keys is None or len(pub_keys) == 0:
        return None

    transmission = Transmission()
    transmission.previous_hash = previous_hash
    transmission.timestamp = hex(int(time.time()))[2:]
    transmission.pub_keys = pub_keys
    transmission.hash = document_hash
    transmission.signed_hash = signing.sign(document_hash, private_keys)
    transmission.sign_self()
    transmission.transmission_hash = signing.sign(transmission.transmission_hash, private_keys)
    return transmission


def produce_transmission_stage_one(private_key: str, public_key: str, document_hash: str = None, transmission: Transmission = None):
    """
    Produces a temporary transmission object or signs an existing one.
    :param private_key: Private Key of the signing entity
    :param public_key: Public Key of the signing entity
    :param document_hash: Checksum of the document or None if signing an existing transmission
    :param transmission: An existing transmission or None if signing a new one.
    :return: None if document_hash and transmission are both None or not None. A new temporary transmission object otherwise.
    """

    if (document_hash is None and transmission is None) or (document_hash is not None and transmission is not None):
        return None

    if document_hash is None:
        transmission.pub_keys.append(public_key)
        transmission.signed_hash = signing.sign(transmission.signed_hash, private_key)
        return transmission

    else:
        transmission = Transmission()
        transmission.pub_keys = [public_key]
        transmission.hash = document_hash
        transmission.signed_hash = signing.sign(document_hash, private_key)
        return transmission


def produce_transmission_stage_two(private_key: str, transmission: Transmission, previous_hash: str = None, master: bool = True):
    """
    Finishes a temporary transmission object or signs a finished one.
    :param private_key: Private Key of the signing entity
    :param previous_hash: Hash of previous block
    :param public_key: Public Key of the signing entity
    :param transmission: An existing transmission or None if signing a new one.
    :param master: Determines if the unit is a master unit (sets previous hash, timestamp and transmission_hash)
    :return: None if document_hash and transmission are both None or not None. A new temporary transmission object otherwise.
    """

    if master:
        transmission.previous_hash = previous_hash
        transmission.timestamp = hex(int(time.time()))[2:]
        transmission.sign_self()
        transmission.transmission_hash = signing.sign(transmission.transmission_hash, private_key)

    else:
        transmission.transmission_hash = signing.sign(transmission.transmission_hash, private_key)

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

def network_log(*argv):
    text = ""
    for arg in argv:
        text += str(arg)

    network_file.write(logging_date() + " " + external_ip + ": " + text)
