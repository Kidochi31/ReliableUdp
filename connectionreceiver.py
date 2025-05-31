from connectionstate import ConnectionState
import time


MAX_RECEIVE_SILENCE = 10_000_000_000

class ConnectionReceiver:

    def __init__(self, state: ConnectionState, receive_window: int):
        self.state = state
        self.queue: list[bytes | None] = [None] * receive_window
        self.last_receive = time.time_ns()

    def report_receive(self):
        self.last_receive = time.time_ns()

    def queue_data(self, payload: bytes, seq: int) -> tuple[list[bytes], bool]:
        # returns any new data to be pushed to the user, and whether an ack needs to be sent
        relative_seq = self.state.get_incoming_relative_seq(seq)
        if relative_seq >= len(self.queue): # old data, already received -> should ack it anyway
            return ([], True)
        elif relative_seq > 0:
            self.queue[relative_seq] = payload # data is put in queue, but need 
            return ([], False)
        else:
            # must push data
            self.queue[0] = payload
            push_data : list[bytes] = []
            num_pushed = 0
            while num_pushed < len(self.queue):
                val = self.queue[num_pushed]
                if val is None:
                    break
                push_data.append(val)
                num_pushed += 1
            self.state.report_received_pushed_to_user(num_pushed)
            
            index = num_pushed
            while index < len(self.queue):
                self.queue[index - num_pushed] = self.queue[index]
                if num_pushed != 0:
                    self.queue[index] = None
                index += 1
            return (push_data, True) # new data, received, send ack
    
    def tick(self) -> bool:
        """
        Returns true if still connected
        """
        if time.time_ns() - self.last_receive > MAX_RECEIVE_SILENCE:
            return False
        return True