#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 14:11:42 2019

@author: rene
"""

from storage import storage
from core import core, client_with_ip_server
import sys


# This program creates a peer object and connects to the other peers in the network
# It can be started with predefined test blocks in the chain
# For ordinary use do not add parameters for execution, the system is then started with the content in the database
# For predefined test blocks give 2 parameters: first a number between 1 and 4 indicating the test case,
# and second a number that is 1 or higher representing the test unit.
# For obtaining fine grained system output, pass the parameter "debug"
# For testing the system in the same LAN, pass the parameter "internal"
# For testing the system on the same computer, pass the parameter "localhost"
# If it is desired to use the debug mode and/or test in same LAN/ on same computer,
# the 2 numbers for test case and test unit have to be given, because those modes are
# only considered for testing and maintenance.

if __name__ == '__main__':
    arg_len = len(sys.argv)
    if arg_len > 5:
        print("Wrong number of arguments")
        sys.exit(1)

    scope = None
    output = None
    
    if arg_len > 2:
        try:
            test = int(sys.argv[1])
            unit = int(sys.argv[2])
        except ValueError:
            print("Irregular arguments (no integers)")
            sys.exit(1)
        
        if arg_len == 5:
            scope = sys.argv[3]
            if not (scope == "internal" or scope == "external" or scope == "localhost"):
                print("Wrong argument for scope. Can either be internal, external or localhost")
                sys.exit(1)
            output = sys.argv[4]
            if not (output == "user" or output == "debug"):
                print("Wrong argument for output. Can either be user or debug")
                sys.exit(1)
                
        if arg_len == 4:
            option = sys.argv[3]
            if (option == "internal" or option == "external" or option == "localhost"):
                scope = option
                
            elif (option == "user" or option == "debug"):
                output = option
            else:
                print("{} is not a valid argument".format(option))
                sys.exit(1)
                
        # predefined blocks for storing in database
        prev = storage.get_block(storage.get_head())
        t1 = core.produce_transmission_dummy(prev.transmission_hash, ["pub_a", "pub_b"], "document-1", "document-1_signed", "t1_trans_hash")
        t2 = core.produce_transmission_dummy(t1.transmission_hash, ["pub_c", "pub_d"], "document-2", "document-2_signed", "t2_trans_hash")
        t3 = core.produce_transmission_dummy(t2.transmission_hash, ["pub_e", "pub_f"], "document-3", "document-3_signed", "t3_trans_hash")

        # test cases
        if test == 1:
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

    # create peer object and start joining network
    peer = client_with_ip_server.Client(scope=scope, output=output)
    peer.client.connect_to_net()

