import argparse
import os
import time
import bluetooth
import selectors

parser = argparse.ArgumentParser()
parser.add_argument('mode')
parser.add_argument('in_filename')
parser.add_argument('out_filename')
parser.add_argument('--port', type=int)
parser.add_argument('--address', required=False)

args = parser.parse_args()
mode = args.mode

if not mode == "rw":
    print("Bad mode for bluetooth")
    exit(1)

sel = selectors.DefaultSelector()

sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
fh_out = os.open(args.in_filename, os.O_WRONLY)
fh_in = os.open(args.out_filename, os.O_RDONLY)

def start_bluetooth(sock, args):
    def client(address, port):
        sock.connect((address, port))
        return sock

    def server(port):
        sock.bind(("", port))
        sock.listen(1)
        bt_sock, addr = sock.accept()
        return bt_sock


    if args.address is None:
        return server(args.port)
    else:
        return client(args.address, args.port)

bt_sock = start_bluetooth(sock, args)

def receive_bluetooth():
    buff = bt_sock.recv(1024)
    if buff:
        os.write(fh_out, buff)

def send_bluetooth():
    buff = os.read(fh_in, 1024)
    if buff:
        bt_sock.send(buff)

sel.register(bt_sock, selectors.EVENT_READ, receive_bluetooth)
sel.register(fh_in, selectors.EVENT_READ, send_bluetooth)

print("Waiting for comms")
try:
    while True:
        events = sel.select()
        for key, mask in events:
            key.data()


finally:
    sel.close()
    os.close(fh_in)
    os.close(fh_out)
    bt_sock.close()

