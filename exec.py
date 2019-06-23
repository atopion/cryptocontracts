import core.core
import sys

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