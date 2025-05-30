from enum import Enum

FINAL_BIT = 4
ACK_BIT = 5
UNRELIABLE_BIT = 6
RELIABLE_BIT = 7

def create_reliable_packet(seq: int, ack: int | None, final: bool, payload: bytes) -> bytes:
    seq_bytes = seq.to_bytes(3, byteorder="big")

    flags = 0
    flags = flags | (1 << RELIABLE_BIT)
    if ack is not None:
        flags = flags | (1 << ACK_BIT)
    if final:
        flags = flags | (1 << FINAL_BIT)
    flag_bytes = flags.to_bytes(1, byteorder="big")
    space_bytes = b''

    ack_bytes = b''
    if ack is not None:
        ack_bytes = ack.to_bytes(3, byteorder="big")
        space_bytes = b'\0'
    
    
    return seq_bytes + flag_bytes + ack_bytes + space_bytes + payload

def create_unreliable_packet(seq: int, payload: bytes) -> bytes:
    seq_bytes = seq.to_bytes(3, byteorder="big")

    flags = 0
    flags = flags | (1 << UNRELIABLE_BIT)
    flag_bytes = flags.to_bytes(1, byteorder="big")
    return seq_bytes + flag_bytes + payload

def create_ack_only_packet(ack: int) -> bytes:
    ack_bytes = ack.to_bytes(3, byteorder="big")

    flags = 0
    flags = flags | (1 << ACK_BIT)
    flag_bytes = flags.to_bytes(1, byteorder="big")
    return ack_bytes + flag_bytes

def create_keep_alive_packet() -> bytes:
    return b''

class PayloadType(Enum):
    RELIABLE = 0
    UNRELIABLE = 1
    NO_PAYLOAD = 2

def interpret_packet(packet: bytes | None) -> tuple[PayloadType, int | None, int | None, bool, bytes | None]:
    """
    Returns (PayloadType, seq?, ack?, final, payload?)
    """
    if packet is None or len(packet) < 4: # corrupted, incorrect, or keep alive packet
        return (PayloadType.NO_PAYLOAD, None, None, False, None)
    flags = packet[3]
    reliable = (flags & (1 << RELIABLE_BIT)) != 0
    unreliable = (flags & (1 << UNRELIABLE_BIT)) != 0
    acking = (flags & (1 << ACK_BIT)) != 0
    final = (flags & (1 << FINAL_BIT)) != 0
    seq = None
    ack = None
    if reliable or unreliable:
        seq = int.from_bytes(packet[0:3], byteorder="big")
        packet = packet[4:]
    if acking:
        ack = int.from_bytes(packet[0:3], byteorder="big")
        packet = packet[4:]
    # now packet is at the beginning of the payload
    if len(packet) == 0:
        packet = None
    type = (PayloadType.NO_PAYLOAD if (packet is None)
            else (PayloadType.RELIABLE if reliable
                  else (PayloadType.UNRELIABLE)))
    return (type, seq, ack, final, packet)