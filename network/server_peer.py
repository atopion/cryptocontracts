#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 23:47:34 2019

@author: rene
"""

import socket
import threading


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
    
    def __init__(self):
        """ Constructor that initiats general server functions
        
        A socket object is created, bind and starts listening to connections.
        The command_handler is started in a dedicated thread.
        Incoming connections are handeled by one thread each.
        When a connection is established the address and connection are stored in the active_peers and connections list.
        Moreover, the list of all active peers is send.
        
        """
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        sock.bind(('0.0.0.0',10000))
        sock.listen(1)
        
        hostname = socket.gethostname()
        hostaddr = socket.gethostbyname(hostname)
        self.active_peers.append(hostaddr)
        
        print("Server running...")
        
        command_thread = threading.Thread(target=self.command_handler)
        command_thread.daemon = True
        command_thread.start()
        
        while True:
            conn,addr = sock.accept()
            thread = threading.Thread(target=self.connection_handler, args=(conn,addr))
            thread.daemon = True
            thread.start()
            self.connections.append(conn)
            self.active_peers.append(addr[0])
            print(str(addr[0]) + ':' + str(addr[1]),"connected")
            self.send_active_peers()
            
        
    def command_handler(self):
        """ Takes care of the user input. 
        
        The command 'peers' shows the other active peers in the network.
        """
        
        while True:
            i = input()
            if i == "peers":
                self.get_active_peers()
            else:
                for connection in self.connections:
                    connection.send(bytes(str(i),'utf-8'))
                    
    
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
            data = conn.recv(1024)
            for connection in self.connections:
                connection.send(bytes(data))    
            if not data:
                print(str(addr[0]) + ":" + str(addr[1]),"disconnected")
                self.connections.remove(conn)
                self.active_peers.remove(addr[0])
                conn.close()
                self.send_active_peers()
                break
    
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
        
        p = ""
        for peer in self.active_peers:
            p = p + peer + ","
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
    
    
#server = ServerPeer()
    