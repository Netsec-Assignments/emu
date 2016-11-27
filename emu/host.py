import emu.packet as packet
#import emu.sender
import socket
import os
import sys
import json

MAX_EOT_RETRIES = 5

# return values from run() to indicate what the controlling program should do
SWITCH = 0
DONE = 1

class Receiver:
    def __init__(self, sock, port, emulator, window_size, outputfile):
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

        # EOT state variables
        self.got_eot = False

        # Output
        self.file = outputfile
        self.buf = bytearray()

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
            if(addr[0] == self.emulator):
                return packet.unpack_packet(pkt)

    """We'll stay in this state until receiving a SYN or FIN"""
    def wait_for_syn(self):
        pkt = self.wait_for_packet(False)
        if(pkt.flags == packet.Type.FIN):
            print("received FIN packet, finishing up")
            self.is_done = True
            self.finish_status = DONE
        elif(pkt.flags == (packet.Type.EOT | packet.Type.ACK)):
            print("received EOT/ACK packet while waiting for SYN; remote side didn't receive final ACK, retransmitting")
            self.sock.sendto(packet.pack_packet(packet.create_ack_packet(0, 0)), (self.emulator, self.port))

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

            # write buffer to file and create an empty buffer
            self.file.write(self.buf)
            self.buf = bytearray()

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

        elif(rcvd.flags == packet.Type.ACK and self.got_eot):
            print("received ACK for EOT/ACK, switching modes")
            self.is_done = True
            self.finish_status = SWITCH

        elif(rcvd.flags == packet.Type.EOT):
            print("received EOT packet, responding with EOT/ACK")
            self.sock.sendto(packet.pack_packet(packet.create_eot_ack_packet()), (self.emulator, self.port))
            self.got_eot = True

        elif(rcvd.flags == packet.Type.DATA):
            # we got a spurious retransmission
            if(rcvd.seq_num != self.ack_num):
                if(rcvd.seq_num < self.ack_num):
                    print("spurious retransmission with sequence number {}".format(rcvd.seq_num))
                    return
                else:
                    # != and ! < , so it's greater than the ACK number we were expecting, AKA packets were dropped (or re-ordered, but that's unlikely)
                    print("received packet with sequence number {}, packet with sequence number {} was dropped".format(rcvd.seq_num, self.ack_num))
                    return

            # the sender will always send max data unless it's almost out of data
            # in that case, we don't want to wait for the timeout
            # we should receive an EOT after this (but it shouldn't actually cause problems if not)
            if(rcvd.data_len < packet.MAX_DATA_LENGTH):
                print("packet had length {}; acking now".format(str(rcvd.data_len)))
                self.ack_now = True

            self.rcvd_window_bytes += rcvd.data_len
            self.latest_ack = packet.create_ack_packet_from_data(rcvd, self.seq_num)
            self.ack_num += rcvd.data_len
            print("received packet with sequence number {}; received {} bytes this window, current ack number is {}".format(rcvd.seq_num, self.rcvd_window_bytes, self.ack_num))
            self.buf.extend(rcvd.data)


    def run(self):
        try:
            print("waiting for SYN packet...")
            self.wait_for_syn()
            if(self.is_done):
                print("finished running, returning status {}".format("SWITCH" if self.finish_status == SWITCH else "DONE"))
                return self.finish_status
        
            print("entering main receiver loop")
            while(not self.is_done):
                self.handle_next_packet()
        except KeyboardInterrupt:
            print("\ncaught keyboard interrupt, sending FIN")
            self.sock.sendto(packet.pack_packet(packet.create_fin_packet()), (self.emulator, self.port))
            self.finish_status = DONE

        print("finished running, returning status {}".format("SWITCH" if self.finish_status == SWITCH else "DONE"))
        return self.finish_status

class Host:
    def __init__(self, cfg_file_path, outputfile):
        if(not os.path.isfile(cfg_file_path)):
            raise TypeError("cfg_file_path must point to an existing file")

        with open(cfg_file_path) as config_file:    
            self.config = json.load(config_file)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.config["port"]))
        self.sock.settimeout(self.config["timeout"])
        self.file = outputfile

    def run(self):
        receiver = Receiver(self.sock, self.config["port"], self.config["emulator"], self.config["window_size"], self.file)
        result = receiver.run()
        if(result == DONE):
            return

if(__name__ == "__main__"):
    # check whether we're supposed to receive or send first based on cmd-line args
    # start host in appropriate mode 
    if(len(sys.argv) != 3):
        print("usage: host [config file] [output file]")
        sys.exit(1)

    try:
        outputfile = open(sys.argv[2], 'wb')
    except:
        print("{} is not a writable file or could not be opened for writing".format(sys.argv[2]))

    try:
        h = Host(sys.argv[1], outputfile)
        h.run()
    except Exception as err:
        print(str(err))
