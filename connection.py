from udpsocket import UdpSocket
from iptools import *
from threading import Lock
from connectionsender import ConnectionSender
from connectionreceiver import ConnectionReceiver
from connectionstate import ConnectionState
from packet import create_unreliable_packet

class Connection:
    # tcp_socket: socket - the socket of the tcp connection
    # local_endpoint: IP_endpoint - the local endpoint of the sockets
    # remote_endpoint: IP_endpoint - the destination of the sockets
    # closed: bool - whether the connection has been closed

    def __init__(self, udp_socket: UdpSocket, remote_endpoint: IP_endpoint):
        self.udp_socket = udp_socket
        self.remote_endpoint = remote_endpoint
        self.lock = Lock()
        self.state = ConnectionState()
        self.sender = ConnectionSender(self.state)
        self.receiver = ConnectionReceiver(self.state, 100)
        self.closed = False
    
    def close(self):
        with self.lock:
            self.closed = True
    
    
    def send_unreliable(self, data: bytes):
        with self.lock:
            if self.closed:
                return
            self.udp_socket.send_immediate(create_unreliable_packet(0, data), self.remote_endpoint)
    
    def send_reliable(self, data:bytes):
        with self.lock:
            if self.closed:
                return
            self.sender.queue_data(data)

    def tick_still_connected(self) -> bool:
        with self.lock:
            if self.closed:
                return False
            if not self.sender.tick(self.remote_endpoint, self.udp_socket):
                self.closed = True
                return False
            if not self.receiver.tick():
                self.closed = True
                return False
            return True
            