import os
import signal

from pyprocs import main
from typer import Typer
from typer.testing import CliRunner

app = Typer()
app.command()(main)


runner = CliRunner()


def handler(signo, frame):
    os.kill(os.getpid(), signal.SIGINT)


def test_main():
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(2)
    runner.invoke(app, ["-s", "tests/app.py"])


def test_timeout():
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(2)
    runner.invoke(app, ["-s", "--graceful-timeout", "2", "tests/timeout_app.py"])


def test_bad():
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(2)
    runner.invoke(app, ["-t", "1", "-s", "nonexist.py"])
