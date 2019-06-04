import os
import signal
from pyprocs import main


def handler(signo, frame):
    os.kill(os.getpid(), signal.SIGINT)


def test_main():
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(2)
    main(["-s", "tests/app.py"])


def test_timeout():
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(2)
    main(["-s", "--graceful-timeout", "2", "tests/timeout_app.py"])


def test_bad():
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(2)
    main(["-t", "1", "-s", "nonexist.py"])
