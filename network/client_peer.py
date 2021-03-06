#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 23:32:58 2019

@author: rene
"""

import socket
import threading
import os
import random
import json
import sys
import time
import datetime

from core import core
from core.transmission import Transmission
from upnp import upnp


class Peer:
    """ A class representing a Peer of the network which connects to the server
    
    Attributes
    ----------
    active_peers : list
        a list containing all peers that are currently connected to the network
    connected_peers : list
        a list containing the peers connected to this host
    fixed_server : boolean
        a boolean that tells if a fixed address for a server to connect to is given
    last_addresses : list
        a list that contains the latest known active peers in the net
    lock : lock object
        a lock object for the treading module to lock main thread
    server_address : str
        a string representing the IP address of the server peer
    sock_server : socket object
        a socket that is bind to handle the in coming connections
    sock_client : socket object
        a socket that is bind to enable a connection to a different peer

        
    Methods
    -------
    choose_connection()
        Defines where to establish a connection to depending on if a specific address is given or not
    command_handler()
        Takes care of the user input
    incoming_connection_handler(conn, addr)
        Manages connections to other peers
    connect_to_net()
        Establishes connection to the server peer
    disconnect_from_net()
        Disconnects from the network/server peer
    get_active_peers()
        Gets the list of all peers currently connected to the net/server peer
    get_connected_peers()
        Returns the list of all peers currently connected to the this host
    get_host_addr()
        Returns the IP address of this host
    listen_for_connections()
        Makes sure that peers can connect to this host
    outgoing_connection_handler()
        Maintains outgoing connection from this peer to another node in the net
    request_graph(address)
        Sends request for latest version of graph to peer specified in address
    send_active_peers()
        Sends the list of active peers to all the known addresses in the network
    send_graph(address)
        Sends latest version of graph to peer specified in address
    store_addresses()
        Stores the currently active peers in the network to file
    """
    
    active_connectable_addresses = []
    active_peers = []
    full_addresses = []     # Both addresses of active peers, for sending and receiving
    connected_peers = []    # Addresses of peers connected to this host
    connections = []    # holds connection objects
    fixed_server = False
    last_addresses = []
    lock = threading.Lock()     # To lock main thread after establishing connection
    port = None
    server_address = None
    server_peers = []
    sock_server = None
    sock_client = None
    standalone = False  # If true start host without connecting
    client_sockets = []
    address_connection_pairs = {} # addresses of peers to connect to and the connection object from this host to the same peer

    synchronization_finished_event = threading.Event()
    synchronization_subchain_event = threading.Event()

    def __init__(self,addr=None, port=None, list_chain=None, send_sync_message=None, send_subchain_message=None,
                 start_sync=None, receive_subchain_message=None, receive_message=None):
        
        self.cb_list_chain = list_chain
        self.cb_start_sync = start_sync
        self.cb_send_sync_message = send_sync_message
        self.cb_send_subchain_message = send_subchain_message
        self.cb_receive_message = receive_message
        self.cb_receive_subchain_message = receive_subchain_message

        self.synchronization_chain = []
        self.synchronization_request_answers = []

        self.fixed_server = False

        if addr is None:
            if os.path.isdir("./addresses") and os.path.isfile("./addresses/last_active_addresses.txt"):
                last_addresses = open("./addresses/last_active_addresses.txt")
                try:
                    str_rep = last_addresses.read().split(",")
                    for loc in str_rep:
                        temp = loc.split(":")   # bring into tupel format
    #                    print(temp)
                        self.last_addresses.append((temp[0],int(temp[1])))
                    last_addresses.close()
                except:
                    print("Can not read addresses, host will start and wait for incoming connections")
                    self.standalone = True

            else:
#                sys.exit("No addresses stored. Please give a specific peer address when creating object.")
                print("No addresses stored, host will start and wait for incoming connections")
                self.standalone = True
        else:
            if port:
                upnp.add_port(int(port))
                self.server_address = (addr, int(port))

            else:
                self.server_address = addr

            self.fixed_server = True    # Flag to decide how to connect to net
    
    
    def choose_connection(self):
        """ Defines where to establish a connection to depending on if a specific address is given or not
        
        If no server address is specified when creating the peer object, an address from the last known addresses of the network is
        chosen randomly. If none is active the program is quit.
        """
        
        connected = False
        if self.fixed_server == False:
            

#            not necessary anymore cause own address removed before shutdown
#            try:
#                self.last_addresses.remove(self.get_host_addr())
#            except:
#                pass
            host_addr = self.get_host_addr()
            while connected == False:
                
                if len(self.active_connectable_addresses) > 1 : # evoid endless looping when only own address is in list
                    chosen_addr = random.choice(self.active_connectable_addresses)
                    

                elif not self.last_addresses:
                    print("No peer is online, host will start and wait for incoming connections")
                    break

                else:
                    chosen_addr = random.choice(self.last_addresses)

                if not (chosen_addr[0] == host_addr[0] and chosen_addr[1] == host_addr[1]):     # do not connect to own address
                    print("Trying to connect to {}:{}".format(chosen_addr[0],str(chosen_addr[1])))
                    connected = self.create_new_connection(chosen_addr)
                    if connected:
                        self.active_connectable_addresses.append(self.get_host_addr())
                        self.store_addresses()


#                        try:
#                            self.send_port(chosen_addr, self.sock_client)
#                        except:
#                            print("Could not send own address!")

                    else:
                        try:
                            self.last_addresses.remove(chosen_addr)
                        except Exception as e:
                            print("Can not remove chosen address from last_addresses. Exception: ", e)


        # server address specified on execution
        else:
            try:    # address can either contain a port number or not
#                self.sock_client.connect(self.server_address)
                self.create_new_connection(self.server_address)
                connected = True
#                print("connected to server {}:{}".format(self.server_address[0],str(self.server_address[1])))
#                self.active_connectable_addresses.append(self.get_host_addr())
            except:
                print("Could not connect to specified address. Host will start and wait for connections")
#
        return connected

    def clean_active_connectable_addresses(self):
        """ Removes duplicates from list containing active connectable addresses in the net
        """
        # TODO make sure that it is not possible that an address is appended while cleaning
        
        if len(self.active_connectable_addresses) > 1:
            i = 0
            for addr in self.active_connectable_addresses:
                j = i+1
                for other in self.active_connectable_addresses[i+1:]:
                    if addr[0] == other[0] and int(addr[1]) == int(other[1]):
                        self.active_connectable_addresses.pop(j)
                        j -= 1  # list gets smaller due to pop
                    j +=1
                i +=1
#                
#        print("AFTER CLEANING:",self.get_active_connectable_addresses())

    def clean_active_peers(self):
        """ Removes duplicates from list containing active peers in the net
        """

        # TODO make sure that it is not possible that an address is appended while cleaning

        i = 0
        for addr in self.active_peers:
            j = 0
            for other in self.active_peers[i+1:]:
                if addr[0] == other[0] and int(addr[1]) == int(other[1]):
                    self.active_peers.pop(j)
                    j -= 1
                j +=1
            i +=1

#        clean_list = []
#        for peer in self.active_peers:
#            if peer not in clean_list:
#                clean_list.append(peer)
#        self.active_peers = clean_list

    def clean_connections(self):
        """ Removes duplicates from list containing connections to this host
        """

        i = 0
        for addr in self.connections:
            j = 0
            for other in self.connections[i+1:]:
                if addr is other:
                    self.connections.pop(j)
                    j -= 1
                j +=1
            i +=1


    def clean_connected_peers(self):
        """ Removes duplicates from list containing connected peers to this host
        """

        i = 0
        for addr in self.connected_peers:
            j = 0
            for other in self.connected_peers[i+1:]:
                if addr[0] == other[0] and int(addr[1]) == int(other[1]):
                    self.connected_peers.pop(j)
                    j -= 1
                j +=1
            i +=1
    
    def command_handler(self):
        """ Takes care of the user input. 
        
        The command 'peer' shows the other active peers in the network.
        the commands 'exit', 'quit' and 'close' end the connection.
        """
        while True:
            try:

                i = input()
                if i == "peers":
                    p = self.get_active_peers()
                    print(p)

                elif i == "connectable":
                    p = self.get_active_connectable_addresses()
                    print(p)
                elif i == "exit" or i == "quit" or i == "close":
                    self.disconnect_from_net()
                elif i == "connections":
                    p = self.get_connected_peers()
                    print(p)
                elif i == "servers":
                    p = self.get_server_peers()
                    print(p)
                elif i == "clients":
                    p = self.get_connected_peers()
                    print(p)
                elif i == "pairs":
                    print(self.address_connection_pairs)
                elif i == "sync":
                    print(self.cb_start_sync)
                    if self.cb_start_sync is not None:
                        self.cb_start_sync()
                elif i == "list":
                    if self.cb_list_chain is not None:
                        self.cb_list_chain()
                elif i == "host":
                    p = self.get_host_addr()
                    print(p[0]+":"+str(p[1]))
                elif i == "clean":
                    self.clean_active_peers()
                    self.clean_connected_peers()
                else:
                    for connection in self.connections:
                        connection.send(bytes(str(i),'utf-8'))

            except EOFError:
                os._exit(1)
            except KeyboardInterrupt:
                os._exit(1)
    
    def connect_to_net(self):
        """ Establishes connection to the server peer
        
        Sets up a socket and connects to the server peer. A new thread is started
        that runs the command_handler function for user input handling.
        Data that is received is checked for special meaning by prefixes.
        If no prefix is found, it is considered a message and printed out.
        """
        
#        self.sock_client= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        self.sock_client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        
        command_thread = threading.Thread(target=self.command_handler)
        command_thread.daemon = True
        command_thread.start()
        
        server_thread = threading.Thread(target=self.listen_for_connections)
        server_thread.daemon = True
        server_thread.start()
        
        time.sleep(1)    # so server_thread has time to bind socket and assign port
        host_addr = self.get_host_addr()
        self.active_connectable_addresses.append(host_addr)
        self.store_addresses()
        print("Host address: ", host_addr)

        if not self.standalone:

            connected = self.choose_connection()    # chooses and establishes connection to another node in the net

#            if connected:
#                client_thread = threading.Thread(target=self.outgoing_connection_handler)
#                client_thread.daemon = True
#                client_thread.start()
        
        self.lock.acquire()
        self.lock.acquire()  # call two times to lock main thread


    def create_new_connection(self, addr):
        """ Creates a new connection to a specified address

        A new socket is created. Over that a connecetion to the passed address is established
        The connection is managed in a separate thread. If connection not possible print notification.

        Parameters
        ----------
        addr : (str,int)
           A tuple of IP address and port to which a connection should be established

        Returns
        -------
        connected : boolean
           a variable stating if connection was succesfully created
        """

        existing = False
        for peer in self.server_peers:
            if (peer[0] == addr[0] and peer[1] == addr[1]):
                existing = True

        connected = False
        if not existing:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(addr)
                self.server_peers.append(addr)
                self.client_sockets.append(sock)
                thread = threading.Thread(target=self.outgoing_connection_handler, args=(addr,sock))
                thread.daemon = True
                thread.start()
                print("Connected to " + addr[0] + ":" + str(addr[1]))
                connected = True
            except Exception as e:
                print("Could not connect to {}:{} \n Reason: {}".format(addr[0],str(addr[1]),e))

        return connected


    def disconnect_from_net(self):
        """Disconnects from the network/server peer
        
        The socket is shutdown and closed which causes a disconnection
        """

        try:
            self.last_addresses.remove(self.get_host_addr())
        except:
            pass

        self.store_addresses()  # when restarted this host does not try to connect to itself

        self.lock.release()     #unlock main thread
        
        for sock in self.client_sockets:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()

#        self.sock_client.shutdown(socket.SHUT_RDWR)
#        self.sock_client.close()
        
        self.sock_server.shutdown(socket.SHUT_RDWR)
        self.sock_server.close()

    def get_active_connectable_addresses(self):
        """ Returns the list of all peers currently connected to the net/server peer with their port numbers to connect to

        The peer IP addresses and port numbers are taken from the object variable active_connectable_addresses and are joined in a String

        Returns
        -------
        string
            a string representing the IP addresses of the currently connected peers
        """

        p = ""

        if self.active_connectable_addresses:
            p = self.active_connectable_addresses[0][0] + ":" + str(self.active_connectable_addresses[0][1])

            for peer in self.active_connectable_addresses[1:]:
    #            p = p + peer + ","
                p = p +  "," + peer[0] + ":" + str(peer[1])

        return p


    def get_active_peers(self):
        """ Returns the list of all peers currently connected to the net/server peer

        The peer IP addresses are taken from the object variable activePeer and are joined in a String

        Returns
        -------
        string
            a string representing the IP addresses of the currently connected peers
        """

        p = ""
        
        if self.active_peers:
            p = self.active_peers[0][0] + ":" + str(self.active_peers[0][1])

            for peer in self.active_peers[1:]:
    #            p = p + peer + ","
                p = p +  "," + peer[0] + ":" + str(peer[1])

#        else:
#            p = "List is empty"

        return p
    

    def get_connected_peers(self):
        """ Returns the list of all peers currently connected to the this host
        
        The peer IP addresses are taken from the object variable activePeer and are joined in a String
        
        Returns
        -------
        string
            a string representing the IP addresses of the currently connected peers
        """
        
        p = ""
        
        if self.connected_peers:
            p = self.connected_peers[0][0] + ":" + str(self.connected_peers[0][1])

            for peer in self.connected_peers[1:]:
    #            p = p + peer + ","
                p = p + "," + peer[0] + ":" + str(peer[1])

#        else:
#            p = "No connections established to this host"
            
        return p
    
    def get_host_addr(self):
        """ Returns the IP address of this host.
        
        Returns
        -------
        tuple (str,int)
            a tuple containing the IP address of this host and the port that the server socket is bound to
        """
        
        host_name = socket.gethostname()
        host_addr = socket.gethostbyname(host_name)
        
        return (host_addr,self.port)

    def get_server_peers(self):
        """ Returns addresses of peers that are connected to this host

        Returns
        -------
        string
            a string representation of the IP adresses and ports of the peers that this host is currently connected to

        """

        p = ""

        if self.server_peers:
            p = self.server_peers[0][0] + ":" +  str(self.server_peers[0][1])
            for peer in self.server_peers[1:]:
                p = p + "," + peer[0] + ":" + str(peer[1])

        return p

    def get_time(self):
        
        return datetime.datetime.now().time()

    def incoming_connection_handler(self, conn, address):
        """ Manages connections to other peers

        It is constantly waited for incoming data. The data is a byte stream.
        The data sent by a client is distributed to all the other ones.
        After a connection has been canceled, the new connection list is sent to all the active peers in the network.
        
        parameters:
        -----------
        conn : connection of specific peer
        addr : IP address of specific peer
        """

        # TODO think about if this method should wait for receiving data

        self.send_active_connectable_addresses(conn)

        while True:
            try:

                # TODO check if single thread for each outgoing connection needed
                data = conn.recv(1024)

                if not data:
                    print(str(address[0]) + ":" + str(address[1]),"disconnected")
                    conn.close()
                    try:
                        self.connections.remove(conn)
                        self.clean_connections()
                    # TODO find out why Error is raised
                    except ValueError:
                        print("Could not remove connection from connections \n")

                    try:
                        self.connected_peers.remove(address)
                        self.clean_connected_peers()
                    except ValueError:
                        print("Could not remove address {}:{} from connected peers \n".format(address[0],str(address[1])))

                    try:
                        self.active_peers.remove(address)
                        self.clean_active_peers()
                    except ValueError:
                        print("Could not remove address {}:{} from active peers \n".format(address[0],str(address[1])))

#                    self.send_active_peers()
                    self.send_offline_peer(address) # notify connected peers that one peer went offline
                    break

                print("{}: From {}:{} received {} over incoming connection handler \n".format(self.get_time(),address[0],str(address[1]),data))
#                 mode = int(bytes(data).hex()[0:2])


                inputs = str(data, "utf-8").split("!")
#                print("{}: INPUTS: {} \n \n".format(self.get_time(),inputs))
                for msg in inputs:
#                    print("{}: MSG at BEG: {} \n \n".format(self.get_time(),msg))
                    if msg != "":
                        mode = int(bytes(msg, "utf-8").hex()[0:2])
#                        print("part message: ", msg)
                        print("{}: MODE: {} \n".format(self.get_time(),mode))
                        core.network_log("RECEIVED \\x", mode, " from ", address[0])
                        # look for specific prefix indicating the list of active peers
                        if mode == 11:

                            self.clean_active_peers()   # just for testing

                            rec_active_peers = []
                            rec_data = msg[1:].split(",")
                            for addr in rec_data:
                                temp = addr.split(":")  # bring into tuple format
                                rec_active_peers.append((temp[0],int(temp[1])))
                            if not (set(rec_active_peers) == set(self.active_peers)): # check if peer lists are equal
                                for rec_peer in rec_active_peers:
                                    existing = False
                                    for peer in self.active_peers:
                                        existing = False
                                        if (peer[0] == rec_peer[0] and peer[1] == rec_peer[1]):
                                            existing = True
                                            break
                                    if not existing:
                                        self.active_peers.append((rec_peer[0],rec_peer[1]))     # append new addresses

                                self.clean_active_peers()
#                                self.send_active_peers()

                        elif mode == 12:

#                            self.clean_active_connectable_addresses()   # just for testing

                            rec_connectable_addresses = []
                            rec_data = msg[1:].split(",")

                            for addr in rec_data:
                                temp = addr.split(":")  # bring into tuple format
                                rec_connectable_addresses.append((temp[0],int(temp[1])))

                            if not (set(rec_connectable_addresses) == set(self.active_connectable_addresses)): # check if peer lists are equal
                                for rec_peer in rec_connectable_addresses:
                                    existing = False
                                    for peer in self.active_connectable_addresses:
                                        existing = False
                                        if (peer[0] == rec_peer[0] and peer[1] == rec_peer[1]):
                                            existing = True
                                            break
                                    if not existing:
                                        self.active_connectable_addresses.append((rec_peer[0],rec_peer[1])) # append new addresses
                                        # appending already included in new connection function
                                        self.create_new_connection((rec_peer[0],rec_peer[1]))

                                self.clean_active_connectable_addresses()
                                self.send_active_connectable_addresses()
                                self.store_addresses()
                                
                                
                        elif mode == 15:
                            # for matching address of incoming data and connection object to send data 
                            rec_data = msg[1:]
                            rec_peer = rec_data.split(":")
                            self.create_new_connection((rec_peer[0],int(rec_peer[1])))
                            self.address_connection_pairs.update({rec_data:conn})
                            self.active_connectable_addresses.append((rec_peer[0],rec_peer[1]))
                            print("{}: Address-connection pair added".format(self.get_time()))
                            

                        elif mode == 20:
                            self.cb_receive_message(Transmission.from_json(msg[1:]))

                        elif mode == 31:
                                # Synchronization request
                                if self.cb_send_sync_message is not None:
#                                    self.cb_send_sync_message(self.sock_client)
                                    self.cb_send_sync_message(conn)

                        elif mode == 32:
                            # Synchronization answer
                            data = json.loads(str(msg[1:]))
#                            data["conn"] = self.sock_client
                            data["conn"] = conn
                            self.synchronization_request_answers.append(data)
                            # TODO multiple connections
                            if len(self.synchronization_request_answers) == len(self.connected_peers):
                                self.synchronization_finished_event.set()
                            #self.synchronization_finished_event.set()

                        elif mode == 33:
                            # Subchain request
                            hash = str(msg[1:])
                            if self.cb_send_subchain_message is not None:
#                                self.cb_send_subchain_message(self.sock_client, hash)
                                self.cb_send_subchain_message(conn, hash)

                        elif mode == 34 or mode == 35:

#                            print("{}: MSG: {} \n \n".format(self.get_time(),msg))
                            try:
                                rec_data = msg[1:].split("&")
#                                print("{}: REC_DATA: {} \n \n".format(self.get_time(),rec_data))
                                length = int(rec_data[0])
#                                print("LENGTH: {} \n \n".format(length))
                                all_data = rec_data[1]
#                                print("ALL_DATA: {} \n \n".format(all_data.replace("\\", "")))
                                while len(all_data) < length:
                                    to_read = length - len(all_data)
                                    all_data += str(conn.recv(4096 if to_read > 4096 else to_read), "utf-8")
#                                    print("ALL_DATA IN LOOP: {} \n \n".format(all_data))

                                if mode == 34:
                                    # Subchain answer
                                    self.synchronization_chain = core.core.Transmission.list_from_json(
                                        all_data.replace("\\", ""))
                                    self.synchronization_subchain_event.set()

                                else:
                                    # synchronizing node has more transmissions than the synchronizing partners
                                    self.synchronization_chain = core.core.Transmission.list_from_json(
                                        all_data.replace("\\", ""))
                                    if self.cb_receive_subchain_message is not None:
                                        self.cb_receive_subchain_message(self.synchronization_chain)

                            except Exception as e:
                                print("{}: Could not receive subchain \n".format(self.get_time()))
                                print("Reason: ", e)

                            # if no prefix consider data a message and print it
                        else:
                            print("{}: Message: {}".format(self.get_time(),msg))

                            """elif mode == 34:
                                # Subchain answer
                                self.synchronization_chain = core.core.Transmission.list_from_json(str(msg[1:]).replace("\\\\", "\\"))
                                self.synchronization_subchain_event.set()
                            # if no prefix consider data a message and print it"""

            except ConnectionResetError or ConnectionAbortedError:
                print("Connection closed.")
                os._exit(1)

