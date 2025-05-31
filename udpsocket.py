from socket import socket, AddressFamily
from common import make_socket_reusable, BUFSIZE
from select import select
from threading import Lock
from stun import get_ip_info
from iptools import *

class UdpSocket:
    # socket: socket - the udp socket to be used
    # local_endpoint: IP_endpoint - the endpoint the udp socket is bound to
    # external_endpoint: IP_endpoint | None - the endpoint the udp socket is bound to on the open internet
    # keep_alive_timer: Timer - used to ensure that the hole is kept open in the NAT
    # send_lock: Lock
    # keep_alive_targets: set[endpoint] - Udp packets will be sent to these endpoints every 10 seconds to keep udp connections alive
    # closed: bool
    def __init__(self, port: int, stun_hosts: list[unresolved_endpoint], family: AddressFamily):
        self.socket = create_udp_socket(port, family)
        self.local_endpoint = get_canonical_local_endpoint(self.socket)
        self.external_endpoint = get_ip_info(self.socket, stun_hosts)
        self.send_lock = Lock()
        self.closed = False
    
    def get_local_endpoint(self) -> IP_endpoint:
        return self.local_endpoint

    def _ready_to_receive(self) -> bool:
        try:
            rlist, _, _ = select([self.socket], [], [], 0)
            return len(rlist) > 0
        except:
            return False
    
    def get_external_endpoint(self) -> IP_endpoint | None:
        return self.external_endpoint

    def receive(self) -> list[tuple[bytes, IP_endpoint | None]]:
        result: list[tuple[bytes, IP_endpoint | None]] = []
        while self._ready_to_receive():
            try:
                data, endpoint = self.socket.recvfrom(BUFSIZE)
                result.append((data, get_canonical_endpoint(endpoint, self.socket.family)))
            except:
                break
        return result
    
    def send_immediate(self, data: bytes, endpoint: IP_endpoint):
        with self.send_lock:
            if self.closed:
                return
            try:
                self.socket.sendto(data, endpoint)
            except:
                return
    
    def close(self):
        with self.send_lock:
            self.closed = True
            self.socket.close()
    
def create_udp_socket(port: int, family: AddressFamily) -> socket:
    udp_socket = socket(family, SOCK_DGRAM)
    make_socket_reusable(udp_socket)
    udp_socket.bind(('', port)) # bind the socket
    return udp_socket