import packet
#import emu.sender
import socket
import os
import sys
import json

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
        self.is_done = False        
        self.rcvd_window_bytes = 0
        self.ack_now = False
        self.finish_status = DONE
        self.latest_ack = None

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

    """We'll stay in this state until receiving a SYN or FIN"""
    def wait_for_syn(self):
        pkt = self.wait_for_packet(False)
        if(pkt.flags == packet.Type.FIN):
            self.is_done = True
            self.finish_status = DONE

        self.latest_ack = packet.create_synack_packet(pkt)
        response = packet.pack_packet(self.latest_ack)
        self.sock.sendto(response, (self.emulator, self.port))
        self.ack_num = 1

    """Main function: sends off an ACK (or SYN/ACK) if necessary, then waits for and processes the next packet."""
    def handle_next_packet(self):
        if(self.rcvd_window_bytes == self.window_size or self.ack_now):
            response = packet.pack_packet(self.latest_ack)
            self.sock.sendto(response, (self.emulator, self.port))
            
            self.ack_now = False
            self.rcvd_window_bytes = 0
            # write byte_buf to file system or something

        rcvd = self.wait_for_packet(True)

        # wait_for_packet returns None on timeout
        if(rcvd == None):
            # re-send last ACK
            response = packet.pack_packet(self.latest_ack)
            self.sock.sendto(response, (self.emulator, self.port))

        elif(rcvd.type == packet.Type.SYN):
            response = packet.pack_packet(packet.create_synack_packet(rcvd))
            self.sock.sendto(response, (self.emulator, self.port))

        elif(rcvd.type == packet.Type.FIN):
            self.is_done = True
            self.finish_status = DONE

        elif(rcvd.type == packet.Type.EOT):
            self.is_done = True
            self.finish_status = SWITCH

        elif(rcvd.type == packet.Type.DATA):
            # we got a spurious retransmission - send ACK for latest received data
            if(rcvd.seq_num < self.ack_num):
                self.sock.sendto(self.latest_ack, (self.emulator, self.port))
                return

            # the sender will always send max data unless it's almost out of data
            # in that case, we don't want to wait for the timeout
            # we should receive an EOT after this (but it shouldn't actually cause problems if not)
            if(rcvd.data_len < packet.MAX_LENGTH):
                self.ack_now = True

            self.rcvd_window_bytes += packet.data_len
            self.latest_ack = packet.create_ack_packet(rcvd, self.seq_num)
            self.ack_num += rcvd_window_bytes
            # add data to byte_buf


    def run(self):
        self.wait_for_syn()
        if(self.is_done):
            return self.finish_status
        
        byte_buf = []
        while(not self.is_done):
            self.handle_next_packt()

        return self.finish_status

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
        print("usage: host [config file] [receiver|sender]")
        sys.exit(1)

    try:
        h = Host(sys.argv[1], is_receiver)
        h.run()
    except Exception as err:
        print(str(err))
