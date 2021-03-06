from storage import config, storage
from core import core, client, server
#from GUI import gui
import sys

"""
Old initial

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if str(arg).lower() == "client":
            if len(sys.argv) > 2:
                addr = sys.argv[2]
                client.Client(addr)
            else:
                client.Client()
        elif str(arg).lower() == "server":
            server.Server()
        else:
            server.Server()
    else:
        server.Server()"""

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

    prev = storage.get_block(storage.get_head())
    t1 = core.core.produce_transmission_fully(prev.transmission_hash, ["priv_a", "priv_b"], ["a", "b"], "document-1")
    t2 = core.core.produce_transmission_fully(t1.transmission_hash, ["priv_c", "priv_d"], ["c", "d"], "document-2")
    t3 = core.core.produce_transmission_fully(t2.transmission_hash, ["priv_e", "priv_f"], ["e", "f"], "document-3")

    if mode == "server":
        server.Server()

    elif mode == "client":
        if  test == 1:
            if unit == 1:
                storage.put_block(t1)
            else:
                storage.put_block(t1)
                storage.put_block(t2)

        elif test == 2:
            if unit < 100:
                storage.put_block(t1)
            else:
                storage.put_block(t1)
                storage.put_block(t2)

        elif test == 3:
            if unit < 66:
                storage.put_block(t1)
            elif unit < 132:
                storage.put_block(t1)
                storage.put_block(t2)
            else:
                storage.put_block(t1)
                storage.put_block(t2)
                storage.put_block(t3)

        elif test == 4:
            if unit == 1:
                storage.put_block(t1)
            else:
                storage.put_block(t1)
                storage.put_block(t2)
                storage.put_block(t3)

        # TODO more

        client = client.Client()
        client.client.connect_to_net()

stylesheet = """
    GUI {
    border-image: url("blockchain.png"); 
    background-repeat: no-repeat; 
    background-position: center;}"""

"""if __name__ == '__main__':
    app = gui.QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    ex = gui.GUI()
    sys.exit(app.exec_())"""
