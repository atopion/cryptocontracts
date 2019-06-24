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
import json

import core


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

    synchronization_finished_event = threading.Event()
    synchronization_subchain_event = threading.Event()
    
    def __init__(self,addr=None, list_chain=None, send_sync_message=None, send_subchain_message=None, start_sync=None):

        self.cb_list_chain = list_chain
        self.cb_start_sync = start_sync
        self.cb_send_sync_message = send_sync_message
        self.cb_send_subchain_message = send_subchain_message

        self.synchronization_chain = []
        self.synchronization_request_answers = []

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
                    self.sockClient.connect((chosenAddr, 10000))
                    connected = True
                    print("Found active peer. Connected to network via {}".format(chosenAddr))
                
                except:
                    print("Not able to connect")
                    self.lastAddresses.remove(chosenAddr)
                    
            
        else:
            self.fixedServer = True
            self.sockClient.connect((self.serverAddress, 10000))
            print("connected to server")
    
    def commandHandler(self):
        """ Takes care of the user input. 
        
        The command 'peer' shows the other active peers in the network.
        the commands 'exit', 'quit' and 'close' end the connection.
        """
        while True:
            try:

                i = input()
                if i == "peers":
                    p = self.getActivePeers()
                    print(p)
                elif i == "sync":
                    if self.cb_start_sync is not None:
                        self.cb_start_sync()
                elif i == "list":
                    if self.cb_list_chain is not None:
                        self.cb_list_chain()
                else:
                    if i == "exit" or i == "quit" or i == "close":
                        self.disconnectFromNet()
#                   distinguish between peers and conenctions
#              else:
#                   for connection in self.connections:
#                      connection.send(bytes(str(i),'utf-8'))
            except EOFError:
                os._exit(1)
            except KeyboardInterrupt:
                os._exit(1)
    
    
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
            try:
                data = self.sockClient.recv(1024)

                if not data:
                    break

                print("RECIEVED: ", data)
                mode = int(bytes(data).hex()[0:2])
                # look for specific prefix indicating the list of active peers
                if mode == 11:
                    self.activePeers = str(data[1:], "utf-8").split(",")[:-1]
                    self.storeAddresses()   # store addresses of active peers in file

                elif mode == 31:
                    # Synchronization request
                    if self.cb_send_sync_message is not None:
                        self.cb_send_sync_message(self.sockClient)

                elif mode == 32:
                    # Synchronization answer
                    data = json.loads(str(data[1:])[2:-1])
                    data["conn"] = self.sockClient
                    self.synchronization_request_answers.append(data)
                    # TODO multiple connections
                    #if len(self.synchronization_request_answers) == len(self.connections):
                    #    self.synchronization_finished_event.set()
                    self.synchronization_finished_event.set()

                elif mode == 33:
                    # Subchain request
                    hash = str(data[1:])[2:-1]
                    if self.cb_send_subchain_message is not None:
                        self.cb_send_subchain_message(self.sockClient, hash)

                elif mode == 34:
                    # Subchain answer
                    self.synchronization_chain = core.core.Transmission.list_from_json(str(data[1:])[2:-1].replace("\\\\", "\\"))
                    self.synchronization_subchain_event.set()

                # if no prefix consider data a message and print it
                else:
                    print(str(data,'utf-8'))

            except ConnectionResetError or ConnectionAbortedError:
                print("Connection closed.")
                os._exit(1)
        
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
        self.sockServer.bind(('0.0.0.0', port))
        self.sockServer.listen(1)
        
        while True:
            conn,addr = self.sockServer.accept()
            thread = threading.Thread(target=self.connectionHandler, args=(conn,addr))
            thread.daemon = True
            thread.start()
            self.connections.append(conn)
            self.activePeers.append(addr[0])
            print(str(addr[0]) + ':' + str(addr[1]),"connected")
            print("!!")
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

    def send_synchronize_request(self):
        print("SEND REQUEST")
        # TODO multiple connections
        #for conn in self.connections:
        #    conn.send(b'\x31')
        self.sockClient.send(b'\x31')

        self.synchronization_finished_event.wait(30)
        res = self.synchronization_request_answers
        self.synchronization_request_answers = []
        self.synchronization_finished_event = threading.Event()
        return res

    def send_sync_request_answer(self, conn, obj):
        conn.send(b'\x32' + bytes(json.dumps(obj), "utf-8"))

    def request_subchain(self, msg, hash):
        self.synchronization_chain = None
        msg["conn"].send(b'\x33' + bytes(hash, "utf-8"))

        self.synchronization_subchain_event.wait(30)
        self.synchronization_subchain_event = threading.Event()
        return self.synchronization_chain

    def send_subchain(self, conn, obj):
        conn.send(b'\x34' + bytes(json.dumps([x.to_json() for x in obj]), "utf-8"))
            
    
if __name__ == '__main__':

    if len(sys.argv) < 2:
        client = Peer()
        client.connectToNet()

    else:
        arg1 = sys.argv[1]
        client = Peer(addr=arg1)
        client.connectToNet()