#        while True:
#            data = conn.recv(1024)
#            print("RECEIVED: ", data)
#            for connection in self.connections:
#                connection.send(bytes(data))
#            if not data:
#                print(str(address[0]) + ":" + str(address[1]),"disconnected")
#                self.connections.remove(conn)
#                self.clean_connections()
#                self.connected_peers.remove(address)
#                self.clen_connected_peers()
#                self.active_peers.remove(address)
#                self.clean_active_peers()
#                conn.close()
#                self.send_active_peers()
#                break
    
    
    def listen_for_connections(self):
        """ Makes sure that peers can connect to this host.
        
        Creates an own thread for each incoming connection.
        """
        
        self.sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.port = random.randint(10001,15000)
        upnp.add_port(self.port)
        self.sock_server.bind(('0.0.0.0',self.port))
        self.sock_server.listen(1)
        
        while True:
            conn, addr = self.sock_server.accept()
            thread = threading.Thread(target=self.incoming_connection_handler, args=(conn,addr))
            thread.daemon = True
            thread.start()
            self.connected_peers.append(addr)
            self.connections.append(conn)
            self.clean_connected_peers()
            self.active_peers.append(addr)
            self.clean_active_peers()
            print(str(addr[0]) + ':' + str(addr[1]),"connected")
            self.send_active_peers()
    
    def outgoing_connection_handler(self, address, sock):
        """ Maintains outgoing connection from this peer to another node in the net

        If the connection to the server node corrupts, it is looked for another node to connect to
        """

        self.send_port(address, sock)

        while True:
            try:
                
                # TODO check if single thread for each outgoing connection needed
