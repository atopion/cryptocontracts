#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 23:47:34 2019

@author: rene
"""

import socket
import threading
import os
import json
import core


class ServerPeer:
    """ A class representing the server peer of the network which the client peers can connect to
    
    Attributes
    ----------
    active_peers : list
        a list containing all peers that are currently connected to the network
    connections : list
        a list containing the connections currently established with the clients
        
    Methods
    -------
    command_handler()
        Takes care of the user input
    connection_handler()
        Manages connections to client peers
    get_active_peers()
        Gets the list of all peers currently connected to the net/server peer
    request_graph(address)
        Sends request for latest version of graph to peer specified in address
    send_active_peers()
        Sends the list of active peers to all clients connected to this server
    send_graph(address)
        Sends latest version of graph to peer specified in address
    """    
    
    connections = []
    active_peers = []
    lock = threading.Lock()     # To lock main thread after establishing connection
    
    #cb_list_chain = None
    #cb_send_sync_message = None
    #cb_send_subchain_message = None
    synchronization_finished_event = threading.Event()
    synchronization_subchain_event = threading.Event()
    
    def __init__(self, list_chain=None, send_sync_message=None, send_subchain_message=None, start_sync=None, port=None):
        """ Constructor that initiats general server functions
        
        A socket object is created, bind and starts listening to connections.
        The command_handler is started in a dedicated thread.
        Incoming connections are handeled by one thread each.
        When a connection is established the address and connection are stored in the active_peers and connections list.
        Moreover, the list of all active peers is send.
        
        """
        
        if port == None:
            port = 10000
        
        hostname = socket.gethostname()
        hostaddr = socket.gethostbyname(hostname)
        self.active_peers.append((hostaddr,port))
        
        server_thread = threading.Thread(target=self.listen_for_connections)
        server_thread.daemon = True
        server_thread.start()
        
        self.cb_list_chain = list_chain
        self.cb_start_sync = start_sync
        self.cb_send_sync_message = send_sync_message
        self.cb_send_subchain_message = send_subchain_message
        
        
        
        command_thread = threading.Thread(target=self.command_handler)
        command_thread.daemon = True
        command_thread.start()
        
        self.synchronization_request_answers = []
        self.synchronization_chain = None
        
        self.lock.acquire()
        self.lock.acquire()  # call two times to lock main thread
        
    def listen_for_connections(self):
        """ Makes sure that peers can connect to this host.
        
        Creates an own thread for each incoming connection.
        """
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind(('0.0.0.0',10000))
        self.sock.listen(1)
        
        print("Server running...")
        
        while True:
            conn,addr = self.sock.accept()
            thread = threading.Thread(target=self.connection_handler, args=(conn,addr))
            thread.daemon = True
            thread.start()
            self.connections.append(conn)
            self.active_peers.append(addr)
            print(str(addr[0]) + ':' + str(addr[1]),"connected")
            self.send_active_peers()
            
        
    def command_handler(self):
        """ Takes care of the user input. 
        
        The command 'peers' shows the other active peers in the network.
        """
        
        while True:
            try:
                
                i = input()
                if i == "peers":
                    p = self.get_active_peers()
                    print(p)
                elif i == "list":
                    if self.cb_list_chain is not None:
                        self.cb_list_chain()
                elif i == "sync":
                    self.cb_start_sync()
#                elif i == "connections":
#                    print(self.connections)
                else:
                    for connection in self.connections:
                        connection.send(bytes(str(i),'utf-8'))
                        
            except EOFError:
                os._exit(1)
            except KeyboardInterrupt:
                os._exit(1)
            except TypeError:
                if i == "sync":
                    print("Can not synchronize")
    
    def connection_handler(self, conn, addr):
        """ Manages connections to client peers
        
        It is constantly waited for incoming data. The data is a byte stream.
        The data sent by a client is distributed to all the other ones.
        After a connection has been canceled, the new connection list is send to all the active peers in the network.
        
        parameters:
        -----------
        conn : connection of specific peer
        addr : IP address of specific peer
        """
        
        while True:
            try:
                
                data = conn.recv(1024)
                if not data:
                    print(str(addr[0]) + ":" + str(addr[1]),"disconnected")
                    self.connections.remove(conn)
                    self.active_peers.remove(addr)
                    conn.close()
                    self.send_active_peers()
                    break
                
                mode = int(bytes(data).hex()[0:2])
                if mode == 31:
                    # Synchronization request
                    if self.cb_send_sync_message is not None:
                        self.cb_send_sync_message(conn)

                elif mode == 32:
                    # Synchronization answer
                    data = json.loads(str(data[1:])[2:-1])
                    data["conn"] = conn
                    self.synchronization_request_answers.append(data)
                    if len(self.synchronization_request_answers) == len(self.connections):
                        self.synchronization_finished_event.set()

                elif mode == 33:
                    # Subchain request
                    hash = str(data[1:])[2:-1]
                    if self.cb_send_subchain_message is not None:
                        self.cb_send_subchain_message(conn, hash)

                elif mode == 34:
                    # Subchain answer
                    self.synchronization_chain = core.core.Transmission.list_from_json(str(data[1:])[2:-1].replace("\\\\", "\\"))
                    self.synchronization_subchain_event.set()

                else:
                    for connection in self.connections:
                        connection.send(bytes(data))
                        
            except ConnectionResetError or ConnectionAbortedError:
                print("Connection closed.")
                return
    
#    def connect_to_net(self):
#        pass
#    
#    def disconnect_from_net(self):
#        pass
    
    def get_active_peers(self):
        """ returns the list of all peers currently connected to this net/server peer
        
        The peer IP addresses are taken from the object variable activePeer and are joined in a String
        
        Returns
        -------
        string
            a string representing the IP addresses of the currently connected peers
        """
        
        if self.active_peers:
            p = self.active_peers[0][0] + ":" + str(self.active_peers[0][1])
        
            for peer in self.active_peers[1:]:
    #            p = p + peer + ","
                p = p +  "," + peer[0] + ":" + str(peer[1]) 
        
        return p
    
    
    
    def request_graph(self, address):
        """ Sends request for latest version of graph to peer specified in address
        
        Parameters
        ----------
        address : str
            IP address of peer to send request to
            
        """
        
        pass
    
    def send_active_peers(self):
        """ Sends the list of active peers to all the clients connected to this server.
        
        The list of all active peers is taken and send over every connection as a byte stream.
        A dedicated information is output to the user.
        """
        
        p = self.get_active_peers()

        for connection in self.connections:
            connection.send(b'\x11' + bytes(p, "utf-8"))
        print("peer list sent!")
    
    
    def send_graph(self, address):
        """Sends latest version of graph to peer specified in address
        
        Parameters
        ----------
        address : str
            IP address of peer to send graph to
        """
        
        pass
    
    def send_sync_request_answer(self, conn, obj):
        conn.send(b'\x32' + bytes(json.dumps(obj), "utf-8"))

    def send_synchronize_request(self):
        self.synchronization_request_answers = []
        self.synchronization_finished_event = threading.Event()
        for conn in self.connections:
            conn.send(b'\x31')

        self.synchronization_finished_event.wait(30)
        return self.synchronization_request_answers

    def send_subchain(self, conn, obj):
        conn.send(b'\x34' + bytes(json.dumps([x.to_json() for x in obj]), "utf-8"))

    def request_subchain(self, msg, hash):
        self.synchronization_chain = None
        msg["conn"].send(b'\x33' + bytes(hash, "utf-8"))

        self.synchronization_subchain_event.wait(30)
        self.synchronization_subchain_event = threading.Event()
        return self.synchronization_chain


if __name__ == '__main__':
    server = ServerPeer()
    
    
    
    
#server = ServerPeer()
    