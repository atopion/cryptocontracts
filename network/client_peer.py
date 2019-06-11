#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 23:32:58 2019

@author: rene
"""

import socket
import threading


class Peer:
    """ A class representing a Peer of the network which connects to the server
    
    Attributes
    ----------
    activePeers : list
        a list containing all peers that are currently connected to the network
    serverAddress : str
        a string representing the IP address of the server peer
    sock : socket object
        a socket that is bind to handle the connection
        
    Methods
    -------
    commandHandler()
        Takes care of the user input
    connectToNet()
        Establishes connection to the server peer
    disconnectFromNet()
        Disconnects from the network/server peer
    getActivePeers()
        Gets the list of all peers currently connected to the net/server peer
    requestGraph(address)
        Sends request for latest version of graph to peer specified in address
    sendGraph(address)
        Sends latest version of graph to peer specified in address
    """
    
    activePeers = []
    serverAddress = None
    sock = None
    
    def __init__(self,addr):
        self.serverAddress = addr
    
    
    def commandHandler(self):
        """ Takes care of the user input. 
        
        The command 'peer' shows the other active peers in the network.
        the commands 'exit', 'quit' and 'close' end the connection.
        """
        while True:
            i = input()
            if i == "peers":
                p = self.getActivePeers()
                print(p)
            else:
                if i == "exit" or i == "quit" or i == "close":
                    self.disconnectFromNet()
#                distinguish between peers and conenctions
#            else:
#                for connection in self.connections:
#                    connection.send(bytes(str(i),'utf-8'))
    
    def connectToNet(self):
        """Establishes connection to the server peer
        
        Sets up a socket and connects to the server peer. A new thread is started
        that runs the commandHandler function for user input handling.
        Data that is received is checked for special meaning by prefixes.
        If no prefix is found, it is considered a message and printed out.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.connect((self.serverAddress,10000))
        
        print("connected to server")
        
        commandThread = threading.Thread(target=self.commandHandler)
        commandThread.daemon = True
        commandThread.start()
        
        while True:
            data = self.sock.recv(1024)
            if not data:
                break
            
            # look for specific prefix indicating the list of active peers
            if data[0:1] == b'\x11':
                self.activePeers = str(data[1:], "utf-8").split(",")[:-1]
                
            # if no prefix consider data a message and print it
            else:
                print(str(data,'utf-8'))
        

    def disconnectFromNet(self):
        """Disconnects from the network/server peer
        
        The socket is shutdown and closed which causes a disconnection
        """
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
    
    def getActivePeers(self):
        """ returns the list of all peers currently connected to the net/server peer
        
        The peer IP addresses are taken from the object variable activePeer and are joined in a String
        
        Returns
        -------
        string
            a string representing the IP addresses of the currently connected peers
        """
        
        p = ""
        for peer in self.activePeers:
            p = p + peer + ", "
        return p
    
    def requestGraph(self, address):
        """Sends request for latest version of graph to peer specified in address
        
        Parameters
        ----------
        address : str
            IP address of peer to send request to
            
        """
        
        pass
    
    def sendGraph(self, address):
        """Sends latest version of graph to peer specified in address
        
        Parameters
        ----------
        address : str
            IP address of peer to send graph to
        """
        
        pass
    
    
#client = Peer() 
#client.connectToNet()  