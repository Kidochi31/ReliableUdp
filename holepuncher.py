from udpsocket import UdpSocket
from threading import Lock
from common import debug_print
from iptools import IP_endpoint
from packet import create_keep_alive_packet
import time

HOLE_PUNCH_PERIOD_NS = 5_000_000_000

class HolePuncher:
    # local_endpoint: IP_endpoint - the endpoint the listener is bound to
    # udp_socket: UdpSocket - the UDP Socket used to send and receive info
    # lock: Lock
    # hole_punchers: list[IP_endpoint, (int, int | None)] - the dictionary of connecting TCP sockets and (time since last send (ns), expiry time (ns))
    # hole_punch_fails: list[IP_endpoint] - a list of remote endpoints that could not be connected to (and have yet to be managed)
    
    def __init__(self, udp_socket: UdpSocket):
        self.udp_socket = udp_socket
        self.local_endpoint = self.udp_socket.get_local_endpoint()
        self.lock = Lock()
        self.hole_punchers:dict[IP_endpoint, tuple[int, int | None]] = {} 
        self.fails:set[IP_endpoint] = set()
    
    def remove_hole_puncher(self, endpoint: IP_endpoint):
        with self.lock:
            if endpoint in self.hole_punchers.keys():
                self.hole_punchers.pop(endpoint)
            if endpoint in self.fails:
                self.fails.remove(endpoint)

    def hole_punch(self, endpoint: IP_endpoint, timeout: float | None):
        with self.lock:
            if endpoint in self.hole_punchers:
                debug_print(f"already hole puncher!")
                return
            if endpoint in self.fails:
                self.fails.remove(endpoint)
            self.udp_socket.send_immediate(create_keep_alive_packet(), endpoint)
            expiry_time = None if (timeout is None or timeout < 0) else time.time_ns() + int(timeout * 1_000_000_000)
            self.hole_punchers[endpoint] = (time.time_ns() + HOLE_PUNCH_PERIOD_NS, expiry_time)
    
    def tick(self):
        with self.lock:
            for endpoint in list(self.hole_punchers.keys()):
                next_hole_punch_time, expiry_time = self.hole_punchers[endpoint]
                if expiry_time is not None and expiry_time <= time.time_ns():
                    # expired -> FAILURE
                    self.hole_punchers.pop(endpoint)
                    self.fails.add(endpoint)
                    continue
                if next_hole_punch_time <= time.time_ns():
                    self.udp_socket.send_immediate(create_keep_alive_packet(), endpoint)
                    self.hole_punchers[endpoint] = (time.time_ns() + HOLE_PUNCH_PERIOD_NS, expiry_time)

    def take_fails(self) -> list[IP_endpoint]:
        with self.lock:
            fails = list(self.fails)
            self.fails.clear()
            return fails
        
    def clear(self):
        with self.lock:
            self.hole_punchers.clear()
            self.fails.clear()