from packet import create_reliable_packet, interpret_packet, create_unreliable_packet, create_ack_only_packet, create_keep_alive_packet
from random import randint


def main():
    print("-------------Reliable Packets-------------")
    seq = randint(0, pow(2, 24) - 1)
    ack = randint(0, pow(2, 24) - 1)
    final = False
    payload = b"reliable packet with ack"
    print(f"packet: seq={seq}, ack={ack}, final={final}, payload={payload}")
    packet = create_reliable_packet(seq, ack, final, payload)
    (type, seq, ack, final, payload) = interpret_packet(packet)
    print(f"interpreted packet: type={type}, seq={seq}, ack={ack}, final={final}, payload={payload}")

    seq = randint(0, pow(2, 24) - 1)
    ack = None
    final = False
    payload = b"reliable packet with no ack"
    print(f"packet: seq={seq}, ack={ack}, final={final}, payload={payload}")
    packet = create_reliable_packet(seq, ack, final, payload)
    (type, seq, ack, final, payload) = interpret_packet(packet)
    print(f"interpreted packet: type={type}, seq={seq}, ack={ack}, final={final}, payload={payload}")

    seq = randint(0, pow(2, 24) - 1)
    ack = randint(0, pow(2, 24) - 1)
    final = True
    payload = b"reliable packet with final and ack"
    print(f"packet: seq={seq}, ack={ack}, final={final}, payload={payload}")
    packet = create_reliable_packet(seq, ack, final, payload)
    (type, seq, ack, final, payload) = interpret_packet(packet)
    print(f"interpreted packet: type={type}, seq={seq}, ack={ack}, final={final}, payload={payload}")

    print("")
    print("-------------Unreliable Packets-------------")
    seq = randint(0, pow(2, 24) - 1)
    payload = b"unreliable packet"
    print(f"packet: seq={seq}, payload={payload}")
    packet = create_unreliable_packet(seq, payload)
    (type, seq, ack, final, payload) = interpret_packet(packet)
    print(f"interpreted packet: type={type}, seq={seq}, ack={ack}, final={final}, payload={payload}")

    print("")
    print("-------------Ack-Only Packets-------------")
    ack = randint(0, pow(2, 24) - 1)
    print(f"packet: ack={ack}")
    packet = create_ack_only_packet(ack)
    (type, seq, ack, final, payload) = interpret_packet(packet)
    print(f"interpreted packet: type={type}, seq={seq}, ack={ack}, final={final}, payload={payload}")

    print("")
    print("-------------Keep-Alive Packets-------------")
    print(f"packet: KEEP-ALIVE")
    packet = create_keep_alive_packet()
    (type, seq, ack, final, payload) = interpret_packet(packet)
    print(f"interpreted packet: type={type}, seq={seq}, ack={ack}, final={final}, payload={payload}")


if __name__ == "__main__":
    main()