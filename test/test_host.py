import unittest
import unittest.mock as mock
import emu.host as host
import emu.packet as packet
import socket

class ReceiverTestCase(unittest.TestCase):
    @mock.patch('emu.host.socket.socket')
    def test_syn(self, mock_socket):
        # mock variables
        syn_packet = packet.create_syn_packet()
        mock_socket.recvfrom.return_value = (packet.pack_packet(syn_packet), "127.0.0.1")

        expected_response = packet.pack_packet(packet.create_synack_packet(syn_packet))
        r = host.Receiver(mock_socket, 10, "127.0.0.1", 10)
        r.wait_for_syn()

        mock_socket.sendto.assert_called_with(expected_response, ("127.0.0.1", 10))

    @mock.patch('emu.host.socket.socket')
    def test_dup_syn(self, mock_socket):
        syn_packet = packet.create_syn_packet()
        mock_socket.recvfrom.side_effect = [(packet.pack_packet(syn_packet), "127.0.0.1"),
                                            (packet.pack_packet(syn_packet), "127.0.0.1")]

        expected_response = packet.pack_packet(packet.create_synack_packet(syn_packet))
        r = host.Receiver(mock_socket, 10, "127.0.0.1", 10)
        r.wait_for_syn()
        r.handle_next_packet()
        mock_socket.sendto.assert_called_with(expected_response, ("127.0.0.1", 10)) # assert_called_with = most recent call
    
    @mock.patch('emu.host.socket.socket')
    def test_data_timeout(self, mock_socket):
        mock_socket.recvfrom.side_effect = socket.timeout("timed out")

        latest_ack = packet.create_synack_packet(packet.create_syn_packet())
        r = host.Receiver(mock_socket, 10, "127.0.0.1", 10)
        r.latest_ack = latest_ack

        r.handle_next_packet()

        mock_socket.sendto.assert_called_with(packet.pack_packet(latest_ack), ("127.0.0.1", 10))

    @mock.patch('emu.host.socket.socket')
    def test_dup_data(self, mock_socket):
        data = bytes([128] * 512)
        latest_data = packet.create_data_packets(data, 0)[0]
        mock_socket.recvfrom.return_value = (packet.pack_packet(latest_data), "127.0.0.1")

        latest_ack = packet.create_ack_packet_from_data(latest_data, 0)

        r = host.Receiver(mock_socket, 10, "127.0.0.1", 10)
        r.latest_ack = latest_ack
        r.ack_num = 512

        r.handle_next_packet()

        mock_socket.sendto.assert_called_with(packet.pack_packet(latest_ack), ("127.0.0.1", 10))

    @mock.patch('emu.host.socket.socket')
    def test_data(self, mock_socket):
        data = bytes([128] * packet.MAX_LENGTH * 10)
        data_packets = packet.create_data_packets(data, 1)
        # return a different value on each call
        mock_socket.recvfrom.side_effect = [(packet.pack_packet(data_packets[0]), "127.0.0.1"),
                                            (packet.pack_packet(data_packets[1]), "127.0.0.1"),
                                            (packet.pack_packet(data_packets[2]), "127.0.0.1"),
                                            (packet.pack_packet(data_packets[3]), "127.0.0.1"),
                                            (packet.pack_packet(data_packets[4]), "127.0.0.1"),
                                            (packet.pack_packet(data_packets[5]), "127.0.0.1"),
                                            (packet.pack_packet(data_packets[6]), "127.0.0.1"),
                                            (packet.pack_packet(data_packets[7]), "127.0.0.1"),
                                            (packet.pack_packet(data_packets[8]), "127.0.0.1"),
                                            (packet.pack_packet(data_packets[9]), "127.0.0.1"),
                                            (packet.pack_packet(packet.create_fin_packet()), "127.0.0.1")]

        expected_ack = packet.create_ack_packet_from_data(data_packets[9], 0)
        r = host.Receiver(mock_socket, 10, "127.0.0.1", 10)
        r.latest_ack = packet.create_synack_packet(packet.create_syn_packet())
        r.ack_num = 1

        for i in range(11):
            r.handle_next_packet()

        mock_socket.sendto.assert_called_with(packet.pack_packet(expected_ack), ("127.0.0.1", 10))
        self.assertEqual(r.ack_num, 14611)
