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
from network import ip_server
from core import core
from core.transmission import Transmission
#from upnp import upnp
import urllib.request
from storage import config



class Peer:
    """ A class representing a Peer of the network which connects to the server
    
    Attributes
    ----------
    active_peers : list
        a list containing all peers that are currently connected to the network
    connected_peers : list
        a list containing the peers connected to this host
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
    set_host_addr()
        Sets a variable for the IP address and the port of this host
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
    last_addresses = []
    lock = threading.Lock()     # To lock main thread after establishing connection
    port = None
    server_address = None
    server_peers = []
    sock_server = None
    sock_client = None
    standalone = False  # If true start host without connecting
    client_sockets = []
    address_connection_pairs = {}
    host_addr = None
    

    synchronization_finished_event = threading.Event()
    synchronization_subchain_event = threading.Event()

    def __init__(self,addr=None, port=None, list_chain=None, send_sync_message=None, send_subchain_message=None,
                 start_sync=None, receive_subchain_message=None, receive_message=None, scope=None):
        
        self.cb_list_chain = list_chain
        self.cb_start_sync = start_sync
        self.cb_send_sync_message = send_sync_message
        self.cb_send_subchain_message = send_subchain_message
        self.cb_receive_message = receive_message
        self.cb_receive_subchain_message = receive_subchain_message

        self.synchronization_chain = []
        self.synchronization_request_answers = []
        
        # Tell where peers are located, in WAN or in LAN
        if scope == "external" or scope == "internal" or scope == "localhost":
            self.scope = scope
        elif scope == None:
            self.scope = "external"
        else:
            print("{} is not a valid statement for scope. Either assign external, internal or localhost for the scope corresponding to the network".format(scope))
            sys.exit(0)

    def clean_active_connectable_addresses(self):
        """ Removes duplicates from list containing active connectable addresses in the net
        """
        # TODO make sure that it is not possible that an address is appended while cleaning

        if len(self.active_connectable_addresses) > 1:
            i = 0
            for addr in self.active_connectable_addresses:
                j = 0
                for other in self.active_connectable_addresses[i+1:]:
                    if addr[0] == other[0] and int(addr[1]) == int(other[1]):
                        self.active_connectable_addresses.pop(j)
                        j -= 1  # list gets smaller due to pop
                    j +=1
                i +=1

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
                elif i == "sync":
                    if self.cb_start_sync is not None:
                        self.cb_start_sync()
                elif i == "list":
                    if self.cb_list_chain is not None:
                        self.cb_list_chain()
                elif i == "host":
                    p = self.host_addr
                    print(p[0]+":"+str(p[1]))
                elif i == "clean":
                    self.clean_active_peers()
                    self.clean_connected_peers()
                elif i == "pairs":
                    print(self.address_connection_pairs)
                else:
                    for connection in self.connections:
                        connection.send(bytes(str(i),'utf-8'))

            except EOFError:
                os._exit(1)
            except KeyboardInterrupt:
                os._exit(1)
                
    def connect_to_all(self):
        """ Connect to all peers in the network
        
        Function is called after host gets addresses from the IP server after starting.
        """
        
        host_net = self.host_addr[0].split(".")
        
        print("{}: Starting to connect to all peers in the net \n".format(self.get_time()))
        for peer in self.active_connectable_addresses:
            if self.scope == "internal" or self.scope == "localhost":
                peer_net = peer[0].split(".")
#                print("PEER NET: {}".format(peer_net[0]))
#                print("HOST NET: {}".format(host_net[0]))
                if  (peer_net[0] == host_net[0]):   # not in same LAN
#                    print("{}: Connecting to {}:{} \n".format(self.get_time(),peer[0],peer[1]))
                    self.create_new_connection(peer)
            else:
#                print("{}: Connecting to {}:{} \n".format(self.get_time(),peer[0],peer[1]))
                self.create_new_connection(peer)                
    
    def connect_to_net(self):
        """ Establishes connection to the server peer
        
        Sets up a socket and connects to the server peer. A new thread is started
        that runs the command_handler function for user input handling.
        Data that is received is checked for special meaning by prefixes.
        If no prefix is found, it is considered a message and printed out.
        """
        
        command_thread = threading.Thread(target=self.command_handler)
        command_thread.daemon = True
        command_thread.start()
        
        server_thread = threading.Thread(target=self.listen_for_connections)
        server_thread.daemon = True
        server_thread.start()
        
        time.sleep(1)    # so server_thread has time to bind socket and assign port
        self.set_host_addr()
#        self.active_connectable_addresses.append(host_addr)
#        self.store_addresses()
        print("{}: Host address: {}".format(self.get_time(),self.host_addr))
        
        if self.scope == "internal":    # For nodes in the same network
            ip_server.add_self_internal(*self.host_addr)
            print("{}: Using internal mode".format(self.get_time()))
        elif self.scope == "localhost":
            ip_server.add_self_internal(*self.host_addr)
            print("{}: Starting network on localhost".format(self.get_time()))
        else:
            ip_server.add_self(self.port)
        print("{}: Host address added to IP Server \n".format(self.get_time()))
        
        print("{}: Host now accepts connections".format(self.get_time()))
        
        self.active_connectable_addresses = self.get_peers_from_ip_server()
        print("{}: Pulling active nodes from IP server".format(self.get_time()))
        print("{}: Active nodes in the network: {}".format(self.get_time(),self.active_connectable_addresses))
        
        
        print("{}: Trying to connect to all active nodes in the network".format(self.get_time()))
        self.connect_to_all()

        refreshing_thread = threading.Thread(target=self.refresh_connections)
        refreshing_thread.daemon = True
        refreshing_thread.start()
        
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
        own = False
        for peer in self.server_peers:
            if (peer[0] == addr[0] and int(peer[1]) == int(addr[1])):
                existing = True
            
        if addr[0] == self.host_addr[0] and int(addr[1]) == int(self.host_addr[1]):
                own = True
                
        connected = False
        if not (existing or own):
            try:
                print("{}: Trying to connect to {}:{}...".format(self.get_time(),addr[0],addr[1]))
                connecting_thread = threading.Thread(target=self.establish_connection,args=(addr,))
                connecting_thread.daemon = True
                connecting_thread.start()
                connecting_thread.join(timeout=5)  # if not able to connect after certain amout of time, terminate thread
#                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                sock.connect(addr)
#                self.server_peers.append(addr)
#                self.client_sockets.append(sock)
#                thread = threading.Thread(target=self.outgoing_connection_handler, args=(addr,sock))
#                thread.daemon = True
#                thread.start()
#                print("Connected to " + addr[0] + ":" + str(addr[1]))
                existing = False
                for peer in self.server_peers:
                    if (peer[0] == addr[0] and int(peer[1]) == int(addr[1])):
                        existing = True
                if not existing:
                    print("{}: Could not connect to {}:{} due to a timeout".format(self.get_time(),addr[0],str(addr[1])))
                
                connected = True
            except Exception as e:
                print("{}: Could not connect to {}:{} \n Reason: {}".format(self.get_time(),addr[0],str(addr[1]),e))

        return connected

    def establish_connection(self,addr):
        """ Esablishes a connection to the peer represented in addr.
        
        Creates a socket and connects it to addr. Connection is handled in dedicated thread.
        
        Parameters
        ----------
        addr : (str,int)
            tuple containing IP address and port number
        """
        connected = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)
            connected = True
        except (ConnectionRefusedError, TimeoutError, BlockingIOError):
            connected = False
        if connected:
            self.server_peers.append(addr)
            self.client_sockets.append(sock)
            thread = threading.Thread(target=self.outgoing_connection_handler, args=(addr,sock))
            thread.daemon = True
            thread.start()
            print("{}: Connected to {}:{}".format(self.get_time(),addr[0], str(addr[1])))
        
    def disconnect_from_net(self):
        """Disconnects from the network/server peer
        
        The socket is shutdown and closed which causes a disconnection.
        """

        ip_server.delete(self.host_addr[0])

        self.lock.release()     #unlock main thread
        
        for sock in self.client_sockets:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        
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
                p = p +  "," + peer[0] + ":" + str(peer[1])

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
                p = p + "," + peer[0] + ":" + str(peer[1])
            
        return p
    
    def get_peers_from_ip_server(self):
        """ Gets the addresses of the active nodes in the network from the IP Server.
        
        Returns
        -------
        peer_addr : list of (str,int)
            List of IP addresses and ports of the active nodes
        """
        
        online_peers = ip_server.get_all()
        peer_addr = []
        for peer in online_peers:
            ip = peer["ip"]
            port = int(peer["port"])
            peer_addr.append((ip,port))
            
        return peer_addr

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
        """ Returns the current time
        
        Returns
        -------
        time : float
            the current time
        """
        
        time = datetime.datetime.now().time()
        
        return time

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

        while True:
            try:

                data = conn.recv(4096)

                if not data:
                    print("{}: {}:{} disconnected \n".format(self.get_time(),str(address[0]),str(address[1])))
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
#                    self.send_offline_peer(address) # notify connected peers that one peer went offline
                    break

                print("{}: From {}:{} received {} over incoming connection handler \n".format(self.get_time(),address[0],str(address[1]),data))


                inputs = str(data, "utf-8").split("!")

                for msg in inputs:
                    if msg != "":
                        mode = int(bytes(msg, "utf-8").hex()[0:2])
#                        print("part message: ", msg)
                        print("{}: MODE {}: ".format(self.get_time(), mode))
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

                            self.clean_active_connectable_addresses()   # just for testing

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
#                                self.send_active_connectable_addresses()
#                                self.store_addresses()

                        elif mode == 15:
                            # for matching address of incoming data and connection object to send data 
                            rec_data = msg[1:]
                            rec_peer = rec_data.split(":")
                            connected = self.create_new_connection((rec_peer[0],int(rec_peer[1])))
                            self.address_connection_pairs.update({rec_data:conn})
                            print("{}: Address-connection pair added".format(self.get_time()))
                            if connected:
                                self.active_connectable_addresses.append((rec_peer[0],rec_peer[1]))

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

                            try:
                                rec_data = msg[1:].split("&")
                                length = int(rec_data[0])
                                all_data = rec_data[1]
                                while len(all_data) < length:
                                    to_read = length - len(all_data)
                                    all_data += str(conn.recv(4096 if to_read > 4096 else to_read), "utf-8")

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
                                print("{}: Could not send receive subchain".format(self.get_time()))
                                print("{}: Reason: {} \n".format(self.get_time(),e))

                            # if no prefix consider data a message and print it
                        else:
                            print("{}: Message: {}".format(self.get_time(),msg))

                            """elif mode == 34:
                                # Subchain answer
                                self.synchronization_chain = core.core.Transmission.list_from_json(str(msg[1:]).replace("\\\\", "\\"))
                                self.synchronization_subchain_event.set()
                            # if no prefix consider data a message and print it"""

            except ConnectionResetError or ConnectionAbortedError:
                print("{}: {}:{} Connection impolitly closed.".format(self.get_time(), address[0],str(address[1])))
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

    def listen_for_connections(self):
        """ Makes sure that peers can connect to this host.
        
        Creates an own thread for each incoming connection.
        """
        while True:
            try:
                self.sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock_server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                if self.scope == "localhost" or self.scope == "internal":
                    self.port = random.randint(10001,15000)
                if self.scope == "external":
                    self.port = int(config.get("server", "port"))    # get port from config file
