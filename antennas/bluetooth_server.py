import argparse
import os
import time
import bluetooth

parser = argparse.ArgumentParser()
parser.add_argument('mode')
parser.add_argument('in_filename')
parser.add_argument('out_filename')
parser.add_argument('bluetooth_port')

args = parser.parse_args()
mode = args.mode

if not mode == "rw":
    print("Bad mode for echo")
    exit(1)

bt_sock_server = bluetooth.BluetoothSocket(bluetooth.L2CAP)
fh_out = os.open(args.in_filename, os.O_WRONLY)
fh_in = os.open(args.out_filename, os.O_RDONLY|os.O_NONBLOCK)

bt_sock_server.bind(("", args.bluetooth_port))
bt_sock_server.listen(1)

print("Waiting connection")
bt_sock, addr = bt_sock_server.accept()
print("Waiting for comms")
try:
    while True:
        try:
            buff = os.read(fh_in, 1024)
            if buff:
                bt_sock.send(buff)

            bt_sock.recv(1024)
            if buff:
                os.write(fh_out, buff)
            
        except BlockingIOError as E:
            if E.errno != 11:
                raise E

finally:
    os.close(fh_in)
    os.close(fh_out)
    bt_sock.close()
    bt_sock_server.close()

