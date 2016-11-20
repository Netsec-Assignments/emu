import emu.packet as packet
import socket
import os
import sys
import json
from enum import Enum

# return values from run() to indicate what the controlling program should do
SWITCH = 0
DONE = 1

class Receiver:
    def __init__(self, sock, port, emulator):
        self.sock = sock
        self.port = port
        self.emulator = emulator
        self.ack_num = 0
        self.seq_num = 0

    def wait_for_packet(self, return_on_timeout = True):
        while(True):
            try:
                pkt, addr = self.sock.recvfrom(packet.MAX_LENGTH)
            except socket.timeout:
                if(return_on_timeout):
                    return None
                else:
                    continue

            # ignore packets from the wrong host
            if(addr == self.emulator):
                return packet.unpack_packet(pkt)

    def run(self):
        pkt = self.wait_for_packet(False)
        if(packet.type == packet.Type.FIN):
            return DONE

        response = packet.pack_packet(packet.create_synack_packet())
        self.sock.sendto(response, (self.fwd_host, self.port))
        self.ack_num = 1
        
        rcvd_window_bytes = 0
        ack_now = False
        latest_rcvd = None
        while(True):
            if(rcvd_window_bytes == window_size or ack_now == True):
                self.ack_num += rcvd_window_bytes
                response = packet.pack_packet(packet.create_ack_packet(rcvd, self.seq_num))
                self.sock.sendto(response, (self.fwd_host, self.port))
                ack_now = False
                rcvd_window_bytes = 0

            rcvd = self.wait_for_packet(True)

            # wait_for_packet returns None on timeout
            if(rcvd == None):
                # re-send last ACK
                ack_packet = packet.pack_packet(packet.create_ack_packet(latest_rcvd, self.seq_num))
                self.sock.sendto(ack_packet, (self.fwd_host, self.port))
            elif(rcvd.type == packet.Type.SYN):
                # respond to SYN w/ SYN/ACK
                response = packet.pack_packet(packet.create_synack_packet())
                self.sock.sendto(response, (self.fwd_host, self.port))
            elif(rcvd.type == packet.Type.FIN):
                return DONE
            elif(rcvd.type == packet.Type.EOT):
                return SWITCH
            elif(rcvd.type == packet.Type.DATA):
                if(rcvd.seq_num < self.ack_num):
                    # resend last ACK
                    ack_packet = packet.create_ack_packet(latest_rcvd, self.seq_num)
                    self.sock.sendto(ack_packet, (self.fwd_host, self.port))
                    continue

                if(rcvd.data_len < packet.MAX_LENGTH):
                    send_ack_now = True

                rcvd_window_bytes += packet.data_len
                latest_rcvd = rcvd         

class Host:
    def __init__(self, cfg_file_path, is_receiver):
        if(not os.path.isfile(cfg_file_path)):
            raise TypeError("cfg_file_path must point to an existing file")

        with open(cfg_file_path) as config_file:    
            self.config = json.load(config_file)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.config["timeout"])
        self.is_recv = is_receiver

    def run(self):
        while(True):
            if(self.is_recv):
                receiver = Receiver(self.sock, self.config["port"], self.config["emulator"])
                result = receiver.run()
                if(result == DONE):
                    return
                else:
                    self.is_recv = False
            else:
                # Initialise sender and run it
                pass

if(__name__ == "__main__"):
    # check whether we're supposed to receive or send first based on cmd-line args
    # start host in appropriate mode 
    if(len(sys.argv) != 3):
        print("usage: host <config file> [receiver|sender]")
        sys.exit(1)

    is_receiver = False
    if(sys.argv[2] == "receiver"):
        is_receiver = True
    elif(sys.argv[2] != "sender"):
        print("usage: host <config file> [receiver|sender]")
        sys.exit(1)

    try:
        h = Host(sys.argv[1], is_receiver)
        h.run()
    except Exception as err:
        print(str(err))
