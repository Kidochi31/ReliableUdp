from connection import Connection
from threading import Lock
from udpsocket import UdpSocket
from packet import interpret_packet, PayloadType
from iptools import *

class ConnectionCollection:
    # connections: Dictionary[endpoint, Connection] - the dictionary of Connections from the remote endpoint
    # disconnections: list[Connection] - a list of connections that have recently disconnected but not been handled
    # udp_socket: UdpSocket
    # lock: Lock - the lock for this connection collection
    def __init__(self, udp_socket: UdpSocket):
        self.connections: dict[IP_endpoint, Connection] = {}
        self.disconnections: dict[IP_endpoint, Connection] = {}
        self.udp_socket = udp_socket
        self.lock = Lock()

    def __contains__(self, endpoint: IP_endpoint) -> bool:
        return endpoint in self.connections.keys()
    
    def __getitem__(self, endpoint: IP_endpoint) -> Connection:
        return self.connections[endpoint]
    
    def _manage_disconnection(self, connection: Connection):
        connection.close()
        self.connections.pop(connection.remote_endpoint)
        self.disconnections[connection.remote_endpoint] = connection

    def _get_or_create_connection(self, endpoint: IP_endpoint) -> tuple[bool, Connection]:
        if endpoint in self:
            return (False, self.connections[endpoint])
        # new connection
        new_connection = Connection(self.udp_socket, endpoint)
        self.connections[endpoint] = new_connection
        return (True, new_connection)

    def report_received_data(self, received_data: list[tuple[bytes, IP_endpoint | None]]) -> tuple[list[Connection], list[Connection], list[tuple[bytes, Connection]], list[tuple[bytes, Connection]]]:
        """
        Returns (new_connections, disconnections, reliable_data, unreliable_data)
        """
        with self.lock:
            new_connections: list[Connection] = []
            disconnections: list[Connection] = []
            reliable_data: list[tuple[bytes, Connection]] = []
            unreliable_data: list[tuple[bytes, Connection]] = []

            for data, endpoint in received_data:
                if endpoint is None:
                    continue
                type, seq, ack, final, payload = interpret_packet(data)
                new, connection = self._get_or_create_connection(endpoint)
                connection.receiver.report_receive()
                if new:
                    new_connections.append(connection)
                if final:
                    disconnections.append(connection)
                    self._manage_disconnection(connection)
                if type == PayloadType.RELIABLE and seq is not None:
                    pushed_data, must_send_ack = connection.receiver.queue_data(payload, seq)
                    for d in pushed_data:
                        if d != b'':
                            reliable_data.append((d, connection))
                    if must_send_ack:
                        connection.sender.report_outgoing_ack_change()
                if type == PayloadType.UNRELIABLE and payload != b'':
                    unreliable_data.append((payload, connection))
                connection.sender.report_received_ack(ack)
            return (new_connections, disconnections, reliable_data, unreliable_data)

    def tick_and_get_disconnections(self) -> list[Connection]:
        disconnections: list[Connection] = []

        for endpoint in list(self.connections.keys()):
            connection = self.connections[endpoint]
            if not connection.tick_still_connected():
                disconnections.append(connection)
                self._manage_disconnection(connection)
        
        return disconnections

    def disconnect_all(self):
        with self.lock:
            for endpoint in self.connections.keys():
                #connection = self.connections[endpoint]
                pass
            
            self.connections.clear()
            self.disconnections.clear()