#                upnp.add_port(self.port)
                self.sock_server.bind(('0.0.0.0',self.port))
                self.sock_server.listen(1)
                
                break
            
            except OSError:
                print("{}: Randomly chosen port numer already taken, choosing different number")
        
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
            print("\n{}: {}:{} connected \n".format(self.get_time(),str(addr[0]),str(addr[1])))
#            self.send_active_peers()
    
    def outgoing_connection_handler(self, address, sock):
        """ Maintains outgoing connection from this peer to another node in the net

        If the connection to the server node corrupts, it is looked for another node to connect to
        """

        self.send_port(address, sock)   # for matching of address and connection

        while True:
            try:
                
                data = sock.recv(4096)
                if not data:
                    try:
                        self.server_peers.remove(address)
                    except:
                        print("{}: Could not remove server peer: {}:{} from server list".format(self.get_time(), address[0],str(address[1])))

                    try:
                        self.active_connectable_addresses.remove(address)
                    except:
                        print("{}: Could not remove server peer: {}:{} from active connectable address list".format(self.get_time(), address[0],str(address[1])))

                    try:
                        self.address_connection_pairs.pop(str(address[0]+":"+str(address[1])))
                    except Exception as e:
                        print("{}: Could not remove address from address connection pair dict".format(self.get_time()))
                        print("Reason: ",e)

                    self.send_offline_connectable_address(address)  # notify other peers that one peer went offline

                    self.client_sockets.remove(sock)
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()

                    break

                print("{}: From {}:{} received {}".format(self.get_time(),address[0],str(address[1]),data))

                inputs = str(data, "utf-8").split("!")

                for msg in inputs:
                    if msg != "":
                        try:
                            mode = int(bytes(msg, "utf-8").hex()[0:2])
                        except ValueError:
                            mode = ""
