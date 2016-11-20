#import emu.packet as packet
import packet
import socket
import os
import sys
import json
from enum import Enum

# return values from run() to indicate what the controlling program should do
SWITCH = 0
DONE = 1

class Sender:
    def __init__(self, sock, port, emulator):
        self.sock = sock
        self.port = port
        self.emulator = emulator
        self.ack_num = 0
        self.seq_num = 0

    def run(self):
        print("run")

class Client:
    def __init__(self, cfg_file_path, is_receiver):
        if(not os.path.isfile(cfg_file_path)):
            raise TypeError("cfg_file_path must point to an existing file")
        
        with open(cfg_file_path) as config_file:    
            self.config = json.load(config_file)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.config["timeout"])
        self.is_sender = is_sender
       
    def start(self):
        print("run executed")
        while(True):
            if(self.is_sender):
                sender = Sender(self.sock, self.config["port"], self.config["emulator"])
                result = sender.run()
                if(result == DONE):
                    return
                else:
                    self.is_sender = False
            else:
                pass
        #connect to channel
        #self.dataSock.connect((self.ipAddr, self.portNum))
        #self.dataSock.setblocking(0)
        #print("Disconnected.")
        #self.dataSock.close()
        

    def intro(self):
        print("    Final Assignment: C7005")
        print("    Mat Siwoski and Shane Spoor\n")
        print("    Started the Client Program")

if(__name__ == "__main__"):
    # check whether we're supposed to receive or send first based on cmd-line args
    # start host in appropriate mode 
    if(len(sys.argv) != 3):
        print("usage: host <config file> [receiver|sender]")
        sys.exit(1)

    is_sender = False
    if(sys.argv[2] == "receiver"):
        is_sender = False
    elif(sys.argv[2] == "sender"):
        is_sender = True
    elif(sys.argv[2] != "sender"):
        print("usage: host <config file> [receiver|sender]")
        sys.exit(1)

    try:
        c = Client(sys.argv[1], is_sender)
        c.intro()
        c.start()
    except TypeError as err:
        print(str(err))
