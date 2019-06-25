#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 23:32:58 2019

@author: rene
"""

import socket
import threading
import os
import sys
import random

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
    get_connections()
        Returns the list of all peers currently connected to the this host
    get_host_name()
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
    
    active_peers = []
    connected_peers = []    # Addresses of peers connected to this host
    fixed_server = False
    last_addresses = []
    lock = threading.Lock()     # To lock main thread after establishing connection
    server_address = None
    sock_server = None
    sock_client = None
    
    
    def __init__(self,addr=None):
        if addr is None:
            if os.path.isdir("./addresses") and os.path.isfile("./addresses/last_active_addresses.txt"):
                last_addresses = open("./addresses/last_active_addresses.txt")
                self.last_addresses = last_addresses.read().split(",")
                last_addresses.close()
            else:
                sys.exit("No addresses stored. Please give a specific peer address when creating object.")
        else:
            self.server_address = addr
            self.fixed_server = True    # Flag to decide how to connect to net
    
    
    def choose_connection(self):
        """ Defines where to establish a connection to depending on if a specific address is given or not
        
        If no server address is specified when creating the peer object, an address from the last known addresses of the network is
        chosen randomly. If none is active the program is quit.
        """
        
        if self.fixed_server == False:
            connected = False
            try:
                self.last_addresses.remove(self.get_host_name())
            except:
                pass
            
            while connected == False:
                
                if not self.last_addresses:
                    sys.exit("None of the lastly active peers is active right now")
                    
                chosen_addr = random.choice(self.last_addresses)
                try:
                    print("Trying to connect to {}".format(chosen_addr))
                    self.sock_client.connect((chosen_addr,10000))
                    connected = True
                    print("Found active peer. Connected to network via {}".format(chosen_addr))
                
                except:
                    print("Not able to connect")
                    self.last_addresses.remove(chosen_addr)
                    
            
        else:
            self.sock_client.connect((self.server_address,10000))
            print("connected to server")
    
    def command_handler(self):
        """ Takes care of the user input. 
        
        The command 'peer' shows the other active peers in the network.
        the commands 'exit', 'quit' and 'close' end the connection.
        """
        while True:
            i = input()
            if i == "peers":
                p = self.get_active_peers()
                print(p)
            else:
                if i == "exit" or i == "quit" or i == "close":
                    self.disconnect_from_net()
                    
                else:
                    if i == "connections":
                        p = self.get_connections()
                        print(p)
                    else:
                        for connection in self.connected_peers:
                            connection.send(bytes(str(i),'utf-8'))
    
    
    def incoming_connection_handler(self, conn, addr):
        """ Manages connections to other peers
        
        It is constantly waited for incoming data. The data is a byte stream.
        The data sent by a client is distributed to all the other ones.
        After a connection has been canceled, the new connection list is send to all the active peers in the network.
        
        parameters:
        -----------
        conn : connection of specific peer
        addr : IP address of specific peer
        """
        
        while True:
            data = conn.recv(1024)
            for connection in self.connected_peers:
                connection.send(bytes(data))    
            if not data:
                print(str(addr[0]) + ":" + str(addr[1]),"disconnected")
                self.connected_peers.remove(conn)
                self.active_peers.remove(addr[0])
                conn.close()
                self.send_active_peers()
                break
    
    def connect_to_net(self):
        """ Establishes connection to the server peer
        
        Sets up a socket and connects to the server peer. A new thread is started
        that runs the command_handler function for user input handling.
        Data that is received is checked for special meaning by prefixes.
        If no prefix is found, it is considered a message and printed out.
        """
        
        self.sock_client= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        
        self.choose_connection()    # chooses and establishes connection to another node in the net
        
        command_thread = threading.Thread(target=self.command_handler)
        command_thread.daemon = True
        command_thread.start()
        
        server_thread = threading.Thread(target=self.listen_for_connections)
        server_thread.daemon = True
        server_thread.start()
        
        client_thread = threading.Thread(target=self.outgoing_connection_handler)
        client_thread.daemon = True
        client_thread.start()
        
        self.lock.acquire()
        self.lock.acquire()  # call two times to lock main thread

    def disconnect_from_net(self):
        """Disconnects from the network/server peer
        
        The socket is shutdown and closed which causes a disconnection
        """
        
        self.lock.release()     #unlock main thread
        
        self.sock_client.shutdown(socket.SHUT_RDWR)
        self.sock_client.close()
        
        self.sock_server.shutdown(socket.SHUT_RDWR)
        self.sock_server.close()
    
    def get_active_peers(self):
        """ Returns the list of all peers currently connected to the net/server peer
        
        The peer IP addresses are taken from the object variable activePeer and are joined in a String
        
        Returns
        -------
        string
            a string representing the IP addresses of the currently connected peers
        """
        
        p = ""
        
        for peer in self.active_peers:
            p = p + peer + ","
        
        return p
    
    def get_connections(self):
        """ Returns the list of all peers currently connected to the this host
        
        The peer IP addresses are taken from the object variable activePeer and are joined in a String
        
        Returns
        -------
        string
            a string representing the IP addresses of the currently connected peers
        """
        
        p = ""
        
        for peer in self.connected_peers:
            p = p + peer + ","
            
        return p
    
    def get_host_name(self):
        """ Returns the IP address of this host.
        
        Returns
        -------
        string
            a string representing the IP address of this host
        """
        
        host_name = socket.gethostname()
        host_addr = socket.gethostbyname(host_name)
        
        return host_addr
    
    
    def listen_for_connections(self):
        """ Makes sure that peers can connect to this host.
        
        Creates an own thread for each incoming connection.
        """
        
        self.sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        port = random.randint(10001,15000)
        self.sock_server.bind(('0.0.0.0',port))
        self.sock_server.listen(1)
        
        while True:
            conn,addr = self.sock_server.accept()
            thread = threading.Thread(target=self.incoming_connection_handler, args=(conn,addr))
            thread.daemon = True
            thread.start()
            self.connected_peers.append(conn)
            self.active_peers.append(addr[0])
            print(str(addr[0]) + ':' + str(addr[1]),"connected")
            self.send_active_peers()
    
    def outgoing_connection_handler(self):
        """ Maintains outgoing connection from this peer to another node in the net
        
        If the connection to the server node corrupts, it is looked for another node to connect to
        """
        
        while True:
            data = self.sock_client.recv(1024)
            
            if not data:
                self.fixed_server = False   # When server peer goes offline, this peer needs to connect to another peer
                self.choose_connection()
            
            # look for specific prefix indicating the list of active peers
            if data[0:1] == b'\x11':
                self.active_peers = self.active_peers + str(data[1:], "utf-8").split(",")[:-1]
                self.store_addresses()   # store addresses of active peers in file
                
            # if no prefix consider data a message and print it
            else:
                print(str(data,'utf-8'))
        
    def request_graph(self, address):
        """Sends request for latest version of graph to peer specified in address
        
        Parameters
        ----------
        address : str
            IP address of peer to send request to
            
        """
        
        pass
    
    def send_active_peers(self):
        """ Sends the list of active peers to all the known addresses in the network.
        
        The list of all active peers is taken and send over every connection as a byte stream.
        A dedicated information is output to the user.
        """
        
        p = self.get_active_peers()

        for address in self.connected_peers:
            address.send(b'\x11' + bytes(p, "utf-8"))
        print("peer list sent!")
    
    def send_graph(self, address):
        """Sends latest version of graph to peer specified in address
        
        Parameters
        ----------
        address : str
            IP address of peer to send graph to
        """
        pass
    
    def store_addresses(self):
        """ Stores the currently active peers in the network to file
        
        """
        if not os.path.isdir("./addresses") == True:
            os.mkdir("./addresses")
            
        last_addresses = open("./addresses/last_active_addresses.txt","w")
        last_addresses.write(self.get_active_peers())
        last_addresses.close()
            
    
    
#client = Peer() 
#client.connect_to_net()  