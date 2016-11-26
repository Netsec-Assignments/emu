import emu.packet as packet
#import packet
import socket
import os
import sys
import json
from enum import Enum

# return values from run() to indicate what the controlling program should do
SWITCH = 0
DONE = 1

class Sender:
    def __init__(self, sock, port, emulator, window_size):
        #Config variables
        self.sock = sock
        self.port = port
        self.emulator = emulator
        self.window_size = window_size

        #State variables
        self.ack_num = 0
        self.seq_num = 0
        self.is_done = False
        self.rcvd_window_bytes = 0
        self.ack_now = False
        self.finish_status = DONE
        self.latest_ack = None

    def wait_for_packet(self, return_on_timeout = True):
        while(True):
            try:
                pkt, addr = self.sock.recvfrom(packet.MAX_PACKET_LENGTH)
            except socket.timeout:
                if(return_on_timeout):
                    return None
                else:
                    continue
            if(addr[0] == self.emulator):
                return packet.unpack_packet(pkt)
            
    """We'll stay in this state until receiving a SYN or FIN"""
    def wait_for_syn_ack(self):
        pkt = self.wait_for_packet(False)
        if(pkt.flags == packet.Type.FIN):
            print("received FIN packet, finishing up")
            self.is_done = True
            self.finish_status = DONE            
        elif(pkt.flags == (packet.Type.SYN or packet.Type.ACK)):
            print("received SYN_ACK packet: responding with ACK")
            self.latest_ack = pkt
            self.seq_num = max(pkt.ack_num, self.seq_num)


    """Send initial syn to begin connection"""
    def send_syn(self):
        response = packet.pack_packet(packet.create_syn_packet())
        self.sock.sendto(response, (self.emulator, self.port))
        self.seq_num = 1
        self.rcvd_window_bytes = 0
        self.latest_rcvd = None

    """Send ack to acknowledge syn ack to begin sending data"""
    """not necessary as we are not doing three way handshake"""
    def send_ack(self):
        response = packet.pack_packet(packet.create_ack_packet())
        self.sock.sendto(response, (self.emulator, self.port))
        self.rcvd_window_bytes = 0
        self.ack_now = True
        self.latest_rcvd = None

    """Send EOT at the end of the transmission"""
    def send_eot(self):
        self.sock.sendto(packet.pack_packet(packet.create_eot_packet()), (self.emulator, self.port))

    """Send FIN as the last packet when the data is completed"""
    def send_fin(self):
        self.sock.sendto(packet.pack_packet(packet.create_fin_packet()), (self.emulator, self.port))
        
    """Begin sending data to the server """    
    def send_data(self):
        packets = packet.create_data_packets(bytes([128] * packet.MAX_DATA_LENGTH * self.window_size), self.seq_num)
        for p in packets:
            self.sock.sendto(packet.pack_packet(p), (self.emulator, self.port))
            print("sent DATA packet with seq {} and data len {} to {} on port {}".format(p.seq_num, p.data_len, self.emulator, self.port))
        
    def run(self):
        print("starting the connection")
        self.send_syn()
        if(self.is_done):
            print("finished running, returning status {}".format("SWITCH" if self.finish_status == SWITCH else "DONE"))
            return self.finish_status

        print("waiting for SYN_ACK packet...")
        self.wait_for_syn_ack()
        if(self.is_done):
            print("finished running, returning status {}".format("SWITCH" if self.finish_status == SWITCH else "DONE"))
            return self.finish_status

        print("entering main sender loop")
        while(not self.is_done):
            pkt = self.wait_for_packet()
            if (pkt != None):
                if (pkt.flags & packet.Type.ACK):
                    print("received ACK with ack_num {} from host {}".format(pkt.ack_num, self.emulator))
                    self.seq_num = max(pkt.ack_num, self.seq_num)   
                    self.send_data()
                elif (pkt.flags & packet.Type.EOT):
                    self.is_done = True
                    self.finish_status = SWITCH                
                elif (pkt.flags & packet.Type.FIN):
                    self.is_done = True
                    self.finish_status = DONE
            else:
                print("timed out while waiting for ACK")
                self.send_data()

        print("finished running, returning status {}".format("SWITCH" if self.finish_status == SWITCH else "DONE"))
        return self.finish_status            

class Client:
    def __init__(self, cfg_file_path, is_receiver):
        if(not os.path.isfile(cfg_file_path)):
            raise TypeError("cfg_file_path must point to an existing file")
        
        with open(cfg_file_path) as config_file:    
            self.config = json.load(config_file)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', self.config["port"]))
        self.sock.settimeout(self.config["timeout"])
        self.is_sender = is_sender
       
    def start(self):
        while(True):
            if(self.is_sender):
                sender = Sender(self.sock, self.config["port"], self.config["emulator"], self.config["window_size"])

                result = sender.run()
                if(result == DONE):
                    return
                else:
                    self.is_sender = False
            else:
                pass

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
