import unittest
import unittest.mock as mock
import emu.host as host
import emu.packet as packet

class ReceiverTestCase(unittest.TestCase):
    
    @mock.patch('emu.host.socket')
    def test_syn(self, mock_socket):
        # mock variables
        syn_packet = packet.create_syn_packet()
        mock_socket.recvfrom.return_value = (packet.pack_packet(syn_packet), "127.0.0.1")

        expected_response = packet.pack_packet(packet.create_synack_packet(syn_packet))
        r = host.Receiver(mock_socket, 10, "127.0.0.1")
        r.wait_for_syn()

        mock_socket.sendto.assert_called_with(expected_response, ("127.0.0.1", 10))
        