#                        print("part message: ", msg)
                        print("{}: MODE {}: ".format(self.get_time(),mode))
                        core.network_log("RECEIVED \\x", mode, " from ", address[0])
                        # look for specific prefix indicating the list of active peers
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
#                                self.send_active_peers()

                        elif mode == 12:

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
#                                self.send_active_connectable_addresses()
#                                self.store_addresses()


                        elif mode == 13:
                            # peer went offline notification
                            offline_peer = msg[1:].split(":")
                            for addr in self.active_peers:
                                if offline_peer[0] == addr[0] and int(offline_peer[1]) == addr[1]:
                                    self.active_peers.remove(addr)
#                                    self.send_offline_peer(addr)
                                    break   # considering that no redundant addresses in list

                        elif mode == 14:
                            # notification that connectable address not available anymore
                            offline_peer = msg[1:].split(":")
                            for addr in self.active_connectable_addresses:
                                if offline_peer[0] == addr[0] and int(offline_peer[1]) == addr[1]:
                                    self.active_connectable_addresses.remove(addr)
#                                    self.send_offline_connectable_address(addr)
                                    break   # considering that no redundant addresses in list
                        
                        elif mode == 20:
                            self.cb_receive_message(Transmission.from_json(msg[1:]))

                        elif mode == 31:
                            # Synchronization request
                            if self.cb_send_sync_message is not None:
