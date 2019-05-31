import random
import os
import whirlpool

class Core:

    def __init__(self):
        ''' Nothing jet '''

        version = "0.00.1"
        hash_algorithm = "whirlpool"

        ''' Testing '''
        print( hex(Core.checksum(path="./README.md")) )
        print( hex(Core.checksum(s=open("./README.md", "r").read())))
        print( hex(Core.checksum(bytes=bytearray(open("./README.md", "r").read(), "utf-8"))))

        print("Compare result: ", Core.compare(Core.checksum(path="./README.md"), Core.checksum()))

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

        # Produce checksum
        hexstr = whirlpool.new(bytes).hexdigest()
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


if __name__ == "__main__":
    Core()