#                data = self.sock_client.recv(1024)
                data = sock.recv(1024)
                if not data:
                    try:
                        self.server_peers.remove(address)
                    except:
                        print("Could not remove server peer: {}:{} from server list".format(address[0],str(address[1])))

                    try:
                        self.active_connectable_addresses.remove(address)
                    except Exception as e:
                        print("{}: Could not remove server peer: {}:{} from active connectable address list".format(self.get_time(),address[0],str(address[1])))
                        print("{}: Reason: {}".format(self.get_time(),e))


                    try:
                        self.address_connection_pairs.pop(str(address[0]+":"+str(address[1])))
                    except Exception as e:
                        print("Could not remove address from address connection pair dict")
                        print("Reason: ",e)

                    self.send_offline_connectable_address(address)  # notify other peers that one peer went offline

                    self.client_sockets.remove(sock)
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()

                    break
#                    self.fixed_server = False   # When server peer goes offline, this peer needs to connect to another peer
#                    self.choose_connection()

                print("{}: From {}:{} received {}".format(self.get_time(), address[0],str(address[1]),data))
#                 mode = int(bytes(data).hex()[0:2])


                inputs = str(data, "utf-8").split("!")

                for msg in inputs:
                    if msg != "":
                        mode = int(bytes(msg, "utf-8").hex()[0:2])
