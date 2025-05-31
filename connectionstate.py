

MAX_SEQ = 16777215
NUM_SEQ = 16777216
SEQ_RANGE = 8388608

class ConnectionState:
    
    def __init__(self):
        self.last_unacked_seq = 0
        self.next_needed_receive = 0
    
    def report_received_pushed_to_user(self, num_pushed_to_user: int):
         self.next_needed_receive += num_pushed_to_user
         self.next_needed_receive = self.next_needed_receive % NUM_SEQ

    def ack_outgoing(self, ack_received: int) -> int:
        """
        Returns the number of packets to stop sending
        """
        if ack_received == self.last_unacked_seq:
            return 0
        if ack_received > self.last_unacked_seq:
            difference = ack_received - self.last_unacked_seq
        else:
            difference = NUM_SEQ - self.last_unacked_seq + ack_received
        
        if difference <= SEQ_RANGE:
                self.last_unacked_seq += difference
                if self.last_unacked_seq > MAX_SEQ:
                     self.last_unacked_seq: int = self.last_unacked_seq % NUM_SEQ
                return difference
        else:
            return 0

    def get_outgoing_ack(self) -> int:
         return self.next_needed_receive

    def get_outgoing_seq(self, index: int) -> int:
         seq = index + self.last_unacked_seq
         return seq % NUM_SEQ
    
    def get_incoming_relative_seq(self, seq: int) -> int:
         if seq == self.next_needed_receive:
              return 0
         elif seq > self.next_needed_receive:
              return seq - self.next_needed_receive
         else: # seq < self.next_needed_receive
              return NUM_SEQ - self.next_needed_receive + seq