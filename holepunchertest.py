from udpsocket import UdpSocket
from holepuncher import HolePuncher
from threading import Thread
import traceback
from socket import AF_INET

should_quit = None

def main():
    socket = UdpSocket(0, [("stun.ekiga.net", 3478)], AF_INET)
    hp = HolePuncher(socket)
    
    def tick_func():
        while not socket.closed:
            hp.tick()
            fails = hp.take_fails()
            for fail in fails:
                print(f"HOLE PUNCH FAIL: {fail}")

    tick_thread = Thread(target=tick_func)
    tick_thread.start()
    
    try:
        while True:
            if socket.closed:
                break
            text = input("")
            if text == "quit":
                socket.close()
            elif text.startswith("holepunch "):
                text = text.removeprefix("holepunch ")
                timeout, text = text.split(" ", maxsplit=1)
                timeout = float(timeout)
                address, port = text.split(":", maxsplit=1)
                port = int(port)
                endpoint = (address, port)
                hp.hole_punch(endpoint, timeout)
            elif text.startswith("rm "):
                text = text.removeprefix("rm ")
                address, port = text.split(":", maxsplit=1)
                port = int(port)
                endpoint = (address, port)
                hp.remove_hole_puncher(endpoint)
    except BaseException:
        print(f"\nException in main loop: {traceback.format_exc()}")
        socket.close()
    
    print("Main Thread Ended")


if __name__ == "__main__":
    main()