#                        print("part message: ", msg)
                        print("{}: MODE: {}".format(self.get_time(),mode))
                        # look for specific prefix indicating the list of active peers

                        core.network_log("RECEIVED \\x", mode, " from ", address[0])

                        if mode == 11:

                            rec_active_peers = []
                            rec_data = msg[1:].split(",")
                            for addr in rec_data:
                                temp = addr.split(":")  # bring into tuple format
                                try:
                                    rec_active_peers.append((temp[0],int(temp[1])))
                                except IndexError:
                                    print("INDEXERROR: ", temp)
                                    
                            self.clean_active_peers()
                            if not (set(rec_active_peers) == set(self.active_peers)): # check if peer lists are equal

                                for rec_peer in rec_active_peers:
                                    existing = False
                                    for peer in self.active_peers:
                                        if (peer[0] == rec_peer[0] and peer[1] == rec_peer[1]):
                                            existing = True
                                            break
                                    if not existing:
                                        self.active_peers.append((rec_peer[0],rec_peer[1]))     # append new addresses

                                self.clean_active_peers()
                                self.send_active_peers()

                        elif mode == 12:
#                            print("Before cleaning: ", self.active_connectable_addresses)
#                            print("After cleaning: ", self.active_connectable_addresses)

                            rec_connectable_addresses = []
                            rec_data = msg[1:].split(",")

                            for addr in rec_data:
                                temp = addr.split(":")  # bring into tuple format
                                rec_connectable_addresses.append((temp[0],int(temp[1])))

                            self.clean_active_connectable_addresses()
                            if not (set(rec_connectable_addresses) == set(self.active_connectable_addresses)): # check if peer lists are equal

                                for rec_peer in rec_connectable_addresses:
                                    existing = False
                                    for peer in self.active_connectable_addresses:
                                        if (peer[0] == rec_peer[0] and peer[1] == rec_peer[1]):
                                            existing = True
                                            break
                                    if not existing:
                                        self.active_connectable_addresses.append((rec_peer[0],rec_peer[1]))     # append new addresses
                                        # appending already included in new connection function
                                        self.create_new_connection((rec_peer[0],rec_peer[1]))

                                self.clean_active_connectable_addresses()
                                self.send_active_connectable_addresses()
                                self.store_addresses()


                        elif mode == 13:
                            # peer went offline notification
                            offline_peer = msg[1:].split(":")
                            for addr in self.active_peers:
                                if offline_peer[0] == addr[0] and int(offline_peer[1]) == addr[1]:
                                    self.active_peers.remove(addr)
                                    self.send_offline_peer(addr)
                                    break   # considering that no redundant addresses in list

                        elif mode == 14:
                            # notification that connectable address not available anymore
                            offline_peer = msg[1:].split(":")
                            for addr in self.active_connectable_addresses:
                                if offline_peer[0] == addr[0] and int(offline_peer[1]) == addr[1]:
                                    self.active_connectable_addresses.remove(addr)
                                    self.send_offline_connectable_address(addr)
                                    break   # considering that no redundant addresses in list

                        elif mode == 20:
                            self.cb_receive_message(Transmission.from_json(msg[1:]))

                        elif mode == 31:
                            # Synchronization request
                            if self.cb_send_sync_message is not None:
                                self.cb_send_sync_message(self.address_connection_pairs[str(address[0]+":"+str(address[1]))])

                        elif mode == 32:
                            # Synchronization answer
                            print("IN MODE 32 in OCH: msg is ",str(msg[1:]))
                            data = json.loads(str(msg[1:]))
