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
    lastAddresses = []
    serverAddress = None
    sockServer = None
    sockClient = None
    fixedServer = False
    
    def __init__(self,addr=None):
        if addr is None:
            if os.path.isdir("./addresses") and os.path.isfile("./addresses/last_active_addresses.txt"):
                lastAddresses = open("./addresses/last_active_addresses.txt")
                self.lastAddresses = lastAddresses.read().split(",")
                lastAddresses.close()
            else:
                sys.exit("No addresses stored. Please give a specific peer address when creating object.")
        else:
            self.serverAddress = addr
            self.fixedServer = True    # Flag to decide how to connect to net
    
    
    def chooseConnection(self):
        """ Function defines where to establish a connection to depending on if a specific address is given or not
        
        If no server address is specified when creating the peer object, an address from the last known addresses of the network is
        chosen randomly. If none is active the program is quit.
        """
        
        if self.fixedServer == False:
            connected = False
            try:
                self.lastAddresses.remove(self.getHostAddr())
            except:
                pass
            
            while connected == False:
                
                if not self.lastAddresses:
                    sys.exit("None of the lastly active peers is active right now")
                    
                chosenAddr = random.choice(self.lastAddresses)
                try:
                    print("Trying to connect to {}".format(chosenAddr))
                    self.sockClient.connect((chosenAddr,10000))
                    connected = True
                    print("Found active peer. Connected to network via {}".format(chosenAddr))
                
                except:
                    print("Not able to connect")
                    self.lastAddresses.remove(chosenAddr)
                    
            
        else:
            self.fixedServer == True
            self.sockClient.connect((self.serverAddress,10000))
            print("connected to server")
    
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
    
    
    def connectionHandler(self, conn, addr):
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
            for connection in self.connections:
                connection.send(bytes(data))    
            if not data:
                print(str(addr[0]) + ":" + str(addr[1]),"disconnected")
                self.connections.remove(conn)
                self.activePeers.remove(addr[0])
                conn.close()
                self.sendActivePeers()
                break
    
    def connectToNet(self):
        """Establishes connection to the server peer
        
        Sets up a socket and connects to the server peer. A new thread is started
        that runs the commandHandler function for user input handling.
        Data that is received is checked for special meaning by prefixes.
        If no prefix is found, it is considered a message and printed out.
        """
        self.sockClient= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockClient.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        
        self.chooseConnection()
        
        commandThread = threading.Thread(target=self.commandHandler)
        commandThread.daemon = True
        commandThread.start()
        
        serverThread = threading.Thread(target=self.listenForConnections)
        serverThread.daemon = True
        serverThread.start()
        
        while True:
            data = self.sockClient.recv(1024)
            if not data:
                break
            
            # look for specific prefix indicating the list of active peers
            if data[0:1] == b'\x11':
                self.activePeers = str(data[1:], "utf-8").split(",")[:-1]
                self.storeAddresses()   # store addresses of active peers in file
                
            # if no prefix consider data a message and print it
            else:
                print(str(data,'utf-8'))
        
        self.fixedServer = False
        self.chooseConnection()

    def disconnectFromNet(self):
        """Disconnects from the network/server peer
        
        The socket is shutdown and closed which causes a disconnection
        """
        self.sockClient.shutdown(socket.SHUT_RDWR)
        self.sockClient.close()
        
        self.sockServer.shutdown(socket.SHUT_RDWR)
        self.sockServer.close()
    
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
            p = p + peer + ","
        return p
    
    def getHostAddr(self):
        """ Returns the IP address of this host.
        
        Returns
        -------
        string
            a string representing the IP address of this host
        """
        
        hostName = socket.gethostname()
        hostAddr = socket.gethostbyname(hostName)
        
        return hostAddr
    
    
    def listenForConnections(self):
        """ Makes sure that peers can connect to this host.
        
        Creates an own thread for each incoming connection.
        """
        
        self.sockServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockServer.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        port = random.randint(10001,15000)
        self.sockServer.bind(('0.0.0.0',port))
        self.sockServer.listen(1)
        
        while True:
            conn,addr = self.sockServer.accept()
            thread = threading.Thread(target=self.connectionHandler, args=(conn,addr))
            thread.daemon = True
            thread.start()
            self.connections.append(conn)
            self.activePeers.append(addr[0])
            print(str(addr[0]) + ':' + str(addr[1]),"connected")
            self.sendActivePeers()
    
    
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
    
    def storeAddresses(self):
        """ Stores the currently active peers in the network to file
        
        """
        if not os.path.isdir("./addresses") == True:
            os.mkdir("./addresses")
            
        last_addresses = open("./addresses/last_active_addresses.txt","w")
        last_addresses.write(self.getActivePeers())
        last_addresses.close()
            
    
    
#client = Peer() 
#client.connectToNet()  