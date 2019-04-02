#!/usr/bin/python3
# file: l2capclient.py
# desc: Demo L2CAP server for pybluez.
# $Id: l2capserver.py 524 2007-08-15 04:04:52Z albert $

import argparse
import os
import time

parser = argparse.ArgumentParser()
parser.add_argument('mode')
parser.add_argument('in_filename')
parser.add_argument('out_filename')
args = parser.parse_args()
mode = args.mode

if not mode == "rw":
    print("Bad mode for echo")
    exit(1)

fh_out = os.open(args.in_filename, os.O_WRONLY)
fh_in = os.open(args.out_filename, os.O_RDONLY|os.O_NONBLOCK)

print("Waiting for comms")
try:
    while True:
        try:
            buff = os.read(fh_in, 1024)
            if buff:
                print(buff)
                os.write(fh_out, buff)
        except BlockingIOError as E:
            if E.errno != 11:
                raise E

finally:
    os.close(fh_in)
    os.close(fh_out)