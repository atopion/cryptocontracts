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
import urllib.request
from storage import config, storage



class Peer:
    """ A class representing a Peer of the peer-to-peer network 
        for the blockchain project cryptocontracts
    
    Attributes
    ----------
    active_connectable_addresses : list
        a list containing addresses of active peers in the net to connect to
    address_connection_pairs : dict
        a dictionary for mapping of addresses from incoming connection and outgoing connection of same peer
    client_sockets : list
        a list containing sockets over that this peer connects to other peers
    connected_peers : list
        a list containing the peers connected to this host
    connections : list
        a list containing the connection objects of the server socket
    gui_socket : socket object
        a socket for the connection to the GUI
    host_addr : (str,int)
        a tuple of the IP address and port number of this peer
    lock : lock object
        a lock object for the treading module to lock main thread
    port : int
       a port that is bound to the server socket
    server_peers : list
        a list containing addresses of peers that this peer is connected to
    sock_server : socket object
        a socket that is bound to handle the incoming connections
    synchronization_finished_event : event object
        an event for indicating finished synchronization
    synchronization_subchain_event : event object
        event for indicating subchain transmission process
        
    Methods
    -------
    clean_active_connectable_addresses()
        Removes duplicates from list containing active connectable addresses in the net
    clean_connected_peers()
        Removes duplicates from list containing connected peers to this host
    clean_connections()
        Removes duplicates from list containing connections to this host
    command_handler()
        Takes care of the user input
    connect_to_all()
        Connect to all peers in the network
    connect_to_net()
        Start performing system actions and connect to the network
    create_new_connection(addr)
        Creates a new connection to a specified address
    disconnect_from_net()
        Disconnects from the network and ends the program
    establisih_connetion()
        Esablishes a connection to the peer represented in addr
    get_active_connectable_addresses()7
        Returns the list of all active peer addresses to connect to
    get_connected_peers()
        Returns the list of all active peers connected to the this host
    get_host_addr()
        Returns the IP address of this host
    get_peers_from_ip_server()
        Gets the addresses of the active nodes in the network from the IP server
    get_server_peers()
        Returns addresses of peers that this peer is connected to
    get_time()
        Returns the current local time
    gui_handler()
        Handels connection to the GUI
    incoming_connection_handler(conn, addr)
        Manages connections to other peers
    listen_for_connections()
        Makes sure that peers can connect to this host
    outgoing_connection_handler(address, sock)
        Maintains outgoing connection from this peer to another node in the net
    refresh_connections()
        Pulls the current active peers in a specific period and connects to them
    request_subchain(msg, hash)
        Request specific subchain from all connected peer
    send_n1_subchain(obj)
        Send own subchain that is ahead of other peer to promote own chain
    send_n2_subchain(conn, obj) 
        Send own subchain to requester
    send_port(address, socket)
        Sends address with port number for establishing connection to this host
    send_synchronize_request()
        Send a synchronization request to all connected peers
    send_sync_request_answer(conn, obj)
        Send last transmission hash of own chain
    send_transmission(transmission)
        Send a block to all connected peers in the net
    set_host_addr()
        Sets the IP address and the port of this host
    """
    
    active_connectable_addresses = []   # addresses of active peers in the net to connect to
    address_connection_pairs = {}   # mapping of addresses from incoming connection and outgoing connection of same peer
    client_sockets = []     # sockets over that this peer connects to other peers
    BUFFERSIZE = 4096   # buffersize for data length when receiving over sockets
    connected_peers = []    # Addresses of peers connected to this host
    connections = []    # holds connection objects of the server socket
    gui_socket = None   # socket for connection to the GUI 
    host_addr = None    # IP adresses and port number of this peer
    lock = threading.Lock()     # To lock main thread after establishing connections and creating threadds for different tasks
    port = None     # port that is bind to socket for incoming connections
    server_peers = []   # addresses of peers that this peer is connected to
    sock_server = None      # socket for incoming connections
    
    synchronization_finished_event = threading.Event()  # event for indicating finished synchronization
    synchronization_subchain_event = threading.Event()  # event for indicating subchain transmission process

    def __init__(self,addr=None, port=None, list_chain=None, send_sync_message=None, send_subchain_message=None,
                 start_sync=None, receive_subchain_message=None, receive_message=None, scope=None, output=None):
        
        # methods giving or transmitting blockchain information
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
            
        # define system output
        if output == "user" or output == "debug":
            self.output = output
        elif output == None:
            self.output = "user"
        else:
          print("{} is not a valid statement for output. Either put user or debug".format(output))
          sys.exit(0)  

        self.lock.acquire()     # bring lock in locked status          
          

    def clean_active_connectable_addresses(self):
        """ Removes duplicates from list containing active connectable addresses in the net
        """

        if len(self.active_connectable_addresses) > 1:
            i = 0
            for addr in self.active_connectable_addresses:
                j = 0
                for other in self.active_connectable_addresses[i+1:]:
                    if addr[0] == other[0] and int(addr[1]) == int(other[1]):
                        self.active_connectable_addresses.pop(j)
                        j -= 1  # list gets smaller due to pop
                    j += 1
                i += 1

    def clean_connected_peers(self):
        """ Removes duplicates from list containing connected peers to this host
        """

        if len(self.connected_peers) > 1: 
            i = 0
            for addr in self.connected_peers:
                j = 0
                for other in self.connected_peers[i+1:]:
                    if addr[0] == other[0] and int(addr[1]) == int(other[1]):
                        self.connected_peers.pop(j)
                        j -= 1
                    j += 1
                i += 1

    def clean_connections(self):
        """ Removes duplicates from list containing connections to this host
        """
        
        if len(self.connections) > 1:
            i = 0
            for addr in self.connections:
                j = 0
                for other in self.connections[i+1:]:
                    if addr[0] == other[0] and int(addr[1]) == int(other[1]):
                        self.connections.pop(j)
                        j -= 1
                    j += 1 
                i += 1

    def command_handler(self):
        """ Takes care of the user input. 
        
        The user can choose from various options to display information or perform actions.
        """
        
        help_text = "The following system commands are available: \n" \
        + "client/connections: displays the peers connected to this host \n" \
        + "connectable:        displays the addresses of the active peers to that a connection can be established \n" \
        + "exit/quit/close     disconnects from the network and end the program \n" \
        + "help:               displays input possiblities for performing actions or displaying information \n" \
        + "host:               displays address of this host to which other peers can connect to \n" \
        + "list:               displays the blockchain currently stored in own database \n" \
        + "pairs:              displays the matching between the socket address incoming connections of a peer and its socket address over that it is connected to this peer \n" \
        + "servers:            displays the addresses of the peers to that this host is connected \n" \
        + "sync:               start synchronization process of blockchain \n"
        
        while True:
            try:

                i = input()
                if i == "clients":
                    p = self.get_connected_peers()
                    print(p)
                elif i == "connectable":
                    p = self.get_active_connectable_addresses()
                    print(p)
                elif i == "connections":
                    p = self.get_connected_peers()
                    print(p)
                elif i == "exit" or i == "quit" or i == "close":
                    self.disconnect_from_net()
                elif i == "help":
                    print(help_text)
                elif i == "host":
                    p = self.host_addr
                    print(p[0]+":"+str(p[1]))
                elif i == "list":   # display the current chain
                    if self.cb_list_chain is not None:
                        self.cb_list_chain()
                elif i == "pairs":
                    print(self.address_connection_pairs)
                elif i == "servers":
                    p = self.get_server_peers()
                    print(p)
                elif i == "sync":   # start synchronization process
                    if self.cb_start_sync is not None:
                        print("{}: Starting synchronization...".format(self.get_time()))
                        self.cb_start_sync()
                else:   # send message
                    for connection in self.connections:
                        connection.send(bytes(str(i),'utf-8'))

            except EOFError:
                os._exit(1)
            except KeyboardInterrupt:
                os._exit(1)
                
    def connect_to_all(self):
        """ Connect to all peers in the network
        
        Function is called after host gets addresses from the IP server.
        If system is used in same LAN or on same computer it is checked 
        that this host only connects to addresses in that scope.
        """
        
        host_net = self.host_addr[0].split(".")     # IP address of this host
        
        print("{}: Starting to connect to all peers in the net \n".format(self.get_time()))
        for peer in self.active_connectable_addresses:
            if self.scope == "internal" or self.scope == "localhost":
                peer_net = peer[0].split(".")
                if  (peer_net[0] == host_net[0]):   # check if peers are in same LAN
                    self.create_new_connection(peer)
            else:
                self.create_new_connection(peer)                
    
    def connect_to_net(self):
        """ Start performing system actions and connect to the network
        
        A new thread is started that runs the command_handler function
        for user input handling. A socket is created listening for connections.
        Another thread is created enabling the communication to the GUI.
        The IP address and the port number of this host are added to IP server.
        Moreover, the addresses of the active nodes in the network are requested from the IP server.
        Next, connections to all active peers are established and a periodically refreshing of the 
        active peers in the network is set up. Lastly, the main thread is locked to keep this
        system running and avoid looping.
        """
        
        # start command handler for user input
        command_thread = threading.Thread(target=self.command_handler)
        command_thread.daemon = True
        command_thread.start()
        
        # start to accept connections
        server_thread = threading.Thread(target=self.listen_for_connections)
        server_thread.daemon = True
        server_thread.start()
        
        # prepare for interaction with GUI for adding a document to the chain
        gui_thread = threading.Thread(target=self.gui_handler)
        gui_thread.daemon = True
        gui_thread.start()
        
        time.sleep(1)    # so server_thread has time to bind socket and assign port
        self.set_host_addr()    # set IP address and port number of this peer
        
        print("Enter help for list of commands \n")
        
        if self.output == "debug":
            print("{}: Host address: {}".format(self.get_time(),self.host_addr))
        
        if self.scope == "internal":    # For nodes in the same network
            ip_server.add_self_internal(*self.host_addr)
            if self.output == "debug":
                print("{}: Using internal mode".format(self.get_time()))
                
        elif self.scope == "localhost":     # For running multiple peers on same computer (only for testing purpose)
            ip_server.add_self_internal(*self.host_addr)
            if self.output == "debug":
                print("{}: Starting network on localhost".format(self.get_time()))
                
        else:
            ip_server.add_self(self.port)   # add port number for incoming connections to IP server
            
        print("{}: Host address added to IP Server".format(self.get_time()))
        print("{}: Host now accepts connections".format(self.get_time()))
        
        self.active_connectable_addresses = self.get_peers_from_ip_server()     # Pull active peer addresses from IP server
        if self.output == "debug":
            print("{}: Pulling active nodes from IP server".format(self.get_time()))
            print("{}: Active nodes in the network: {}".format(self.get_time(),self.active_connectable_addresses))
        
        self.connect_to_all()   # establish connection to every active node in the network

        # periodically aks for current active addresses at IP server
        refreshing_thread = threading.Thread(target=self.refresh_connections)
        refreshing_thread.daemon = True
        refreshing_thread.start()
        
        self.lock.acquire()  # lock main thread

    def create_new_connection(self, addr):
        """ Creates a new connection to a specified address

        A new socket is created. Over that a connecetion to the passed address is established
        The connection is managed in a separate thread. If connection is not possible print notification.

        Parameters
        ----------
        addr : (str,int)
           A tuple of IP address and port to which a connection should be established

        Returns
        -------
        connected : boolean
           a variable stating if connection was succesfully created
        """

        existing = False    # indicate if already connected to addr
        own = False     # indicate if addr is its own
        for peer in self.server_peers:
            if (peer[0] == addr[0] and int(peer[1]) == int(addr[1])):
                existing = True     # already connected to addr
            
        if addr[0] == self.host_addr[0] and int(addr[1]) == int(self.host_addr[1]):
                own = True  # addr is own address
                
        connected = False
        if not (existing or own):
            try:
                if self.output == "debug":
                    print("{}: Trying to connect to {}:{}...".format(self.get_time(),addr[0],addr[1]))
                connecting_thread = threading.Thread(target=self.establish_connection,args=(addr,))
                connecting_thread.daemon = True
                connecting_thread.start()
                connecting_thread.join(timeout=5)  # if not able to connect after certain amout of time, terminate thread
                for peer in self.server_peers:
                    # if addr is in list connection was successful
                    if (peer[0] == addr[0] and int(peer[1]) == int(addr[1])):
                        existing = True
                        break
                # if addr is not in list, connection failed
                if not existing:
                    if self.output == "debug":
                        print("{}: Could not connect to {}:{} due to a timeout".format(self.get_time(),addr[0],str(addr[1])))
                connected = True
            except Exception as e:
                print("{}: Could not connect to {}:{} \n Reason: {}".format(self.get_time(),addr[0],str(addr[1]),e))

        return connected
    
    def disconnect_from_net(self):
        """ Disconnects from the network and ends the program
        
        Own address is removed from IP server
        The sockets used for outgoing connections
        are shutdown and closed which causes a disconnection.
        The connection to the GUI is cut and the 
        main thread is unlocked causing the program to end.
        """

        ip_server.delete(self.host_addr[0])     # remove own address from IP server

        # close sockets for outgoing connections
        for sock in self.client_sockets:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        
        # close socket for incoming connections. Catch error occuring if program ended before socket created
        try:
            self.sock_server.shutdown(socket.SHUT_RDWR)
            self.sock_server.close()
        except OSError:
            pass
        
        # close connection to GUI. Catch error occuring if program before socket created
        try:
            self.gui_socket.shutdown(socket.SHUT_RDWR)
            self.gui_socket.close()
        except OSError:
            pass
        
        self.lock.release()     #unlock main thread

    def establish_connection(self,addr):
        """ Esablishes a connection to the peer represented in addr
        
        Creates a socket and connects it to addr. Connection is handled in dedicated thread.
        
        Parameters
        ----------
        addr : (str,int)
            a tuple containing IP address and port number
        """
        
        connected = False
        try:
            # create socket and connect to address
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)
            connected = True    # connection was successful
        # several reasons for connection failure
        except (ConnectionRefusedError, TimeoutError, BlockingIOError, OSError):
            connected = False
        # After succes add socket and addr in lists and maintain connections
        if connected:
            self.server_peers.append(addr)
            self.client_sockets.append(sock)
            thread = threading.Thread(target=self.outgoing_connection_handler, args=(addr,sock))
            thread.daemon = True
            thread.start()
            print("{}: Connected to {}:{} \n".format(self.get_time(),addr[0], str(addr[1])))
        
    def get_active_connectable_addresses(self):
        """ Returns the list of all active peer addresses to connect to

        The peer IP addresses and port numbers are taken from the object variable active_connectable_addresses and are joined in a String

        Returns
        -------
        string
            a string representing the addresses of the currently connected peers
        """

        p = ""

        if self.active_connectable_addresses:
            p = self.active_connectable_addresses[0][0] + ":" + str(self.active_connectable_addresses[0][1])

            for peer in self.active_connectable_addresses[1:]:
                p = p +  "," + peer[0] + ":" + str(peer[1])

        return p

    def get_connected_peers(self):
        """ Returns the list of all active peers connected to the this host
        
        The peer IP addresses are taken from the object variable connected_peers and are joined in a String
        
        Returns
        -------
        string
            a string representing the addresses of the currently connected peers
        """
        
        p = ""
        
        if self.connected_peers:
            p = self.connected_peers[0][0] + ":" + str(self.connected_peers[0][1])

            for peer in self.connected_peers[1:]:
                p = p + "," + peer[0] + ":" + str(peer[1])
            
        return p
    
    def get_host_addr(self):
        """ Returns the IP address of this host

        Returns
        -------
        tuple (str,int)
            a tuple containing the IP address of this host and the port that the server socket is bound to
        """

        host_name = socket.gethostname()
        host_addr = socket.gethostbyname(host_name)

        return (host_addr, self.port)
    
    def get_peers_from_ip_server(self):
        """ Gets the addresses of the active nodes in the network from the IP server
        
        Returns
        -------
        peer_addr : list of (str,int)
            a list of IP addresses and ports of the active nodes
        """
        
        online_peers = ip_server.get_all()  # pull addresses from IP server
        peer_addr = []
        # bring into tuple format
        for peer in online_peers:
            ip = peer["ip"]
            port = int(peer["port"])
            peer_addr.append((ip,port)) 
            
        return peer_addr

    def get_server_peers(self):
        """ Returns addresses of peers that this peer is connected to

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
        """ Returns the current local time
        
        Only used for print statements,
        not related to timestamp in blockchain
        
        Returns
        -------
        time : float
            the current local time
        """
        
        time = datetime.datetime.now().time()
        
        return time
    
    def gui_handler(self):
        """ Handels connection to the GUI
        
        A dedicated socket is created to establish a connection.
        This way the actions for adding a new block that was created over
        the GUI are performed. This architecture is necessary because
        only one process can access the database. Therefore, the GUI
        requests the head of the chain and adds new blocks over this class.
        """
        
        # create socket with predefined port and address in config file
        self.gui_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gui_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)    # reuse socket
        addr = config.get("gui", "addr")
        port = int(config.get("gui", "port"))
        self.gui_socket.bind((addr, port))
        self.gui_socket.listen(1)
    
        try:
            gui_conn, gui_addr = self.gui_socket.accept()
            print("{}: GUI connected".format(self.get_time()))
        except OSError:
            pass    # program closed without GUI being connected
            
            
        while True:
            try:
                # receive commands from GUI
                data = gui_conn.recv(self.BUFFERSIZE)
                if not data:
                    if self.output == "debug":
                        print("{}: GUI closed".format(self.get_time()))
                    gui_conn.close()
                    break
                
                if self.output == "debug":
                    print("{}: From GUI received {}".format(self.get_time(),data))
                
                data = str(data, "utf-8")
                mode = int(bytes(data[0], "utf-8").hex()[0:2])
                content = data[1:]
                
                # request for last transmission hash in chain alias head
                if mode == 11:
                    if self.output == "debug":
                        print("{}: Received head of chain request from GUI".format(self.get_time()))
                    head = storage.get_head()   # get head from storage
                    gui_conn.send(b'\x21' + bytes(json.dumps(head), "utf-8"))   # send head in json format
                    if self.output == "debug":
                        print("{}: Sent head of chain to GUI".format(self.get_time()))
                        
                # request for adding a new block to the chain       
                if mode == 12:
                    if self.output == "debug":
                        print("{}: Received document upload request from GUI".format(self.get_time()))
                    content = Transmission.from_json(content)   # convert to json format
                    storage.put_block(content)  # add to local chain  
                    gui_conn.send(b'\x22')  # send acknowledgement to GUI 
                    # Publish block to the network
                    if self.cb_start_sync is not None:
                        print("{}: Starting synchronization...".format(self.get_time()))
                        self.cb_start_sync()
            
            # GUI disconnected not ordinary or not connected before closing program
            except (ConnectionResetError, ConnectionAbortedError, UnboundLocalError):
                if self.output == "debug":
                    print("{}: Lost connection to GUI".format(self.get_time()))

    def incoming_connection_handler(self, conn, address):
        """ Manages incoming connections from other peers

        It is constantly waited for incoming data in a byte stream. 
        The data is checked for prefixes and processed accordingly.
        
        
        Parameters:
        -----------
        conn : connection object
            connection of specific peer
        addr : (str, int)
            a tuple of the IP address and the port number of specific peer
        """

        while True:
            try:
                # wait for receiving data
                data = conn.recv(self.BUFFERSIZE)

                # peer disconnected
                if not data:
                    if self.output == "debug":
                        print("{}: {}:{} disconnected \n".format(self.get_time(),str(address[0]),str(address[1])))
                    conn.close()
                    try:
                        # remove connnection object from list
                        self.connections.remove(conn)
                        self.clean_connections()
                    except ValueError:
                        if self.output == "debug":
                            print("Could not remove connection from connections \n")

                    try:
                        # remove address from list
                        self.connected_peers.remove(address)
                        self.clean_connected_peers()
                    except ValueError:
                        if self.output == "debug":
                            print("Could not remove address {}:{} from connected peers \n".format(address[0],str(address[1])))
                    break
                
                if self.output == "debug":
                    print("{}: From {}:{} received {} over incoming connection handler \n".format(self.get_time(),address[0],str(address[1]),data))
                    
                # if messages are comming so close together that multiple of them are considered as one, the postfix ! indicates this
                inputs = str(data, "utf-8").split("!")

                # check each message individually
                for msg in inputs:
                    if msg != "":
                        mode = int(bytes(msg, "utf-8").hex()[0:2])  # prefix indicating purpose of message
                        if self.output == "debug":
                            print("{}: MODE {}: ".format(self.get_time(), mode))
                        core.network_log("RECEIVED \\x", mode, " from ", address[0])    # log statement
                        
                        # look for specific prefix indicating the list of active peers
                        # for matching address of incoming data and connection object to send data
                        if mode == 15:
                            rec_data = msg[1:]
                            rec_peer = rec_data.split(":")
                            # create connection to this address
                            connected = self.create_new_connection((rec_peer[0],int(rec_peer[1])))
                            self.address_connection_pairs.update({rec_data:conn})   # match connection from and to this peer
                            if self.output == "debug":
                                print("{}: Address-connection pair added".format(self.get_time()))
                            if connected:
                                # connection successful
                                self.active_connectable_addresses.append((rec_peer[0],rec_peer[1]))

#                        # received a block
#                        elif mode == 20:
#                            print("{}: Received transmission from {}:{}".format(self.get_time(), address[0], int(address[1])))
#                            self.cb_receive_message(Transmission.from_json(msg[1:]))
#
#                        # Synchronization request
#                        elif mode == 31:
#                                print("{}: Received synchronization request from {}:{}".format(self.get_time(), address[0], int(address[1])))
#                                if self.cb_send_sync_message is not None:
#                                    self.cb_send_sync_message(conn)     # send head of own chain to requester
#
#                        # Synchronization answer
#                        elif mode == 32:
#                            print("{}: Received synchronization answer from {}:{}".format(self.get_time(), address[0], int(address[1])))
#                            data = json.loads(str(msg[1:]))
#                            data["conn"] = conn
#                            self.synchronization_request_answers.append(data)
#                            if len(self.synchronization_request_answers) == len(self.connected_peers):
#                                # already have same chain
#                                self.synchronization_finished_event.set()
#
#                        # Subchain request
#                        elif mode == 33:
#                            print("{}: Received subchain request from {}:{}".format(self.get_time(), address[0], int(address[1])))
#                            hash = str(msg[1:])
#                            if self.cb_send_subchain_message is not None:
#                                self.cb_send_subchain_message(conn, hash)   # send subchain that is coming afterreceived hash
#                                
#                        # received subschain 
#                        elif mode == 34 or mode == 35:
#                            print("{}: Received subchain from {}:{}".format(self.get_time(), address[0], int(address[1])))
#                            try:
#                                rec_data = msg[1:].split("&")   # indicator & separates length and actual message of subchain
#                                length = int(rec_data[0])
#                                all_data = rec_data[1]
#                                while len(all_data) < length:   # if message longer than buffersize keep receiving until message complete
#                                    to_read = length - len(all_data)
#                                    all_data += str(conn.recv(self.BUFFERSIZE if to_read > self.BUFFERSIZE else to_read), "utf-8")
#
#                                # Subchain answer
#                                if mode == 34:
#                                    # start adding to chain process
#                                    self.synchronization_chain = core.core.Transmission.list_from_json(
#                                        all_data.replace("\\", ""))     # bring into right format
#                                    self.synchronization_subchain_event.set()
#
#                                # synchronizing node has more transmissions than the synchronizing partners
#                                else:
#                                    self.synchronization_chain = core.core.Transmission.list_from_json(
#                                        all_data.replace("\\", ""))     # bring into right format
#                                    if self.cb_receive_subchain_message is not None:    # start synchronizing
#                                        self.cb_receive_subchain_message(self.synchronization_chain)
#
#                            except Exception as e:
#                                if self.output == "debug":
#                                    print("{}: Could not receive subchain".format(self.get_time()))
#                                    print("{}: Reason: {} \n".format(self.get_time(),e))

                        # if no prefix consider data a message and print it
                        else:
                            print("{}: Message from {}:{} : {}".format(self.get_time(),address[0], int(address[1]),msg))

            # connection closed unordinarily
            except (ConnectionResetError, ConnectionAbortedError):
                if self.output == "debug":
                    print("{}: {}:{} Connection impolitely closed.".format(self.get_time(), address[0],str(address[1])))
                    
                # remove address and connection from lists
                try:
                    self.connections.remove(conn)
                    self.clean_connections()
                except ValueError:
                    if self.output == "debug":
                        print("Could not remove connection from connections \n")

                try:
                    self.connected_peers.remove(address)
                    self.clean_connected_peers()
                except ValueError:
                    if self.output == "debug":
                        print("Could not remove address {}:{} from connected peers \n".format(address[0],str(address[1])))

    def listen_for_connections(self):
        """ Start socket for accepting incoming connections
        
        The port is chosen based on scipe of the system.
        For odinary usage (external mode) the port number is 
        specified in the configuration fule. The socket is then
        created and starts listening for incoming connections.
        The conncetion requests are excepted and each connetion handled in 
        a dedicated thread.
        """
        
        while True:
            # check if port for localhost mode is alredy used
            try:
                self.sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock_server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)    # reuse socket
                if self.scope == "localhost" or self.scope == "internal":   # if starting multiple peers on same computer take random port (only for testing)
                    self.port = random.randint(10001,15000)
                if self.scope == "external":
                    self.port = int(config.get("server", "port"))    # get port from config file
                self.sock_server.bind(('0.0.0.0',self.port))
                self.sock_server.listen(1)  # start listening for incoming connections
                break
            except OSError:
                if self.output == "debug":
                    print("{}: Randomly chosen port number already taken, choosing different number".format(self.get_time()))
        
        while True:
            try:
                conn, addr = self.sock_server.accept()  # accept incoming connection request
                thread = threading.Thread(target=self.incoming_connection_handler, args=(conn,addr))    # handle input from client in dedicated thread
                thread.daemon = True
                thread.start()
                self.connected_peers.append(addr)   # save address
                self.connections.append(conn)   # save connection object
                self.clean_connected_peers()    # remove duplicates
                print("{}: {}:{} connected \n".format(self.get_time(),str(addr[0]),str(addr[1])))
            except OSError:
                if self.output == "debug":
                    print("{}: Issues with server socket".format(self.get_time()))
                
    def outgoing_connection_handler(self, address, sock):
        """ Manages outgoing connections to other peers

        It is constantly waited for incoming data in a byte stream. 
        The data is checked for prefixes and processed accordingly.
        
        
        Parameters:
        -----------
        addr : (str, int)
            a tuple of the IP address and the port number of specific peer
        sock : socket object
            a socket object managing connection to peer of address
        """

        self.send_port(address, sock)   # for matching of address and connection

        while True:
            try:
                # wait for incoming data
                data = sock.recv(self.BUFFERSIZE)
                
                # connection closed
                if not data:
                    
                    # remove address from list
                    try:
                        self.server_peers.remove(address)
                    except:
                        if self.output == "debug":
                            print("{}: Could not remove server peer: {}:{} from server list".format(self.get_time(), address[0],str(address[1])))
                            
                    # remove address from list
                    try:
                        self.active_connectable_addresses.remove(address)
                    except:
                        if self.output == "debug":
                            print("{}: Could not remove server peer: {}:{} from active connectable address list".format(self.get_time(), address[0],str(address[1])))

                    # remove connection pairs from list
                    try:
                        self.address_connection_pairs.pop(str(address[0]+":"+str(address[1])))
                    except:
                        if self.output == "debug":
                            print("{}: Could not remove address from address connection pair dict".format(self.get_time()))

                    try:
                        self.client_sockets.remove(sock)
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()
                    except OSError:
                        print("{}: socket could not be closed properly".format(self.get_time()))
                    break
                
                if self.output == "debug":
                    print("{}: From {}:{} received {}".format(self.get_time(),address[0],str(address[1]),data))


                 # if messages are coming so close together that multiple of them are considered as one, the postfix ! indicates this
                inputs = str(data, "utf-8").split("!")

                # check each message individually
                for msg in inputs:
                    if msg != "":
                        mode = int(bytes(msg, "utf-8").hex()[0:2])  # prefix indicating purpose of message
                        if self.output == "debug":
                            print("{}: MODE {}: ".format(self.get_time(), mode))
                        core.network_log("RECEIVED \\x", mode, " from ", address[0])    # log statement

                        # look for specific prefix indicating the list of active peers

                         # received a block
                        if mode == 20:
                            print("{}: Received transmission from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            self.cb_receive_message(Transmission.from_json(msg[1:]))

                        # Synchronization request
                        elif mode == 31:
                                print("{}: Received synchronization request from {}:{}".format(self.get_time(), address[0], int(address[1])))
                                if self.cb_send_sync_message is not None:
                                    self.cb_send_sync_message(self.address_connection_pairs[str(address[0]+":"+str(address[1]))])     # send head of own chain to requester

                        # Synchronization answer
                        elif mode == 32:
                            print("{}: Received synchronization answer from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            data = json.loads(str(msg[1:]))
                            data["conn"] = self.address_connection_pairs[str(address[0]+":"+str(address[1]))]
                            self.synchronization_request_answers.append(data)
                            if len(self.synchronization_request_answers) == len(self.connected_peers):
                                # already have same chain
                                self.synchronization_finished_event.set()

                        # Subchain request
                        elif mode == 33:
                            print("{}: Received subchain request from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            hash = str(msg[1:])
                            if self.cb_send_subchain_message is not None:
                                self.cb_send_subchain_message(self.address_connection_pairs[str(address[0]+":"+str(address[1]))], hash)   # send subchain that is coming after received hash
                                
                        # received subschain 
                        elif mode == 34 or mode == 35:
                            print("{}: Received subchain from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            try:
                                rec_data = msg[1:].split("&")   # indicator & separates length and actual message of subchain
                                length = int(rec_data[0])
                                all_data = rec_data[1]
                                while len(all_data) < length:   # if message longer than buffersize keep receiving until message complete
                                    to_read = length - len(all_data)
                                    all_data += str(sock.recv(self.BUFFERSIZE if to_read > self.BUFFERSIZE else to_read), "utf-8")

                                # Subchain answer
                                if mode == 34:
                                    # start adding to chain process
                                    self.synchronization_chain = core.core.Transmission.list_from_json(
                                        all_data.replace("\\", ""))     # bring into right format
                                    self.synchronization_subchain_event.set()

                                # synchronizing node has more transmissions than the synchronizing partners
                                else:
                                    self.synchronization_chain = core.core.Transmission.list_from_json(
                                        all_data.replace("\\", ""))     # bring into right format
                                    if self.cb_receive_subchain_message is not None:    # start synchronizing
                                        self.cb_receive_subchain_message(self.synchronization_chain)

                            except Exception as e:
                                if self.output == "debug":
                                    print("{}: Could not receive subchain".format(self.get_time()))
                                    print("{}: Reason: {} \n".format(self.get_time(),e))

                        # if no prefix consider data a message and print it
                        else:
                            print("{}: Message from {}:{} : {}".format(self.get_time(), address[0], int(address[1]), msg))

            # connection closed unordinarily
            except (ConnectionResetError, ConnectionAbortedError):
                if self.output == "debug":
                    print("{}: {}:{} impolitely disconnected.".format(self.get_time(), address[0],str(address[1])))
                    
                # remove address and connection pair from list
                try:
                    self.server_peers.remove(address)
                except:
                    if self.output == "debug":
                        print("{}: Could not remove server peer: {}:{} from server list".format(self.get_time(), address[0],str(address[1])))
                try:
                    self.active_connectable_addresses.remove(address)
                except:
                    if self.output == "debug":
                        print("{}: Could not remove server peer: {}:{} from active connectable address list".format(self.get_time(), address[0],str(address[1])))
                try:
                    self.address_connection_pairs.pop(str(address[0]+":"+str(address[1])))
                except:
                    if self.output == "debug":
                        print("{}: Could not remove address from address connection pair dict".format(self.get_time()))

    def refresh_connections(self):
        """ Pulls the current active peers in a specific period and connects to them
        
        The addresses from the active peers in the network are pulled from the IP Server.
        The frequency of requesting is defined in REF_FREQ.
        If a peer belonging to the newly received address is not the own host address
        and there is not yet a connection established to, it is tried to connect to it.
        """
        
        host_net = self.host_addr[0].split(".")  # local network address of host
        
        while True:
            REF_FREQ = 300  # refreshing-frequency in seconds
            time.sleep(REF_FREQ)
            if self.output == "debug":
                print("{}: Refreshing connections...".format(self.get_time()))
            self.active_connectable_addresses = self.get_peers_from_ip_server()
            
            if self.output == "debug":
                print("{}: Active nodes: {}".format(self.get_time(),self.active_connectable_addresses))
                
            for on in self.active_connectable_addresses:
                # check if address in same network and if it is its own address
                own = False
                same_net = True
                if on[0] == self.host_addr[0] and int(on[1]) == int(self.host_addr[1]):
                    own = True  # own address of host
                else:
                    # if using in same LAN or on same computer make sure to just connect to addresses in that scope (only for testing)
                    if self.scope == "internal" or self.scope == "localhost":
                        peer_net = on[0].split(".")
                        if not (peer_net[0] == host_net[0]):   # not in same LAN
                            same_net = False
                            
                # same_net must be true in any case to establish the connection  
                # check if already connected to that address
                if (not own) and same_net:
                    existing = False
                    for peer in self.server_peers:
                        if on[0] == peer[0] and int(on[1]) == int(peer[1]):
                            existing = True
                      
                    if not existing:    # only connect to new peers
                        self.create_new_connection(on)

#    def send_offline_peer(self, address):
#       """ Sends notification to all connected peers that another peer went offline
#       Sends the address of its client socket over that it was connected to this host
#
#       Parameters
#       ----------
#       address : (str,int)
#           tuple of IP address and port number of peer that went offline
#       """
#
#       p = address[0] + ":" + str(address[1])
#       for peer in self.connections:
#            peer.send(b'\x13' + bytes(p, "utf-8") + b'!')
#       core.network_log("SEND \\x13 to ", [x for x in self.connections])
#       if self.output == "debug":
#           print("Notified connected peers that {} is offline".format(p))

