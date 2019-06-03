import os
import signal
import threading


def main():
    print("started", os.getpid())
    event = threading.Event()

    def handler(signum, frame):
        event.set()

    signal.signal(signal.SIGTERM, handler)

    event.wait()
    print("exit")


if __name__ == "__main__":
    main()
