import emu.packet as packet
import socket
import sys
import os
import json
import random
import time

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("usage: emulator [config file]")
        sys.exit(1)
    elif (not os.path.isfile(sys.argv[1])):
        print("no such file {}!".format(sys.argv[1]))
        sys.exit(1)

    with open(sys.argv[1]) as config_file:    
            config = json.load(config_file)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', config["port"]))

    print("started emulator with host 0 {} and host 1 {} on port {}".format(config["host0"], config["host1"], config["port"]))
 
    while(True):
        pack, addr = sock.recvfrom(packet.MAX_PACKET_LENGTH)
        delay1 = config["delay"] - config["delay"]/2
        delay2 = config["delay"] + config["delay"]/2
        delay = random.randrange(delay1, delay2)
        print("delay for this packet is {} seconds".format(delay / 10))
        if (addr[0] == config["host0"]):
            print("received packet from {}, forwarding to {}".format(config["host0"], config["host1"]))
            time.sleep(delay / 10)
            sock.sendto(pack, (config["host1"], config["port"]))
        elif (addr[0] == config["host1"]):
            print("received packet from {}, forwarding to {}".format(config["host1"], config["host0"]))
            time.sleep(delay / 10)            
            sock.sendto(pack, (config["host0"], config["port"]))
