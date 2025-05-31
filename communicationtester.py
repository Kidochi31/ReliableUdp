from socket import socket, AF_INET, SOCK_DGRAM
from select import select
from packet import interpret_packet, PayloadType
from sys import argv

show_keep_alive = False

def main():
    global show_keep_alive
    for arg in argv[1:]:
        if arg == "-ka":
            show_keep_alive = True

    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 0))
    port: int = s.getsockname()[1]
    print(f"name: 127.0.0.1:{port}")

    port1 = input("first port: ")
    address1 = "127.0.0.1"
    port1 = int(port1)
    endpoint1 = (address1, port1)

    port2 = input("second port: ")
    address2 = "127.0.0.1"
    port2 = int(port2)
    endpoint2 = (address2, port2)

    while True:
        try:
            rlist, _, _ = select([s], [], [], 0)
            if len(rlist) == 0:
                continue
            data, server = s.recvfrom(2000)
            
            if server == endpoint1:
                print_packet(1, 2, data)
                s.sendto(data, endpoint2)
            if server == endpoint2:
                print_packet(2, 1, data)
                s.sendto(data, endpoint1)
        except InterruptedError:
            break
        except:
            pass

def print_packet(source: str | int, destination: str | int, data: bytes):
    global show_keep_alive
    type, seq, ack, final, payload = interpret_packet(data)
    if type != PayloadType.NO_PAYLOAD or seq is not None or ack is not None or final or show_keep_alive:
        print(f"{source}->{destination}: type={type}, seq={seq}, ack={ack}, final={final}, payload={payload}")

if __name__ == "__main__":
    main()