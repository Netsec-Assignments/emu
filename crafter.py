import emu.packet as packet
import socket
import sys

if(__name__ == "__main__"):
    # check whether we're supposed to receive or send first based on cmd-line args
    # start host in appropriate mode 
    if(len(sys.argv) != 3):
        print("usage: crafter [dest host IP] [port]")
        sys.exit(1)

    # sock is implicitly bound on sendto, so don't need to bind
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = sys.argv[1]
    port = int(sys.argv[2])
    command_briefs = ["help", "exit", "SYN", "SYNACK", "ACK [ack_num]", "DATA [start_seq] [length]", "EOT", "FIN"]
    commands = {"SYN": "sends a SYN packet with seq_num 0",
                "SYNACK": "SYNACK: sends a SYN/ACK packet with seq_num 0, ack_num 1",
                "ACK": "ACK [ack_num]: sends an ACK with the specified ack number",
                "DATA": "DATA [start_seq] [length]: sends length bytes of data with start sequence number start_seq; if length > 1461, multiple packets are sent" ,
                "EOT": "EOT: sends an EOT packe",
                "FIN": "FIN: sends a FIN packet",
                "help": "help: lists commands; type help [command] to view more detail for a command (but you already knew that)",
                "exit": "exit: quit the program"}

    print("type help for a list of commands\n")
    while(True):
        try:
            raw = input("Enter a command: ")
        except EOFError:
            print("see ya")
            sys.exit(0)

        raw = raw.split()
        command = raw[0]
        args = raw[1:]

        if(command == "help"):
            if(args):
                if(len(args) > 1):
                    print("syntax: help [command name]")
                elif(not args[0] in commands):
                    print("Invalid command {}. Type help for a list of commands.".format(args[0]))
                else:
                    print("{}".format(commands[args[0]]))
            else:
                print("Type help [command] to view more detail for a command")
                for cmd in command_briefs:
                    print(cmd)

        elif(command == "SYN"):
            if(args):
                print("SYN doesn't take any arguments. Sending SYN anyway")
            sock.sendto(packet.pack_packet(packet.create_syn_packet()), (dest, port))
            print("sent SYN packet to {} on port {}".format(dest, port))

        elif(command == "SYNACK"):
            if(args):
                print("SYNACK doesn't take any arguments. Sending SYN/ACK anyway")
            sock.sendto(packet.pack_packet(packet.create_synack_packet(packet.create_syn_packet())), (dest, port))
            print("sent SYN/ACK packet with to {} on port {}".format(dest, port))

        elif(command == "ACK"):
            if(len(args) != 1):
                print("usage: ACK [ack_num] (enter 'help ACK' for more)")
            else:
                sock.sendto(packet.pack_packet(packet.create_ack_packet(int(args[0]), 0)), (dest, port))
                print("sent ACK packet with ack {} to {} on port {}".format(args[0], dest, port))

        elif(command == "DATA"):
            if(len(args) != 2):
                print("usage: DATA [start_seq] [length] (enter 'help DATA' for more')")
            else:
                packets = packet.create_data_packets(bytes([128] * int(args[1])), int(args[0]))
                for p in packets:
                    sock.sendto(packet.pack_packet(p), (dest, port))
                    print("sent DATA packet with seq {} and data len {} to {} on port {}".format(p.seq_num, p.data_len, dest, port))

        elif(command == "EOT"):
            if(args):
                print("EOT doesn't take any arguments. Sending EOT anyway")          
            sock.sendto(packet.pack_packet(packet.create_eot_packet()), (dest, port))
            print("sent EOT packet to {} on port {}".format(dest, port))

        elif(command == "FIN"):
            if(args):
                print("FIN doesn't take any arguments. Sending FIN anyway")
            sock.sendto(packet.pack_packet(packet.create_fin_packet()), (dest, port))
            print("sent SYN packet to {} on port {}".format(dest, port))

        elif(command == "exit"):
            print("see ya")
            sys.exit(0)

        else:
            print("Invalid command {}. Type help for a list of commands.".format(command))
