import core.core
import sys

"""
Old initial

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if str(arg).lower() == "client":
            if len(sys.argv) > 2:
                addr = sys.argv[2]
                core.core.Client(addr)
            else:
                core.core.Client()
        elif str(arg).lower() == "server":
            core.core.Server()
        else:
            core.core.Server()
    else:
        core.core.Server()
"""

if __name__ == '__main__':
    if not len(sys.argv) == 4:
        print("Wrong number of arguments")
        sys.exit(1)

    mode = sys.argv[1]
    try:
        test = int(sys.argv[2])
        unit = int(sys.argv[3])
    except ValueError:
        print("Irregular arguments (no integers)")
        sys.exit(1)

    core.core.storage.init_chain()
    prev = core.core.storage.get_block(core.core.storage.get_head())
    t1 = core.core.Core.produceTransmission(prev.transmission_hash, ["a", "b"], "document-1")
    t2 = core.core.Core.produceTransmission(t1.transmission_hash, ["c", "d"], "document-2")
    t3 = core.core.Core.produceTransmission(t2.transmission_hash, ["e", "f"], "document-3")

    if mode == "server":
        core.core.Server()

    elif mode == "client":
        if  test == 1:
            if unit == 1:
                core.core.storage.put_block(t1)
            else:
                core.core.storage.put_block(t1)
                core.core.storage.put_block(t2)

        elif test == 2:
            if test < 100:
                core.core.storage.put_block(t1)
            else:
                core.core.storage.put_block(t1)
                core.core.storage.put_block(t2)

        elif test == 3:
            if test < 66:
                core.core.storage.put_block(t1)
            elif test < 132:
                core.core.storage.put_block(t1)
                core.core.storage.put_block(t2)
            else:
                core.core.storage.put_block(t1)
                core.core.storage.put_block(t2)
                core.core.storage.put_block(t3)

        # TODO more

        client = core.core.Client()
        client.client.connect_to_net()
