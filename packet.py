from enum import Enum

"""Represents a packet for the protocol"""
class Packet:
    def __init__(self, flags, ack_num, seq_num, data):
        self.flags = flags
        self.ack_num = ack_num
        self.seq_num = seq_num
        self.data = data

        if(self.data != None):
            self.data_len = len(data)
        else:
            self.data_len = 0

MAX_LENGTH = 1472

"""Flags for different packet types"""
class Type(Enum):
    DATA = 1
    ACK = 2
    SYN = 4
    EOT = 8
    FIN = 16

def create_data_packets(buf, start_seq):
    if(buf == None):
        raise ValueError("buf cannot be None")

    ack_num = 0
    buf_len = len(buf)
    whole_chunks = buf_len // MAX_LENGTH
    partial_chunk_size = buf_len % MAX_LENGTH

    packets = []

    # Make as many full-sized packets as we can out of the provided buffer
    for i in range(0, whole_chunks):
        slice_start = i * MAX_LENGTH
        slice_end = (i + 1) * MAX_LENGTH
        p = Packet(
                   Type.DATA,
                   ack_num,
                   start_seq + (i * MAX_LENGTH),
                   bytes(buf[slice_start:slice_end]))
        packets.append(p)

    # If there were any left-over bytes, make another packet with those
    if(partial_chunk_size):
        partial_chunk_seq = start_seq + (whole_chunks * MAX_LENGTH)
        p = Packet(
                   Type.DATA,
                   ack_num,
                   partial_chunk_seq,
                   bytes(buf[partial_chunk_seq:]))
        packets.append(p)

    return packets

def create_ack_packet(data_packet, start_seq):
    seq_num = start_seq
    ack_num = data_packet.seq_num + data_packet.data_len
    flags = Type.ACK
    return Packet(flags, ack_num, seq_num, None)

def create_syn_packet():
    pass

def create_synack_packet(syn_packet):
    pass

def create_eot_pakcet():
    pass

def create_fin_packet():
    pass