#    def send_offline_connectable_address(self, address):
#        """ Sends notification to all connected peers that another peer went offline.
#        Sends the address of its connectable address
#
#        Parameters
#        ----------
#        address : (str,int)
#        tuple of IP address and port number of peer that went offline
#        """
#
#        p = address[0] + ":" + str(address[1])
#        for peer in self.connections:
#            peer.send(b'\x14' + bytes(p, "utf-8") + b'!')
#        core.network_log("SEND \\x14 to ", [x for x in self.connections])
#        if self.output == "debug":
#            print("Notified connected peers that {} is offline".format(p))

    def request_subchain(self, msg, hash):
        """ Request specific subchain from all connected peer
            
        Send specific prefix and latest transmission hash own chain
        to peer represented by msg.
        
        Parameters
        ----------
        msg : dict
            a dictionary containing information about specific peer
        hash : latest transmission hash of own chain
        
        Return
        ------
        self.synchronization_chain : list of chain objects
            a list containing the subchains of the other peers
        """
        
        WAIT_DUR = 30   # waiting duration in seconds
        
        self.synchronization_chain = None
        msg["conn"].send(b'\x33' + bytes(hash, "utf-8"))
        print("{}: Subchain requested".format(self.get_time()))
        core.network_log("SEND \\x33 to ", msg["conn"]) # log statement
        self.synchronization_subchain_event.wait(WAIT_DUR)    # wait specific time to receive answers
        self.synchronization_subchain_event = threading.Event()     # reset event
        return self.synchronization_chain

    def send_n1_subchain(self, obj):
        """ Send own subchain that is ahead of other peer to promote own chain
        
        Transform chain object to json and then to bytes and add the length of 
        the whole transformed chain and send it to all connected peers.
        
        Parameters
        ----------
        obj : str
            the subchain that shall be send
        """
        
        chain = bytes(Transmission.list_to_json(obj), "utf-8")
        length = len(chain)
        # send prefix, length of data and chain. & used for separation
        for conn in self.connections:
            conn.send(b'\x35' + bytes(str(length), "utf-8") + b'&' + chain)
        print("{}: Subchain sent \n".format(self.get_time()))
        core.network_log("SEND \\x35 to ", [x for x in self.connections])   # log statement
        
    def send_n2_subchain(self, conn, obj):
        """ Send own subchain to requester 
        
        Transform chain object to json and then to bytes and add the length of 
        the whole transformed chain and send it to peer.
        
        Parameters
        ----------
        conn : connection object
            connection object belonging to peer
        obj : str
            subchain that shall be send
        """
        
        chain = bytes(Transmission.list_to_json(obj), "utf-8")  # convert to json and to bytes
        length = len(chain) 
        # send prefix, length of data and chain. & used for separation
        conn.send(b'\x34' + bytes(str(length), "utf-8") + b'&' + chain)
        print("{}: Subchain sent \n".format(self.get_time()))
        core.network_log("SEND \\x34 to ", conn)    # log statement
        
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
            core.network_log("SEND \\x15 to ", socket)  # log statement
        else:
            address.send(b'\x15' + bytes(p, "utf-8") + b'!')
            core.network_log("SEND \\x13 to ", address) # log statement
        
        if self.output == "debug":
            print("{}: Own address sent to {}:{}".format(self.get_time(), address[0], str(address[1])))
        
    def send_synchronize_request(self):
        """ Send a synchronization request to all connected peers
        
            Send request to all peers that this host is connected to
            and wait for their answers. The other peers reply with the latest
            transmission hash in their chain.
            
            Return
            ------
            res : list
                a list of the last transmission hashes of all connected peers 
        """
        
        # send request  to all connections
        for conn in self.connections:
            conn.send(b'\x31!')

        WAIT_DUR = 30   # waiting duration in seconds

        print("{}: Synchronization request sent".format(self.get_time()))
        self.synchronization_finished_event.wait(WAIT_DUR)  # finish synchronization requesting process after specifinc time
        res = self.synchronization_request_answers  # answers of all peers
        self.synchronization_request_answers = []   # clear list
        self.synchronization_finished_event = threading.Event()     # reset event
        core.network_log("SEND \\x31 to ", [x for x in self.connections])   # log statement
        return res
        
    def send_sync_request_answer(self, conn, obj):
        """ Send last transmission hash of own chain 
        
        Parameters
        ----------
        conn: connection object 
            a connection object of the connection to a specific peer
        obj: str
            transmission hash of latest block in the own chain
        """
        
        conn.send(b'\x32' + bytes(json.dumps(obj), "utf-8"))    # send latest transmission hash to peer belonging to conn
        print("{}: Synchronization request answer sent".format(self.get_time()))
        core.network_log("SEND \\x32 to ", conn)    # log statement

    def send_transmission(self, transmission: Transmission):
        """ Send a block to all connected peers in the net
        
        Parameters
        ----------
        transmission : Transmission object
            a block from the blockchain
        """
        
        for conn in self.connections:
            # add prefix, transform to json and bytes and send to all connected peers
            conn.send(b'\x20' + bytes(json.dumps(transmission.to_json()), "utf-8"))
        print("{}: Transmission sent".format(self.get_time()))
        core.network_log("SEND \\x20 to ", [x for x in self.connections])   # log statement
        
    def set_host_addr(self):
        """ Sets the IP address and the port of this host
        """
    
        # if using on same computer use random loopback address
        # because IP server stores as key value pairs and overwrites if same address (only for testing)
        if self.scope == "localhost":
            num1 = random.randint(0,199)
            num2 = random.randint(0,199)
            num3 = random.randint(0,199)
            host_addr = "127." + str(num1) + "." + str(num2) + "." + str(num3)
        
        # if using in same LAN use local IP
        elif self.scope == "internal":
            host_name = socket.gethostname()
            host_addr = socket.gethostbyname(host_name)

        else:
            # get loating IP address of this host (only for testing)
            host_addr = urllib.request.urlopen("https://api.zipixx.com/forwardedfor").read().decode("utf-8")

        self.host_addr = (host_addr,self.port)  


