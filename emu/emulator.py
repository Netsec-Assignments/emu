import emu.packet as packet
import socket
import sys
import os
import json
import random
import time

if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print("usage: emulator [config file] [BER|Delay|Both|None]")
        sys.exit(1)
    elif (not os.path.isfile(sys.argv[1])):
        print("no such file {}!".format(sys.argv[1]))
        sys.exit(1)
   
    emulator_function = sys.argv[2]
        
    
    with open(sys.argv[1]) as config_file:    
        config = json.load(config_file)

    delay1 = config["delay"] - config["delay"]/2
    delay2 = config["delay"] + config["delay"]/2
    bit_error_percent = config["BER"]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', config["port"]))
    print("    Welcome to the goodput emulator\n")
    print("    Shane Spoor and Mat Siwoski\n")
    
    print("started emulator with host 0 {} and host 1 {} on port {}".format(config["host0"], config["host1"], config["port"]))
    print("user has select {} for the emulator function".format(emulator_function))
    
    while(True):
        try:
            pack = None
            pack, addr = sock.recvfrom(packet.MAX_PACKET_LENGTH)
            unpacked = packet.unpack_packet(pack)
            flags = []
            if(unpacked.flags & packet.Type.DATA):
                flags.append("DATA")
            if(unpacked.flags & packet.Type.ACK):
                flags.append("ACK")
            if(unpacked.flags & packet.Type.SYN):
                flags.append("SYN")
            if(unpacked.flags & packet.Type.EOT):
                flags.append("EOT")
            if(unpacked.flags & packet.Type.FIN):
                flags.append("FIN")
            print("received packet with flags {}, seq num {}, ack_num {}".format('|'.join(map(str, flags)), unpacked.seq_num, unpacked.ack_num))
            
            if (emulator_function == "BER"):
                bit_error_rate = random.randrange(0, 100)
                print("the bit error rate is {}".format(bit_error_rate))
            elif (emulator_function == "Delay"):
                delay = random.uniform(delay1 ,delay2)
                print("delay for this packet is {} seconds".format(delay / 10))
            elif(emulator_function == "Both"):
                bit_error_rate = random.randrange(0, 100)
                print("Bit Error rate of {} && bit error percent of {}".format(bit_error_rate,bit_error_percent))
                delay = random.uniform(delay1 ,delay2)
                print("delay for this packet is {} seconds".format(delay / 10))

            dest = None            
            if (addr[0] == config["host0"]):
                dest = config["host1"]
            elif (addr[0] == config["host1"]):
                dest = config["host0"]

            if (dest):
                if(emulator_function == "None"):
                     print("send all the packets")
                     sock.sendto(pack, (dest, config["port"]))
                elif (emulator_function == "BER"):
                    if(bit_error_rate >= bit_error_percent):
                        print("received packet from {}, forwarding to {}".format(addr[0], dest))
                        sock.sendto(pack, (dest, config["port"]))
                    else:
                        print("packet has been dropped")
                elif (emulator_function == "Delay"):
                    print("received packet from {}, forwarding to {}".format(addr[0], dest))
                    time.sleep(delay / 10)
                    sock.sendto(pack, (dest, config["port"]))
                elif (emulator_function == "Both"):
                    if(bit_error_rate >= bit_error_percent):
                        time.sleep(delay / 10)
                        print("received packet from {}, forwarding to {}".format(addr[0], dest))
                        sock.sendto(pack, (dest, config["port"]))
                    else:
                        print("packet has been dropped")
                        pack = None
                
        except KeyboardInterrupt:
            print("\nCaught keyboard interrupt, exiting")
            sys.exit(0)
