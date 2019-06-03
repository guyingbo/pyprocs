import os
import sys
import time
import signal
import subprocess
from multiproc import main


def handler(signo, frame):
    os.kill(os.getpid(), signal.SIGINT)


def test_normal():
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
    main(["-s", "app.py"])


def test_main():
    p = subprocess.Popen([sys.executable, "multiproc.py", "-s", "tests/app.py"])
    time.sleep(1)
    p.terminate()
    p.wait()
