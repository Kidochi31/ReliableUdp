from connectionstate import ConnectionState
import time
from udpsocket import UdpSocket
from packet import create_reliable_packet, create_keep_alive_packet, create_ack_only_packet
from iptools import *
from threading import Lock

MAX_PAYLOAD_SIZE = 500
MAX_RETRANSMISSIONS = 6
MAX_SILENCE = 3_000_000_000
MAX_ACK_WAIT = 200_000_000

class ConnectionSender:

    # send_window - list[(bytes, int, int)] - a list of bytes to be sent (data, send_time, retransmission_timeout, num_retransmissions)
    # seq - the lowest unacknowledged seq
    def __init__(self, state: ConnectionState):
        self.state = state
        self.send_window: list[tuple[bytes, int, int, int]] = []
        self.cwnd = 1
        self.data_queue: list[bytes] = []
        self.data_queue_lock = Lock()
        self.send_ack = False
        self.silence_timeout: int = 0
        self.rtt: int = 10_000_000_000

    
    def queue_data(self, data: bytes):
        with self.data_queue_lock:
            self.data_queue.append(data)
    
    def report_received_ack(self, ack: int | None):
        if ack is None:
            return
        # need to remove acks from send window
        number_to_ack = self.state.ack_outgoing(ack)
        if number_to_ack > len(self.send_window) or number_to_ack == 0:
            return
        _, send_time, _,  _ = self.send_window[number_to_ack - 1]
        self.rtt = int(0.8 * self.rtt) + int(0.2 * (time.time_ns() - send_time))

        self.cwnd += number_to_ack / self.cwnd
        self.send_window = self.send_window[number_to_ack:]
    
    def report_outgoing_ack_change(self):
        ack_send_time = time.time_ns() + MAX_ACK_WAIT
        if ack_send_time < self.silence_timeout:
            self.silence_timeout = ack_send_time
        self.send_ack = True

        
    def tick(self, remote_endpoint: IP_endpoint, socket: UdpSocket) -> bool:
        """
        Returns true if still connected
        """
        # first, add new data to send window
        self._enqueue_new_data()

        # second, retransmit data
        for i, (data, send_time, retransmission_timeout, num_retransmissions) in enumerate(self.send_window):
            if retransmission_timeout <= time.time_ns():
                # check if reached max retransmissions => presume disconnection
                if num_retransmissions >= MAX_RETRANSMISSIONS:
                    return False
                # retransmit
                if num_retransmissions != -1:
                    self.rtt = int(self.rtt * 1.5)
                    self.cwnd = self.cwnd * 0.75
                    if self.cwnd < 1:
                        self.cwnd = 1
                packet = create_reliable_packet(self.state.get_outgoing_seq(i), self.state.get_outgoing_ack(), False, data)
                socket.send_immediate(packet, remote_endpoint)
                self.send_window[i] = (data, send_time, self._get_ack_timeout(), num_retransmissions + 1)
                self.silence_timeout = self._get_silence_timeout()
                self.send_ack = False
        
        if self.silence_timeout <= time.time_ns():
            packet = create_ack_only_packet(self.state.get_outgoing_ack()) if self.send_ack else create_keep_alive_packet()
            socket.send_immediate(packet, remote_endpoint)
            self.silence_timeout = self._get_silence_timeout()
            self.send_ack = False
        return True
    
    def _enqueue_new_data(self):
        with self.data_queue_lock:
            while len(self.send_window) < self.cwnd and len(self.data_queue) > 0:
                next_payload = b''
                while len(self.data_queue) > 0 and len(next_payload) < MAX_PAYLOAD_SIZE:
                    space_left = MAX_PAYLOAD_SIZE - len(next_payload)
                    next_payload += self.data_queue[0][:space_left]
                    self.data_queue[0] = self.data_queue[0][space_left:]
                    if len(self.data_queue[0]) == 0:
                        self.data_queue = self.data_queue[1:]
                self.send_window.append((next_payload, time.time_ns(),  0, -1))

    def _get_ack_timeout(self) -> int:
        return time.time_ns() + int(self.rtt * 1.5)

    def _get_silence_timeout(self) -> int:
        return time.time_ns() + MAX_SILENCE