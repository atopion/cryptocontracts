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
    """ A class representing a Peer of the network which connects to the server
    
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
    command_handler()
        Takes care of the user input
    incoming_connection_handler(conn, addr)
        Manages connections to other peers
    connect_to_net()
        Establishes connection to the server peer
    disconnect_from_net()
        Disconnects from the network/server peer
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
    """
    
    active_connectable_addresses = []   # addresses of active peers in the net to connect to
    address_connection_pairs = {}   # mapping of addresses from incoming connection and outgoing connection of same peer
    client_sockets = []     # sockets over that this peer connects to other peers
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
        
        while True:
            try:

                i = input()
                if i == "connectable":
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
                        print("{}: Starting synchronization...".format(self.get_time()))
                        self.cb_start_sync()
                elif i == "list":   # display the current chain i
                    if self.cb_list_chain is not None:
                        self.cb_list_chain()
                elif i == "host":
                    p = self.host_addr
                    print(p[0]+":"+str(p[1]))
                elif i == "pairs":
                    print(self.address_connection_pairs)
                else:   # send message
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
                if  (peer_net[0] == host_net[0]):   # not in same LAN
                    self.create_new_connection(peer)
            else:
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
        
        gui_thread = threading.Thread(target=self.gui_handler)
        gui_thread.daemon = True
        gui_thread.start()
        
        time.sleep(1)    # so server_thread has time to bind socket and assign port
        self.set_host_addr()
        
        if self.output == "debug":
            print("{}: Host address: {}".format(self.get_time(),self.host_addr))
        
        if self.scope == "internal":    # For nodes in the same network
            ip_server.add_self_internal(*self.host_addr)
            if self.output == "debug":
                print("{}: Using internal mode".format(self.get_time()))
                
        elif self.scope == "localhost":
            ip_server.add_self_internal(*self.host_addr)
            if self.output == "debug":
                print("{}: Starting network on localhost".format(self.get_time()))
                
        else:
            ip_server.add_self(self.port)
            
        print("{}: Host address added to IP Server".format(self.get_time()))
        print("{}: Host now accepts connections".format(self.get_time()))
        
        self.active_connectable_addresses = self.get_peers_from_ip_server()
        if self.output == "debug":
            print("{}: Pulling active nodes from IP server".format(self.get_time()))
            print("{}: Active nodes in the network: {}".format(self.get_time(),self.active_connectable_addresses))
        
        self.connect_to_all()

        refreshing_thread = threading.Thread(target=self.refresh_connections)
        refreshing_thread.daemon = True
        refreshing_thread.start()
        
        self.lock.acquire()  # lock main thread

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
                if self.output == "debug":
                    print("{}: Trying to connect to {}:{}...".format(self.get_time(),addr[0],addr[1]))
                connecting_thread = threading.Thread(target=self.establish_connection,args=(addr,))
                connecting_thread.daemon = True
                connecting_thread.start()
                connecting_thread.join(timeout=5)  # if not able to connect after certain amout of time, terminate thread
                existing = False
                for peer in self.server_peers:
                    if (peer[0] == addr[0] and int(peer[1]) == int(addr[1])):
                        existing = True
                if not existing:
                    if self.output == "debug":
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
        except (ConnectionRefusedError, TimeoutError, BlockingIOError, OSError):
            connected = False
        if connected:
            self.server_peers.append(addr)
            self.client_sockets.append(sock)
            thread = threading.Thread(target=self.outgoing_connection_handler, args=(addr,sock))
            thread.daemon = True
            thread.start()
            print("{}: Connected to {}:{} \n".format(self.get_time(),addr[0], str(addr[1])))
        
    def disconnect_from_net(self):
        """Disconnects from the network/server peer
        
        The socket is shutdown and closed which causes a disconnection.
        """

        ip_server.delete(self.host_addr[0])

        self.lock.release()     #unlock main thread
        
        for sock in self.client_sockets:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        
        try:
            self.sock_server.shutdown(socket.SHUT_RDWR)
            self.sock_server.close()
        except OSError:
            pass
        
        try:
            self.gui_socket.shutdown(socket.SHUT_RDWR)
            self.gui_socket.close()
        except OSError:
            pass
        
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
        """ Returns the current time
        
        Returns
        -------
        time : float
            the current time
        """
        
        time = datetime.datetime.now().time()
        
        return time
    
    def gui_handler(self):
        
        self.gui_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = config.get("gui", "addr")
        port = int(config.get("gui", "port"))
        self.gui_socket.bind((addr, port))
        self.gui_socket.listen(1)
    
    
        while True:
            gui_conn, gui_addr = self.gui_socket.accept()
            
            print("{}: GUI connected".format(self.get_time()))
            
            while True:
                try:
                    data = gui_conn.recv(4096)
                    if not data:
                        if self.output == "debug":
                            print("{}: GUI closed".format(self.get_time()))
                        gui_conn.close()
                        break
                    
                    if self.output == "debug":
                        print("{}: From GUI received {}".format(self.get_time(),data))
                    
                    data = str(data, "utf-8")
                    print("data: ", data)
                    mode = int(bytes(data[0], "utf-8").hex()[0:2])
                    print("mode: ", mode)
                    content = data[1:]
                    print("content: ", content)
                    
                    if mode == 11:
                        if self.output == "debug":
                            print("{}: Received chain request from GUI".format(self.get_time()))
                        head = storage.get_head()
                        gui_conn.send(b'\x21' + bytes(json.dumps(head), "utf-8"))
                        if self.output == "debug":
                            print("{}: Sent head of chain to GUI".format(self.get_time()))
                            
                    if mode == 12:
                        if self.output == "debug":
                            print("{}: Received document upload request from GUI".format(self.get_time()))
                        content = Transmission.from_json(content)
                        print("content: ", content)
                        storage.put_block(content)  
                        gui_conn.send(b'\x22')
                        if self.cb_start_sync is not None:
                            print("{}: Starting synchronization...".format(self.get_time()))
                            self.cb_start_sync()
                    
                
                except ConnectionResetError or ConnectionAbortedError:
                    if self.output == "debug":
                        print("{}: Lost connection to GUI".format(self.get_time()))

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
                    if self.output == "debug":
                        print("{}: {}:{} disconnected \n".format(self.get_time(),str(address[0]),str(address[1])))
                    conn.close()
                    try:
                        self.connections.remove(conn)
                        self.clean_connections()
                    # TODO find out why Error is raised
                    except ValueError:
                        if self.output == "debug":
                            print("Could not remove connection from connections \n")

                    try:
                        self.connected_peers.remove(address)
                        self.clean_connected_peers()
                    except ValueError:
                        if self.output == "debug":
                            print("Could not remove address {}:{} from connected peers \n".format(address[0],str(address[1])))