#                                    self.cb_send_sync_message(self.sock_client)
                                self.cb_send_sync_message(self.address_connection_pairs[str(address[0]+":"+str(address[1]))])

                        elif mode == 32:
                            # Synchronization answer
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
#                                self.cb_send_subchain_message(self.sock_client, hash)
                                self.cb_send_subchain_message(self.address_connection_pairs[str(address[0]+":"+str(address[1]))], hash)

                        elif mode == 34 or mode == 35:
                            
                            try:
                                rec_data = msg[1:].split("&")
                                length = int(rec_data[0])
                                all_data = rec_data[1]
                                while len(all_data) < length:
                                    to_read = length - len(all_data)
                                    all_data += str(sock.recv(4096 if to_read > 4096 else to_read), "utf-8")

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
                                print("{}: Could not send receive subchain".format(self.get_time()))
                                print("{}: Reason: {} \n ".format(self.get_time(),e))

                        # if no prefix consider data a message and print it
                        else:
                            print("{}: Message: {} \n".format(self.get_time(),msg))

            except ConnectionResetError or ConnectionAbortedError:
                print("{}: {}:{} impolitly disconnected.".format(self.get_time(), address[0],str(address[1])))
                try:
                    self.server_peers.remove(address)
                except:
                    print("{}: Could not remove server peer: {}:{} from server list".format(self.get_time(), address[0],str(address[1])))
                try:
                    self.active_connectable_addresses.remove(address)
                except:
                    print("{}: Could not remove server peer: {}:{} from active connectable address list".format(self.get_time(), address[0],str(address[1])))
                try:
                    self.address_connection_pairs.pop(str(address[0]+":"+str(address[1])))
                except Exception as e:
                    print("{}: Could not remove address from address connection pair dict".format(self.get_time()))
                    print("Reason: ",e)

    def refresh_connections(self):
        """ Gets the current active nodes in the network in a specific frequency"""
        
        host_net = self.host_addr[0].split(".")  # local network address of host
        
        while True:
            time.sleep(60)
            print("\n{}: Refreshing connections...".format(self.get_time()))
            self.active_connectable_addresses = self.get_peers_from_ip_server()
            
            print("{}: Active nodes: {}".format(self.get_time(),self.active_connectable_addresses))
            for on in self.active_connectable_addresses:
                own = False
                same_net = True
                if on[0] == self.host_addr[0] and int(on[1]) == int(self.host_addr[1]):
                    own = True  # own address of host
                else:
                    if self.scope == "internal" or self.scope == "localhost":
                        peer_net = on[0].split(".")
    #                    print("PEER NET: {}".format(peer_net[0]))
    #                    print("HOST NET: {}".format(host_net[0]))
                        if not (peer_net[0] == host_net[0]):   # not in same LAN
                            same_net = False
                if (not own) and same_net:
                    existing = False
                    for peer in self.server_peers:
                        if on[0] == peer[0] and int(on[1]) == int(peer[1]):
                            existing = True
                      
                    if not existing:    # only connect to new peers
                        self.create_new_connection(on)

    def get_host_addr(self):
        """ Returns the IP address of this host.

        Returns
        -------
        tuple (str,int)
            a tuple containing the IP address of this host and the port that the server socket is bound to
        """

        host_name = socket.gethostname()
        host_addr = socket.gethostbyname(host_name)

        return (host_addr, self.port)

    def send_active_connectable_addresses(self, addr=None):
        """ Sends the list of active connectable addresses to all peers connected to this host.

        The list of all active connectable addresses is taken and send over every connection as a byte stream.
        A dedicated information is output to the user.
        """
        self.clean_active_connectable_addresses()
        p = self.get_active_connectable_addresses()

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
            core.network_log("SEND \\x11 to ", [x for x in self.connections])
            print("peer list sent to all connected peers")
        else:
            print("Wanted to send active peer list but it is empty!")
    
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
       core.network_log("SEND \\x13 to ", [x for x in self.connections])
       print("Notified connected peers that {} is offline".format(p))

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
        core.network_log("SEND \\x14 to ", [x for x in self.connections])
        print("Notified connected peers that {} is offline".format(p))

    def send_port(self, address, socket=None):
        """ Sends address with port number for establishing connection to this host

        Parameters
        ----------
        address : tuple (str,int)
            IP address and port to send to
        """

        p = self.host_addr[0] + ":" + str(self.host_addr[1])

        if socket:
            socket.send(b'\x15' + bytes(p, "utf-8") + b'!')   # ! signals end of message
            core.network_log("SEND \\x15 to ", socket)
        else:
            address.send(b'\x15' + bytes(p, "utf-8") + b'!')
            core.network_log("SEND \\x13 to ", address)
        print("{}: Own address sent to {}:{}".format(self.get_time(), address[0], str(address[1])))
        
    def set_host_addr(self):
        """ Sets the IP address and the port of this host """
    
        
        if self.scope == "localhost":
            num1 = random.randint(0,199)
            num2 = random.randint(0,199)
            num3 = random.randint(0,199)
            host_addr = "127." + str(num1) + "." + str(num2) + "." + str(num3)
            
        elif self.scope == "internal":
            host_name = socket.gethostname()
            host_addr = socket.gethostbyname(host_name)

        else:
            host_addr = urllib.request.urlopen("https://api.zipixx.com/forwardedfor").read().decode("utf-8")

        self.host_addr = (host_addr,self.port)
        
    def store_addresses(self):
        """ Stores the currently active peers in the network to file
        
        """
        if not os.path.isdir("./addresses") == True:
            os.mkdir("./addresses")
            
        last_addresses = open("./addresses/last_active_addresses.txt","w")
        last_addresses.write(self.get_active_connectable_addresses())
        last_addresses.close()
            
    def send_synchronize_request(self):
        for conn in self.connections:
            conn.send(b'\x31!')

        self.synchronization_finished_event.wait(30)
        res = self.synchronization_request_answers
        self.synchronization_request_answers = []
        self.synchronization_finished_event = threading.Event()
        print("{}: Synchronization Request sent".format(self.get_time()))
        core.network_log("SEND \\x31 to ", [x for x in self.connections])
        return res

    def send_sync_request_answer(self, conn, obj):
        conn.send(b'\x32' + bytes(json.dumps(obj), "utf-8"))
        print("{}: Synchronization Request Answer sent".format(self.get_time()))
        core.network_log("SEND \\x32 to ", conn)

    def request_subchain(self, msg, hash):
        self.synchronization_chain = None
        msg["conn"].send(b'\x33' + bytes(hash, "utf-8"))
        print("{}: Subchain requested".format(self.get_time()))
        core.network_log("SEND \\x33 to ", msg["conn"])
        self.synchronization_subchain_event.wait(30)
        self.synchronization_subchain_event = threading.Event()
        return self.synchronization_chain

    def send_n2_subchain(self, conn, obj):
        chain = bytes(Transmission.list_to_json(obj), "utf-8")
        length = len(chain)
        # send prefix, length of data and chain. ! and & used for separation
        conn.send(b'\x34' + bytes(str(length), "utf-8") + b'&' + chain)
        print("{}: Subchain sent \n".format(self.get_time()))
        core.network_log("SEND \\x34 to ", conn)
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
        print("{}: Transmission sent".format(self.get_time()))
        core.network_log("SEND \\x20 to ", [x for x in self.connections])