#                            data["conn"] = self.sock_client
                            data["conn"] = self.address_connection_pairs[str(address[0]+":"+str(address[1]))]
                            self.synchronization_request_answers.append(data)
                            # TODO multiple connections
                            if len(self.synchronization_request_answers) == len(self.connected_peers):
                                self.synchronization_finished_event.set()
                            #self.synchronization_finished_event.set()

                        elif mode == 33:
                            # Subchain request
                            hash = str(msg[1:])
                            if self.cb_send_subchain_message is not None:
                                try:
                                    self.cb_send_subchain_message(self.address_connection_pairs[str(address[0]+":"+str(address[1]))], hash)
                                except Exception as e:
                                    print("Exception: " , e)


                        elif mode == 34 or mode == 35:
#                            print("MSG: {} \n".format(msg))
                            try:
                                rec_data = msg[1:].split("&")
#                                print("REC_DATA: {} \n".format(rec_data))
                                length = int(rec_data[0])
#                                print("LENGTH: {} \n".format(length))
                                all_data = rec_data[1]
                                
                                while len(all_data) < length:
                                    to_read = length - len(all_data)
                                    all_data += str(sock.recv(4096 if to_read > 4096 else to_read), "utf-8")
#                                print("ALL_DATA: {} \n".format(all_data.replace("\\", "")))
                                if mode == 34:
                                    # Subchain answer
                                    self.synchronization_chain = core.core.Transmission.list_from_json(
                                        all_data.replace("\\", ""))
                                    self.synchronization_subchain_event.set()

                                else:
                                    # synchronizing node has more transmissions than the synchronizing partners
                                    self.synchronization_chain = core.core.Transmission.list_from_json(
                                        all_data.replace("\\", ""))
                                    self.cb_receive_subchain_message(self.synchronization_chain)

                            except Exception as e:
                                print("Could not receive subchain \n")
                                print("Reason: ", e)

                        # if no prefix consider data a message and print it
                        else:
                            print("Message: ", msg)

            except ConnectionResetError or ConnectionAbortedError:
                print("Connection closed.")
                os._exit(1)


    def request_graph(self, address):
        """Sends request for latest version of graph to peer specified in address
        
        Parameters
        ----------
        address : str
            IP address of peer to send request to
            
        """
        
        pass
    
    def send_active_connectable_addresses(self, addr=None):
        """ Sends the list of active connectable addresses to all peers connected to this host.

        The list of all active connectable addresses is taken and send over every connection as a byte stream.
        A dedicated information is output to the user.
        """
        
        self.clean_active_connectable_addresses()
        p = self.get_active_connectable_addresses()
