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


class ServerPeer:
    """ A class representing the server peer of the network which the client peers can connect to
    
    Attributes
    ----------
    activePeers : list
        a list containing all peers that are currently connected to the network
    connections : list
        a list containing the connections currently established with the clients
        
    Methods
    -------
    commandHandler()
        Takes care of the user input
    connectionHandler()
        Manages connections to client peers
    getActivePeers()
        Gets the list of all peers currently connected to the net/server peer
    requestGraph(address)
        Sends request for latest version of graph to peer specified in address
    sendActivePeers()
        Sends the list of active peers to all clients connected to this server
    sendGraph(address)
        Sends latest version of graph to peer specified in address
    """    
    
    connections = []
    activePeers = []

    cb_send_sync_message = None
    cb_send_subchain_message = None
    synchronization_finished_event = threading.Event()
    synchronization_subchain_event = threading.Event()

    def __init__(self, send_sync_message=None, send_subchain_message=None):
        """ Constructor that initiats general server functions
        
        A socket object is created, bind and starts listening to connections.
        The commandhandler is started in a dedicated thread.
        Incoming connections are handeled by one thread each.
        When a connection is established the address and connection are stored in the activePeers and connections list.
        Moreover, the list of all active peers is send.
        
        """
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.bind(('0.0.0.0', 10000))
        self.sock.listen(1)
        
        hostname = socket.gethostname()
        hostaddr = socket.gethostbyname(hostname)
        self.activePeers.append(hostaddr)

        self.cb_send_sync_message = send_sync_message
        self.cb_send_subchain_message = send_subchain_message
        
        print("Server running...")
        
        commandThread = threading.Thread(target=self.commandHandler)
        commandThread.daemon = True
        commandThread.start()

        self.synchronization_request_answers = []
        self.synchronization_chain = None

    def bind(self):
        while True:
            conn,addr = self.sock.accept()
            thread = threading.Thread(target=self.connectionHandler, args=(conn,addr))
            thread.daemon = True
            thread.start()
            self.connections.append(conn)
            self.activePeers.append(addr[0])
            print(str(addr[0]) + ':' + str(addr[1]),"connected")
            self.sendActivePeers()
        
    def commandHandler(self):
        """ Takes care of the user input. 
        
        The command 'peers' shows the other active peers in the network.
        """
        
        while True:
            try:
                i = input()
                if i == "peers":
                    self.getActivePeers()
                else:
                    for connection in self.connections:
                        connection.send(bytes(str(i),'utf-8'))

            except EOFError:
                os._exit(1)
            except KeyboardInterrupt:
                os._exit(1)

                    
    
    def connectionHandler(self, conn, addr):
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
            if not data:
                print(str(addr[0]) + ":" + str(addr[1]),"disconnected")
                self.connections.remove(conn)
                self.activePeers.remove(addr[0])
                conn.close()
                self.sendActivePeers()
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
                self.synchronization_chain = json.loads(str(data[1:])[2:-1])
                self.synchronization_subchain_event.set()

            else:
                for connection in self.connections:
                    connection.send(bytes(data))
    
#    def connectToNet(self):
#        pass
#    
#    def disconnectFromNet(self):
#        pass
    
    def getActivePeers(self):
        """ returns the list of all peers currently connected to this net/server peer
        
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
    
    
    
    def requestGraph(self, address):
        """ Sends request for latest version of graph to peer specified in address
        
        Parameters
        ----------
        address : str
            IP address of peer to send request to
            
        """
        
        pass
    
    def sendActivePeers(self):
        """ Sends the list of active peers to all the clients connected to this server.
        
        The list of all active peers is taken and send over every connection as a byte stream.
        A dedicated information is output to the user.
        """
        
        p = self.getActivePeers()

        for connection in self.connections:
            connection.send(b'\x11' + bytes(p, "utf-8"))
        print("peer list sent!")
    
    
    def sendGraph(self, address):
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
        for conn in self.connections:
            conn.send(b'\x31')

        self.synchronization_finished_event.wait(30)
        res = self.synchronization_request_answers
        self.synchronization_request_answers = []
        self.synchronization_finished_event = threading.Event()
        return res

    def send_subchain(self, conn, obj):
        conn.send(b'\x34' + bytes(json.dumps(obj), "utf-8"))

    def request_subchain(self, msg, hash):
        msg["conn"].send(b'\x33' + bytes(hash, "utf-8"))

        self.synchronization_subchain_event.wait(30)
        res = self.synchronization_chain
        self.synchronization_subchain_event = threading.Event()
        self.synchronization_chain = None
        return res


if __name__ == '__main__':
    server = ServerPeer()
    