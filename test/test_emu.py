import unittest
import sys
from emu import packet
Packet = packet.Packet

class PacketCreationTestCase(unittest.TestCase):
    def test_single_data_packet(self):
        # Input: byte array with Packet.MAX_LENGTH elements (all set to 128)        
        buf = bytes([128] * packet.MAX_LENGTH)
        result = packet.create_data_packets(buf, 0)
        
        # Expected output: 1 packet with seq_num = 0, flags = DATA,
        # data_len = Packet.MAX_LENGTH, data = buf
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].seq_num, 0)
        self.assertEqual(result[0].flags, packet.Type.DATA)
        self.assertEqual(result[0].data_len, packet.MAX_LENGTH)
        self.assertEqual(result[0].data, buf)

    def test_multiple_data_packets(self):
        # Input: byte array with Packet.MAX_LENGTH + 512 elements
        buf = bytes([128] * (packet.MAX_LENGTH + 512))
        result = packet.create_data_packets(buf, 0)
        
        # Expected output: 2 packets
        self.assertEqual(len(result), 2)

        # packet 1 with seq_num = 0, flags = DATA,
        # data_len = Packet.MAX_LENGTH, data = buf[0:Packet.MAX_LENGTH)
        self.assertEqual(result[0].seq_num, 0)
        self.assertEqual(result[0].flags, packet.Type.DATA)
        self.assertEqual(result[0].data_len, packet.MAX_LENGTH)
        self.assertEqual(result[0].data, buf[0:packet.MAX_LENGTH])

        # packet 2 with seq_num = Packet.MAX_LENGTH, flags = DATA,
        # data_len = Packet.MAX_LENGTH + 512, data = buf[Packet.MAX_LENGTH:end]
        self.assertEqual(result[1].seq_num, packet.MAX_LENGTH)
        self.assertEqual(result[1].flags, packet.Type.DATA)
        self.assertEqual(result[1].data_len, 512)
        self.assertEqual(result[1].data, buf[packet.MAX_LENGTH:])

    def test_ack_packet(self):
        # Input: packet with data flag set, ack num 0, seq 0, data len 1472;
        # starting sequence number = 10
        data = bytes([128] * packet.MAX_LENGTH)
        data_packet = Packet(packet.Type.DATA, 0, 0, data)
        start_seq = 10

        result = packet.create_ack_packet(data_packet, start_seq)

        # Expected output: packet with sequence number = start_seq_num
        # flags = ACK, ack number: packet.MAX_LENGTH, data len = 0,
        # data = None
        self.assertEqual(result.seq_num, start_seq)
        self.assertEqual(result.flags, packet.Type.ACK)
        self.assertEqual(result.ack_num, packet.MAX_LENGTH)
        self.assertEqual(result.data_len, 0)
        self.assertEqual(result.data, None)

    def test_syn_packet(self):
        # Input: nothing

        result = packet.create_syn_packet()

        # Expected output: packet with
        #   sequence number: 0
        #   flags: SYN
        #   ack number: N/A (not explicitly set)
        #   data len: 0
        #   data: None
        self.assertEqual(result.seq_num, 0)
        self.assertEqual(result.flags, packet.Type.SYN)
        self.assertEqual(result.data_len, 0)
        self.assertEqual(result.data, None)

    def test_synack_packet_invalid(self):
        # Input: packet with any flag other than SYN set

        p = Packet(
                   packet.Type.DATA,
                   0,
                   0,
                   None)
        with self.assertRaises(TypeError) as cm:
            packet.create_synack_packet(p)

        self.assertEqual(str(cm.exception), "packet must have only SYN flag set")
    
    def test_synack_packet_valid(self):
        # Input: packet with SYN flag set, data len 0, seq 0 (other vars ignored)
        p = Packet(
                   packet.Type.SYN,
                   0,
                   0,
                   None)

        # Expected output: packet with
        #   sequence number: 0
        #   ack number: 1 (next expected byte)
        #   data len: 0
        #   data: none
        result = packet.create_synack_packet(p)
        self.assertEqual(result.flags, packet.Type.SYN | packet.Type.ACK)
        self.assertEqual(result.seq_num, 0)
        self.assertEqual(result.ack_num, 1)
        self.assertEqual(result.data_len, 0)
        self.assertEqual(result.data, None)

    def test_eot_packet(self):
        # Input: N/A
        # Output: packet with EOT flag set and all other members at default values
        result = packet.create_eot_packet()
        self.assertEqual(result.flags, packet.Type.EOT)

    def test_fin_packet(self):
        # Input: N/A
        # Output: packet with FIN flag set and all other members at default values
        result = packet.create_fin_packet()
        self.assertEqual(result.flags, packet.Type.FIN)

    def test_packing(self):
        # Input: a data packet containing MAX_LENGTH bytes of data
        buf = bytes([128] * (packet.MAX_LENGTH))
        p = Packet(
                    packet.Type.DATA,
                    0,
                    0,
                    buf)

        packed = packet.pack_packet(p)
        unpacked = packet.unpack_packet(packed)
        
        # Expected output (after packing and unpacking: a packet identical to the packed one
        self.assertEqual(unpacked.flags, p.flags)
        self.assertEqual(unpacked.ack_num, p.ack_num)
        self.assertEqual(unpacked.seq_num, p.seq_num)
        self.assertEqual(unpacked.data_len, p.data_len)
        self.assertEqual(unpacked.data, p.data)

if __name__ == "__main__":
    unittest.main()