#        print("Addresses befor sending:",p)

        if p:
            if addr:
                addr.send(b'\x12' + bytes(p, "utf-8") + b'!')
                print("Connectable addresses sent to freshly connected peer")
                core.network_log("SEND \\x12 to ", addr)
            else:
                for address in self.connections:
                    address.send(b'\x12' + bytes(p, "utf-8") + b'!')
                print("Connectable addresses sent to all connected peers")
                core.network_log("SEND \\x12 to ", [x for x in self.connections])
        else:
            print("Wanted to send connectable address list but it is empty!")
        # TODO also consider outgoing connections

    def send_active_peers(self):
        """ Sends the list of active peers to all the known addresses in the network.

        The list of all active peers is taken and send over every connection as a byte stream.
        A dedicated information is output to the user.
        """
        
        self.clean_active_peers()
        p = self.get_active_peers()
        
        if p:

            for address in self.connections:
                address.send(b'\x11' + bytes(p, "utf-8") + b'!')
            print("peer list sent to all connected peers")
            core.network_log("SEND \\x11 to ", [x for x in self.connections])
        else:
            print("Wanted to send active peer list but it is empty!")
    
    def send_graph(self, address):
        """Sends latest version of graph to peer specified in address
        
        Parameters
        ----------
        address : str
            IP address of peer to send graph to
        """
        pass
    
    def send_offline_peer(self, address):
       """ Sends notification to all connected peers that another peer went offline
       Sends the address of its client socket over that it was connected to this host

       Parameters
       ----------
       address : (str,int)
           tuple of IP address and port number of peer that went offline
       """

       p = address[0] + ":" + str(address[1])
       for peer in self.connections:
            peer.send(b'\x13' + bytes(p, "utf-8") + b'!')
       print("Notified connected peers that {} is offline".format(p))
       core.network_log("SEND \\x13 to ", [x for x in self.connections])

    def send_offline_connectable_address(self, address):
        """ Sends notification to all connected peers that another peer went offline.
        Sends the address of its connectable address

        Parameters
        ----------
        address : (str,int)
        tuple of IP address and port number of peer that went offline
        """

        p = address[0] + ":" + str(address[1])
        for peer in self.connections:
            peer.send(b'\x14' + bytes(p, "utf-8") + b'!')
        print("Notified connected peers that {} is offline".format(p))
        core.network_log("SEND \\x14 to ", [x for x in self.connections])

    def send_port(self, address, socket=None):
        """ Sends address with port number for establishing connection to this host

        Parameters
        ----------
        address : tuple (str,int)
            IP address and port to send to
        """

        host = self.get_host_addr()
        p = host[0] + ":" + str(host[1])

        if socket:
            socket.send(b'\x15' + bytes(p, "utf-8") + b'!')   # ! signals end of message
            core.network_log("SEND \\x15 to ", socket)
        else:
            address.send(b'\x15' + bytes(p, "utf-8") + b'!')
            core.network_log("SEND \\x11 to ", address)
        print("Own address sent to {}:{}".format(address[0], str(address[1])))

    def store_addresses(self):
        """ Stores the currently active peers in the network to file
        
        """
        if not os.path.isdir("./addresses") == True:
            os.mkdir("./addresses")
            
        last_addresses = open("./addresses/last_active_addresses.txt","w")
