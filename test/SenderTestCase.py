import unittest
from  mock import Mock
import sys

import sender

class SenderTestCase(unittest.TestCase):
    def test_socket_connection(self):
        content = sender.read_config()
        client = sender.Client(content[0], content[1])
        self.assertEqual(content[0], "127.0.0.1")
        self.assertEqual(int(content[1]), 7000)
    #@mock.patch("socket.socket.connect")
    def test_socket_connections(self):
        #mock_connection.assert_called_with(ANY, ('127.0.0.1', 7000))
        mock = Mock(ip = '127.0.0.1', port = 7000)
        client = sender.Client(mock.ip, mock.port)
        
        
        
