import random

from core import core
from core.transmission import Transmission, signing
from storage import storage
from network.client_peer import Peer

SUCCESS = 1
FAIL = 0

class Client:
    # Dummy TODO

    def __init__(self, addr=None):
        # Dummy implementation, to be replaced by calls to the actual network script
        self.client = Peer(addr=addr, list_chain=self.list_chain, send_sync_message=self.react_to_sync_request,
                           send_subchain_message=self.react_to_subchain_request, start_sync=self.synchronize,
                           receive_subchain_message=self.react_to_received_subchain,
                           receive_message=self.react_to_receive_messsage)

    @staticmethod
    def list_chain():
        print("CHAIN:")
        storage.print_all()
        #print("HEAD: ", storage.get_head())

    def react_to_sync_request(self, conn):
        t = storage.get_block(storage.get_head())
        x = {
            "public_key": signing.OWN_PUBLIC_KEY,
            "transmission_hash": t.unsigned_transmission_hash(),
            "transmission_hash_signed": signing.sign(t.unsigned_transmission_hash(), signing.OWN_PRIVATE_KEY)
        }
        self.client.send_sync_request_answer(conn, x)
        print("INCOMING REMOTE SYNC REQUEST")

    def react_to_subchain_request(self, conn, transmission_hash):
        subchain = storage.get_subchain(transmission_hash)
        subchain.reverse()
        self.client.send_n2_subchain(conn, subchain)

    def react_to_receive_messsage(self, transmission):
        if transmission is None:
            return

        if not core.compare(transmission.transmission_hash,
            storage.get_block(storage.get_head()).unsigned_transmission_hash()):
            print("REMOTE SYNC REJECTED")
            return

        if not core.verify_transmission(transmission):
            print("REMOTE SYNC REJECTED")
            return

        storage.put_block(transmission)
        print("REMOTE SYNC ACCEPTED")

    @staticmethod
    def react_to_received_subchain(subchain):
        if subchain is None:
            return

        if not core.compare(subchain[0].transmission_hash,
                            storage.get_block(storage.get_head()).unsigned_transmission_hash()):
            return

        for j in range(1, len(subchain)):
            if not core.compare(subchain[j].previous_hash, subchain[j - 1].unsigned_transmission_hash()):
                return

            if not core.verify_transmission(subchain[j]):
                return

        for sub in subchain[1:]:
            storage.put_block(sub)

    def synchronize(self):
        # Synchronizing:
        # Step 1: send request message and get list of transmission hashes (clear and signed)
        message_list = self.client.send_synchronize_request()
        # message_list: [{public_key, transmission_hash, transmission_hash_signed}]

        # Step 2: group received hashes by majority
        majority = []
        for msg in message_list:
            # TODO add again
            #r = requests.get('https://api.zipixx.com/cryptocontracts/', header="Content-Type: application/json", data="{key: " + msg["public_key"] + "}")
            #if not r.status_code == 200:
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

        majority = sorted(majority, key= lambda k:k["count"], reverse=True)

        # Step 3: request subchain
        result = None
        already_synced = 0
        for maj in majority:
            if core.compare(maj["hash"], storage.get_block(storage.get_head()).unsigned_transmission_hash()):
                already_synced += 1
                continue

            elif storage.block_exists(maj["hash"]):
                subchain = storage.get_subchain(maj["hash"])
                subchain.reverse()
                self.client.send_n1_subchain(subchain)
                print("SYNC SUCCESS")
                return SUCCESS

            succeeded = False
            for i in range(5):
                rnd = random.randint(0, len(maj["list"])-1)
                subchain = self.client.request_subchain(maj["list"][rnd], storage.get_block(storage.get_head()).unsigned_transmission_hash())
                # subchain: list of transmissions [old -> new]
                if subchain is None:
                    continue

                if not core.compare(subchain[0].transmission_hash, storage.get_block(storage.get_head()).unsigned_transmission_hash()):
                    continue

                failed = False
                for j in range(1, len(subchain)):
                    if not core.compare(subchain[j].previous_hash, subchain[j-1].unsigned_transmission_hash()):
                        failed = True
                        break

                    if not core.verify_transmission(subchain[j]):
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

    def place_transmission(self, transmission):

        self.client.send_transmission(transmission)

        if not self.synchronize() == SUCCESS:
            print("No new transmission possible")
            return