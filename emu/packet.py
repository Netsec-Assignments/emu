import struct
from enum import IntEnum

"""Represents a packet for the protocol"""
class Packet:
    def __init__(self, flags, ack_num, seq_num, data):
        self.flags = flags
        self.ack_num = ack_num
        self.seq_num = seq_num

        if(data != None):
            self.data_len = len(data)
        else:
            self.data_len = 0

        self.data = data

MAX_DATA_LENGTH = 1461
MAX_PACKET_LENGTH = 1472

"""Flags for different packet types"""
class Type(IntEnum):
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

def create_ack_packet(ack_num, seq_num):
    flags = Type.ACK
    return Packet(flags, ack_num, seq_num, None)

def create_ack_packet_from_data(data_packet, start_seq):
    seq_num = start_seq
    ack_num = data_packet.seq_num + data_packet.data_len
    flags = Type.ACK
    return Packet(flags, ack_num, seq_num, None)

def create_syn_packet():
    seq_num = 0
    ack_num = 0
    flags = Type.SYN
    return Packet(flags, ack_num, seq_num, None)

def create_synack_packet(syn_packet):
    if(syn_packet.flags != Type.SYN):
        raise TypeError("packet must have only SYN flag set")

    seq_num = 0
    ack_num = 1
    flags = Type.SYN | Type.ACK
    return Packet(flags, ack_num, seq_num, None)

def create_eot_packet():
    return Packet(Type.EOT, 0, 0, None)

def create_fin_packet():
    return Packet(Type.FIN, 0, 0, None)

def pack_packet(p):
    # Format string corresponds to
    # unsigned char
    # unsigned int
    # unsigned int
    # unsigned short
    # char[] with a given number of members

    format_str = "!BIIH"
    if(p.data):
        format_str += str(p.data_len) + 's'
        return struct.pack(format_str, p.flags, p.ack_num, p.seq_num, p.data_len, p.data)
    else:
        return struct.pack(format_str, p.flags, p.ack_num, p.seq_num, p.data_len)

def unpack_packet(buf):
    format_str = "!BIIH"
    data_len = struct.unpack_from("!H", buf, 9)[0]

    if(data_len != 0):
        format_str += str(data_len) + 's'
        flags, ack_num, seq_num, data_len, data = struct.unpack(format_str, buf)
        return Packet(flags, ack_num, seq_num, data)
    else:
        flags, ack_num, seq_num, data_len = struct.unpack(format_str, buf)
        return Packet(flags, ack_num, seq_num, None)
