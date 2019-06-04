# pyprocs

[![Build Status](https://travis-ci.com/guyingbo/multiproc.svg?branch=master)](https://travis-ci.com/guyingbo/multiproc)
[![Python Version](https://img.shields.io/pypi/pyversions/pyprocs.svg)](https://pypi.python.org/pypi/pyprocs)
[![Version](https://img.shields.io/pypi/v/pyprocs.svg)](https://pypi.python.org/pypi/pyprocs)
[![Format](https://img.shields.io/pypi/format/pyprocs.svg)](https://pypi.python.org/pypi/pyprocs)
[![License](https://img.shields.io/pypi/l/pyprocs.svg)](https://pypi.python.org/pypi/pyprocs)
[![codecov](https://codecov.io/gh/guyingbo/pyprocs/branch/master/graph/badge.svg)](https://codecov.io/gh/guyingbo/pyprocs)

Multiprocsess manager, command-line version of python supervisor.

## Installation

~~~
pip3 install pyprocs
~~~

## Usage

~~~
usage: pyprocs.py [-h] [-w NUM_WORKERS] [--graceful-timeout SECONDS] [-s]
                  [-t SECONDS] [--fail-threshold SECONDS]
                  ARG [ARG ...]

Multiprocess manager

positional arguments:
  ARG                   program to run

optional arguments:
  -h, --help            show this help message and exit
  -w NUM_WORKERS, --num_workers NUM_WORKERS
                        number of worker processes, default to cpu count
  --graceful-timeout SECONDS
                        seconds to wait before force killing processes
  -s, --sys-executable  use system python executable
                        (/usr/local/opt/python/bin/python3.7) to run command
  -t SECONDS, --restart-wait SECONDS
                        seconds to wait before restart failed process (exit code
                        != 0)
  --fail-threshold SECONDS
                        process exit within N seconds is also considered as
                        a failure
~~~

## Example

~~~
python3 -m pyprocs -w 4 --graceful-timeout 10 -s script.py
~~~

~~~
python3 -m pyprocs sh program.sh
~~~