#        last_addresses.write(self.get_active_peers())
        last_addresses.write(self.get_active_connectable_addresses())
        last_addresses.close()
            
    def send_synchronize_request(self):
        for conn in self.connections:
            conn.send(b'\x31!')

        self.synchronization_finished_event.wait(30)
        res = self.synchronization_request_answers
        self.synchronization_request_answers = []
        self.synchronization_finished_event = threading.Event()
        print("{}: Synchronization Request sent \n".format(self.get_time()))
        core.network_log("SEND \\x31 to ", [x for x in self.connections])
        return res

    def send_sync_request_answer(self, conn, obj):
        conn.send(b'\x32' + bytes(json.dumps(obj), "utf-8"))
        print("{}: Synchronization Request Answer sent \n".format(self.get_time()))
        core.network_log("SEND \\x32 to ", conn)

    def request_subchain(self, msg, hash):
        self.synchronization_chain = None
        msg["conn"].send(b'\x33' + bytes(hash, "utf-8"))
        print("{}: Subchain requested \n".format(self.get_time()))
        core.network_log("SEND \\x32 to ", [x for x in self.connections])
        self.synchronization_subchain_event.wait(30)
        self.synchronization_subchain_event = threading.Event()
        return self.synchronization_chain

    def send_n2_subchain(self, conn, obj):
        chain = bytes(Transmission.list_to_json(obj), "utf-8")
        length = len(chain)
        # send prefix, length of data and chain. ! and & used for separation
        conn.send(b'\x34' + bytes(str(length), "utf-8") + b'&' + chain)
        core.network_log("SEND \\x34 to ", conn)
        print("{}: Subchain sent \n".format(self.get_time()))
        # conn.send(b'\x34' + bytes(json.dumps([x.to_json() for x in obj]), "utf-8") + b'!')

    def send_n1_subchain(self, obj):
        chain = bytes(Transmission.list_to_json(obj), "utf-8")
        length = len(chain)
        for conn in self.connections:
            conn.send(b'\x35' + bytes(str(length), "utf-8") + b'&' + chain)
        print("{}: Subchain sent \n".format(self.get_time()))
        core.network_log("SEND \\x35 to ", [x for x in self.connections])

    def send_transmission(self, transmission: Transmission):
        for conn in self.connections:
            conn.send(b'\x20' + bytes(json.dumps(transmission.to_json()), "utf-8"))
        print("{}: Transmission sent \n".format(self.get_time()))
        core.network_log("SEND \\x32 to ", [x for x in self.connections])



if __name__ == '__main__':

    if len(sys.argv) < 2:
        client = Peer()
        client.connect_to_net()

    elif len(sys.argv) == 2:
        arg1 = sys.argv[1]
        client = Peer(addr=arg1)
        client.connect_to_net()
    else:
        client = Peer(addr=sys.argv[1],port=sys.argv[2])
        client.connect_to_net()

