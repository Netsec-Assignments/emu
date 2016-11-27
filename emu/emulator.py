import emu.packet as packet
import socket
import sys
import os
import json
import random
import time

if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print("usage: emulator [config file] [BER|Delay|Both]")
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
    sock.bind(('', config["port"]))

    print("started emulator with host 0 {} and host 1 {} on port {}".format(config["host0"], config["host1"], config["port"]))
    print("user has select {} for the emulator function".format(emulator_function))
    
    while(True):
        pack, addr = sock.recvfrom(packet.MAX_PACKET_LENGTH)
        if (emulator_function == "BER"):
            bit_error_rate = random.randrange(0, 100)
            print("the bit error rate is {}".format(bit_error_rate))
        elif (emulator_function == "Delay"):
            delay = random.randrange(delay1, delay2)
            print("delay for this packet is {} seconds".format(delay / 10))
        elif(emulator_function == "Both"):
            bit_error_rate = random.randrange(0, 100)
            print("the bit error rate is {}".format(bit_error_rate))
            delay = random.randrange(delay1, delay2)
            print("delay for this packet is {} seconds".format(delay / 10))
        if (addr[0] == config["host0"]):
            if (emulator_function == "BER"):
                if(bit_error_rate > bit_error_percent):
                    print("received packet from {}, forwarding to {}".format(config["host0"], config["host1"]))
                    sock.sendto(pack, (config["host1"], config["port"]))
                else:
                    print("packet has been dropped")
            elif (emulator_function == "Delay"):
                print("received packet from {}, forwarding to {}".format(config["host0"], config["host1"]))
                time.sleep(delay / 10)
                sock.sendto(pack, (config["host1"], config["port"]))
            elif (emulator_function == "Both"):
                if(bit_error_rate > bit_error_percent):
                    time.sleep(delay / 10)
                    print("received packet from {}, forwarding to {}".format(config["host0"], config["host1"]))
                    sock.sendto(pack, (config["host1"], config["port"]))
                else:
                    print("packet has been dropped")
        elif (addr[0] == config["host1"]):
            if (emulator_function == "BER"):
                if(bit_error_rate > bit_error_percent):
                    print("received packet from {}, forwarding to {}".format(config["host1"], config["host0"]))           
                    sock.sendto(pack, (config["host0"], config["port"]))
                else:
                    print("packet has been dropped")
            elif (emulator_function == "Delay"):
                print("received packet from {}, forwarding to {}".format(config["host1"], config["host0"]))
                time.sleep(delay / 10)            
                sock.sendto(pack, (config["host0"], config["port"]))
            elif (emulator_function == "Both"):
                if(bit_error_rate > bit_error_percent):
                    time.sleep(delay / 10)
                    print("received packet from {}, forwarding to {}".format(config["host1"], config["host0"]))           
                    sock.sendto(pack, (config["host0"], config["port"]))
                else:
                    print("packet has been dropped")