#                    self.send_offline_peer(address) # notify connected peers that one peer went offline
                    break
                if self.output == "debug":
                    print("{}: From {}:{} received {} over incoming connection handler \n".format(self.get_time(),address[0],str(address[1]),data))


                inputs = str(data, "utf-8").split("!")

                for msg in inputs:
                    if msg != "":
                        mode = int(bytes(msg, "utf-8").hex()[0:2])
#                        print("part message: ", msg)
                        if self.output == "debug":
                            print("{}: MODE {}: ".format(self.get_time(), mode))
                        core.network_log("RECEIVED \\x", mode, " from ", address[0])
                        # look for specific prefix indicating the list of active peers

                        if mode == 15:
                            # for matching address of incoming data and connection object to send data 
                            rec_data = msg[1:]
                            rec_peer = rec_data.split(":")
                            connected = self.create_new_connection((rec_peer[0],int(rec_peer[1])))
                            self.address_connection_pairs.update({rec_data:conn})
                            if self.output == "debug":
                                print("{}: Address-connection pair added".format(self.get_time()))
                            if connected:
                                self.active_connectable_addresses.append((rec_peer[0],rec_peer[1]))

                        elif mode == 20:
                            print("{}: Received transmission from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            self.cb_receive_message(Transmission.from_json(msg[1:]))

                        elif mode == 31:
                                # Synchronization request
                                print("{}: Received synchronization request from {}:{}".format(self.get_time(), address[0], int(address[1])))
                                if self.cb_send_sync_message is not None:
                                    self.cb_send_sync_message(conn)

                        elif mode == 32:
                            # Synchronization answer
                            print("{}: Received synchronization answer from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            data = json.loads(str(msg[1:]))
                            data["conn"] = conn
                            self.synchronization_request_answers.append(data)
                            # TODO multiple connections
                            if len(self.synchronization_request_answers) == len(self.connected_peers):
                                self.synchronization_finished_event.set()
                            #self.synchronization_finished_event.set()

                        elif mode == 33:
                            # Subchain request
                            print("{}: Received subchain request from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            hash = str(msg[1:])
                            if self.cb_send_subchain_message is not None:
                                self.cb_send_subchain_message(conn, hash)

                        elif mode == 34 or mode == 35:
                            print("{}: Received subchain from {}:{}".format(self.get_time(), address[0], int(address[1])))
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
                                if self.output == "debug":
                                    print("{}: Could not receive subchain".format(self.get_time()))
                                    print("{}: Reason: {} \n".format(self.get_time(),e))

                            # if no prefix consider data a message and print it
                        else:
                            print("{}: Message from {}:{} : {}".format(self.get_time(),address[0], int(address[1]),msg))

                            """elif mode == 34:
                                # Subchain answer
                                self.synchronization_chain = core.core.Transmission.list_from_json(str(msg[1:]).replace("\\\\", "\\"))
                                self.synchronization_subchain_event.set()
                            # if no prefix consider data a message and print it"""

            except ConnectionResetError or ConnectionAbortedError:
                if self.output == "debug":
                    print("{}: {}:{} Connection impolitely closed.".format(self.get_time(), address[0],str(address[1])))
                try:
                    self.connections.remove(conn)
                    self.clean_connections()
                # TODO find out why Error is raised
                except ValueError:
                    if self.output == "debug":
                        print("Could not remove connection from connections \n")

                try:
                    self.connected_peers.remove(address)
                    self.clean_connected_peers()
                except ValueError:
                    if self.output == "debug":
                        print("Could not remove address {}:{} from connected peers \n".format(address[0],str(address[1])))

                except ValueError:
                    if self.output == "debug":
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
                if self.output == "debug":
                    print("{}: Randomly chosen port numer already taken, choosing different number")
        
        while True:
            conn, addr = self.sock_server.accept()
            thread = threading.Thread(target=self.incoming_connection_handler, args=(conn,addr))
            thread.daemon = True
            thread.start()
            self.connected_peers.append(addr)
            self.connections.append(conn)
            self.clean_connected_peers()
            print("{}: {}:{} connected \n".format(self.get_time(),str(addr[0]),str(addr[1])))
    
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
                        if self.output == "debug":
                            print("{}: Could not remove server peer: {}:{} from server list".format(self.get_time(), address[0],str(address[1])))

                    try:
                        self.active_connectable_addresses.remove(address)
                    except:
                        if self.output == "debug":
                            print("{}: Could not remove server peer: {}:{} from active connectable address list".format(self.get_time(), address[0],str(address[1])))

                    try:
                        self.address_connection_pairs.pop(str(address[0]+":"+str(address[1])))
                    except Exception as e:
                        if self.output == "debug":
                            print("{}: Could not remove address from address connection pair dict".format(self.get_time()))
                            print("Reason: ",e)

#                    self.send_offline_connectable_address(address)  # notify other peers that one peer went offline

                    self.client_sockets.remove(sock)
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()

                    break
                if self.output == "debug":
                    print("{}: From {}:{} received {}".format(self.get_time(),address[0],str(address[1]),data))

                inputs = str(data, "utf-8").split("!")

                for msg in inputs:
                    if msg != "":
                        try:
                            mode = int(bytes(msg, "utf-8").hex()[0:2])
                        except ValueError:
                            mode = ""
#                        print("part message: ", msg)
                        if self.output == "debug":
                            print("{}: MODE {}: ".format(self.get_time(),mode))
                        core.network_log("RECEIVED \\x", mode, " from ", address[0])
                        # look for specific prefix indicating the list of active peers

#                        elif mode == 14:
#                            # notification that connectable address not available anymore
#                            offline_peer = msg[1:].split(":")
#                            for addr in self.active_connectable_addresses:
#                                if offline_peer[0] == addr[0] and int(offline_peer[1]) == addr[1]:
#                                    self.active_connectable_addresses.remove(addr)
##                                    self.send_offline_connectable_address(addr)
#                                    break   # considering that no redundant addresses in list
                        
                        if mode == 20:
                            print("{}: Received transmission from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            self.cb_receive_message(Transmission.from_json(msg[1:]))

                        elif mode == 31:
                            # Synchronization request
                            print("{}: Received synchronization request from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            if self.cb_send_sync_message is not None:
                                self.cb_send_sync_message(self.address_connection_pairs[str(address[0]+":"+str(address[1]))])

                        elif mode == 32:
                            # Synchronization answer
                            print("{}: Received synchronization answer from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            data = json.loads(str(msg[1:]))
                            data["conn"] = self.address_connection_pairs[str(address[0]+":"+str(address[1]))]
                            self.synchronization_request_answers.append(data)
                            # TODO multiple connections
                            if len(self.synchronization_request_answers) == len(self.connected_peers):
                                self.synchronization_finished_event.set()
                            #self.synchronization_finished_event.set()

                        elif mode == 33:
                            # Subchain request
                            print("{}: Received subchain request from {}:{}".format(self.get_time(), address[0], int(address[1])))
                            hash = str(msg[1:])
                            if self.cb_send_subchain_message is not None:
                                self.cb_send_subchain_message(self.address_connection_pairs[str(address[0]+":"+str(address[1]))], hash)

                        elif mode == 34 or mode == 35:
                            print("{}: Received subchain from {}:{}".format(self.get_time(), address[0], int(address[1])))
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
                                print("{}: Could not receive subchain".format(self.get_time()))
                                print("{}: Reason: {} \n ".format(self.get_time(),e))

                        # if no prefix consider data a message and print it
                        else:
                            print("{}: Message from: {}:{} : {} \n".format(self.get_time(), address[0], int(address[1]),msg))

            except ConnectionResetError or ConnectionAbortedError:
                if self.output == "debug":
                    print("{}: {}:{} impolitely disconnected.".format(self.get_time(), address[0],str(address[1])))
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
                except Exception as e:
                    if self.output == "debug":
                        print("{}: Could not remove address from address connection pair dict".format(self.get_time()))
                        print("Reason: ",e)

    def refresh_connections(self):
        """ Gets the current active nodes in the network in a specific frequency"""
        
        host_net = self.host_addr[0].split(".")  # local network address of host
        
        while True:
            time.sleep(300)
            if self.output == "debug":
                print("{}: Refreshing connections...".format(self.get_time()))
            self.active_connectable_addresses = self.get_peers_from_ip_server()
            
            if self.output == "debug":
                print("{}: Active nodes: {}".format(self.get_time(),self.active_connectable_addresses))
            for on in self.active_connectable_addresses:
                own = False
                same_net = True
                if on[0] == self.host_addr[0] and int(on[1]) == int(self.host_addr[1]):
                    own = True  # own address of host
                else:
                    if self.scope == "internal" or self.scope == "localhost":
                        peer_net = on[0].split(".")
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
       if self.output == "debug":
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
        if self.output == "debug":
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
        
        if self.output == "debug":
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
        
    def send_synchronize_request(self):
        for conn in self.connections:
            conn.send(b'\x31!')

        print("{}: Synchronization request sent".format(self.get_time()))
        self.synchronization_finished_event.wait(30)
        res = self.synchronization_request_answers
        self.synchronization_request_answers = []
        self.synchronization_finished_event = threading.Event()
        core.network_log("SEND \\x31 to ", [x for x in self.connections])
        return res

    def send_sync_request_answer(self, conn, obj):
        conn.send(b'\x32' + bytes(json.dumps(obj), "utf-8"))
        print("{}: Synchronization request answer sent".format(self.get_time()))
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


