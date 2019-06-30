import random

from storage import storage
from core import core, signing
from core.transmission import Transmission
from network.server_peer import ServerPeer

SUCCESS = 1
FAIL = 0

class Server:
    # Dummy TODO

    def __init__(self):
        # Dummy implementation, to be replaced by calls to the actual network script
        self.server = ServerPeer(list_chain=self.list_chain, send_sync_message=self.react_to_sync_request,
                                 send_subchain_message=self.react_to_subchain_request, start_sync=self.synchronize)
        storage.put_block(core.produceTransmission(storage.get_head(), ["a", "b"], "document-3"))
        # connect to network, retrieve latest graph
        # now wait for transmissions from clients, verify them and append them to local chain
        # self.synchronize()

    def synchronize(self):
        # Synchronizing:
        # Step 1: send request message and get list of transmission hashes (clear and signed)
        message_list = self.server.send_synchronize_request()
        # message_list: [{public_key, transmission_hash, transmission_hash_signed}]

        # Step 2: group received hashes by majority
        majority = []
        for msg in message_list:
            # TODO add again
            # r = requests.get('https://api.zipixx.com/cryptocontracts/', header="Content-Type: application/json", data="{key: " + msg["public_key"] + "}")
            # if not r.status_code == 200:
            #    continue

            unsigned_hash = signing.unsign(msg["transmission_hash_signed"], {msg["public_key"]})
            if not core.compare(unsigned_hash, msg["transmission_hash"]):
                continue

            close = False
            for i in range(len(majority)):
                if core.compare(majority[i]["hash"], msg["transmission_hash"]):
                    majority[i]["count"] += 1
                    majority[i]["list"].append(msg)
                    close = True
                    break

            if not close:
                majority.append({"hash": msg["transmission_hash"], "count": 1, "list": [msg]})

        majority = sorted(majority, key=lambda k: k["count"], reverse=True)

        # Step 3: request subchain
        result = None
        already_synced = 0
        for maj in majority:
            if core.compare(maj["hash"], storage.get_block(storage.get_head()).unsigned_transmission_hash()):
                already_synced += 1
                continue

            succeeded = False
            for i in range(5):
                rnd = random.randint(0, len(maj["list"]) - 1)
                subchain = self.server.request_subchain(maj["list"][rnd], storage.get_block(
                    storage.get_head()).unsigned_transmission_hash())
                # subchain: list of transmissions [old -> new]
                if subchain is None:
                    continue

                if not core.compare(subchain[0].transmission_hash,
                                    storage.get_block(storage.get_head()).unsigned_transmission_hash()):
                    continue

                failed = False
                for j in range(1, len(subchain)):
                    if not core.compare(subchain[j].previous_hash, subchain[j - 1].unsigned_transmission_hash()):
                        failed = True
                        break

                    if not core.verifyTransmission(subchain[j]):
                        failed = True
                        break

                if failed:
                    continue
                succeeded = True
                result = subchain
                break

            if succeeded:
                break

        if already_synced == len(majority):
            print("ALREADY SYNCHRONIZED")
            return SUCCESS

        # Step 4: Add
        if result is None:
            print("SYNC FAIL")
            return FAIL

        for sub in result[1:]:
            storage.put_block(sub)
        print("SYNC SUCCESS")
        return SUCCESS

    def react_to_sync_request(self, conn):
        t = storage.get_block(storage.get_head())
        x = {
            "public_key": signing.OWN_PUBLIC_KEY,
            "transmission_hash": t.unsigned_transmission_hash(),
            "transmission_hash_signed": signing.sign(t.unsigned_transmission_hash(), signing.OWN_PRIVATE_KEY)
        }
        self.server.send_sync_request_answer(conn, x)

    def react_to_subchain_request(self, conn, transmission_hash):
        print("HASH: ", transmission_hash)
        subchain = storage.get_subchain(transmission_hash)
        subchain.reverse()
        print("SUBCHAIN", subchain)
        self.server.send_subchain(conn, subchain)

    def list_chain(self):
        print("CHAIN:")
        storage.print_all()
        print("HEAD: ", storage.get_head())

    def got_transmission(self, transmission: Transmission):
        # don't resend if transmission is already in graph

        if storage.block_exists(transmission.transmission_hash):
            return

        if not core.verifyTransmission(transmission):
            # send REFUSE package to network
            return

        # check if previous hash is correct
        # if not core.compare(transmission.previous_hash, self.graph[-1].transmission_hash):
        if not isinstance(storage.get_head(), Transmission) or \
                not core.compare(transmission.previous_hash, storage.get_head().transmission_hash):
            # maybe the graph is not the latest version. Get latest graph and try again
            # getLatestGraph()
            if not isinstance(storage.get_head(), Transmission) or \
                    not core.compare(transmission.previous_hash, storage.get_head().transmission_hash):
                # send REFUSE package to network
                return

        storage.put_block(transmission)

        # send SUCCESS package to network
        # send the transmission to all known peers in network
