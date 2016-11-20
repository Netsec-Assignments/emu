import os
import socket
import sys

FILE_NAME = "config.txt"

class Client:
    def __init__(self, ipAddr, portNum):
        if(ipAddr == None):
            self.ipAddr = '192.168.0.7'
        else:
            self.ipAddr = ipAddr
        if(portNum == None):
            self.portNum = "7000"
        else:
            self.portNum = int(portNum)
        self.running = True
        print("Client Initialized")

    def start(self):
        print("run executed")

        #connect to channel
        self.dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dataSock.connect((self.ipAddr, self.portNum))
        self.dataSock.setblocking(0)
        print("Disconnected.")
        self.dataSock.close()

def read_config():
    with open(FILE_NAME) as f:
        content = f.read().splitlines()
    print("    User will connect on :", content[0])
    print("    on port:", content[1])
    return content

def intro():
    print("    Final Assignment: C7005")
    print("    Mat Siwoski and Shane Spoor\n")
    print("    Started the Client Program")

intro()
content = read_config()  


client = Client(content[0], content[1])

client.start();
