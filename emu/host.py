import emu.packet as packet
#import emu.sender
import socket
import os
import sys
import json

# return values from run() to indicate what the controlling program should do
SWITCH = 0
DONE = 1

class Receiver:
    def __init__(self, sock, port, emulator, window_size):
        # Config variables        
        self.sock = sock
        self.port = port
        self.emulator = emulator
        self.window_size = window_size
        
        # State variables
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

            # ignore packets from the wrong host
            if(addr == self.emulator):
                return packet.unpack_packet(pkt)

    """We'll stay in this state until receiving a SYN or FIN"""
    def wait_for_syn(self):
        pkt = self.wait_for_packet(False)
        if(pkt.flags == packet.Type.FIN):
            print("received FIN packet, finishing up")
            self.is_done = True
            self.finish_status = DONE

        print("received SYN packet; responding with SYN/ACK")
        self.latest_ack = packet.create_synack_packet(pkt)
        response = packet.pack_packet(self.latest_ack)
        self.sock.sendto(response, (self.emulator, self.port))
        self.ack_num = 1

    """Main function: sends off an ACK (or SYN/ACK) if necessary, then waits for and processes the next packet."""
    def handle_next_packet(self):
        if(self.rcvd_window_bytes == (self.window_size * packet.MAX_DATA_LENGTH) or self.ack_now):
            print("sending ack {}".format(self.ack_num))
            response = packet.pack_packet(self.latest_ack)
            self.sock.sendto(response, (self.emulator, self.port))
            
            self.ack_now = False
            self.rcvd_window_bytes = 0
            # write byte_buf to file system or something

        print("waiting for next packet...")
        rcvd = self.wait_for_packet(True)

        # wait_for_packet returns None on timeout
        if(rcvd == None):
            # re-send last ACK
            print("timed out while waiting for packet; retransmitting ack with ack number {}".format(self.ack_num))
            response = packet.pack_packet(self.latest_ack)
            self.sock.sendto(response, (self.emulator, self.port))

        elif(rcvd.flags == packet.Type.SYN):
            print("received another SYN packet; responding with SYN/ACK")
            response = packet.pack_packet(packet.create_synack_packet(rcvd))
            self.sock.sendto(response, (self.emulator, self.port))

        elif(rcvd.flags == packet.Type.FIN):
            print("received FIN packet, finishing up")
            self.is_done = True
            self.finish_status = DONE

        elif(rcvd.flags == packet.Type.EOT):
            print("received EOT packet; switching to sender mode")
            self.is_done = True
            self.finish_status = SWITCH

        elif(rcvd.flags == packet.Type.DATA):
            # we got a spurious retransmission - send ACK for latest received data
            if(rcvd.seq_num < self.ack_num):
                print("spurious retransmission with sequence number {}, retransmitting ack {}".format(rcvd.seq_num, self.latest_ack.ack_num))
                response = packet.pack_packet(self.latest_ack)
                self.sock.sendto(response, (self.emulator, self.port))
                return

            # the sender will always send max data unless it's almost out of data
            # in that case, we don't want to wait for the timeout
            # we should receive an EOT after this (but it shouldn't actually cause problems if not)
            if(rcvd.data_len < packet.MAX_DATA_LENGTH):
                print("packet had length < max length; acking now")
                self.ack_now = True

            self.rcvd_window_bytes += rcvd.data_len
            self.latest_ack = packet.create_ack_packet_from_data(rcvd, self.seq_num)
            self.ack_num += rcvd.data_len
            print("received packet with sequence number {}; received {} bytes this window, current ack number is {}".format(rcvd.seq_num, self.rcvd_window_bytes, self.ack_num))
            # add data to byte_buf


    def run(self):
        print("waiting for SYN packet...")
        self.wait_for_syn()
        if(self.is_done):
            print("finished running, returning status {}".format("SWITCH" if self.finish_status == SWITCH else "DONE"))
            return self.finish_status
        
        print("entering main receiver loop")
        while(not self.is_done):
            self.handle_next_packet()

        print("finished running, returning status {}".format("SWITCH" if self.finish_status == SWITCH else "DONE"))
        return self.finish_status

class Host:
    def __init__(self, cfg_file_path, is_receiver):
        if(not os.path.isfile(cfg_file_path)):
            raise TypeError("cfg_file_path must point to an existing file")

        with open(cfg_file_path) as config_file:    
            self.config = json.load(config_file)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((socket.gethostname(), self.config["port"]))
        self.sock.settimeout(self.config["timeout"])
        self.is_recv = is_receiver

    def run(self):
        while(True):
            if(self.is_recv):
                receiver = Receiver(self.sock, self.config["port"], self.config["emulator"], self.config["window_size"])
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
