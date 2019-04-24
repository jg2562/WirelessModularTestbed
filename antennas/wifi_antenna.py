import argparse
import os
import time
import selectors
import socket


parser = argparse.ArgumentParser()
parser.add_argument('mode')
parser.add_argument('in_filename')
parser.add_argument('out_filename')
parser.add_argument('--port', type=int)
parser.add_argument('--address', required=False)

args = parser.parse_args()
mode = args.mode
hostname = socket.gethostname()    
HOST = socket.gethostbyname(hostname)  
PORT = args.port

#setup
sel = selectors.DefaultSelector()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

fh_out = os.open(args.in_filename, os.O_WRONLY)
fh_in = os.open(args.out_filename, os.O_RDONLY)

def start_wifi(sock,args):
    def server():
        sock.bind((HOST, PORT))
        sock.listen(1)
        conn, addr=sock.accept()
        return wifi_sock

        #msg = input('>')
        #conn.send(msg.encode('utf-8'))
        return sock
    
    #client code
    def client():
        sock.connect((coHOST, PORT))
        #data = s.recv(1024)
        #print(data.decode('utf-8'))
        
    if args.address is None:
        return server(args.port)
    else:
        return client(args.address, args.port)

wifi_sock = start_wifi(sock,args)

def receive_wifi():
    buff = wifi_sock.recv(1024)
    if buff:
        os.write(fh_out,buff)

def send_wifi():
    buff = os.read(fh_in, 1024)
    if buff:
        bt_sock.send(buff)

sel.register(bt_sock, selectors.EVENT_READ, receive_wifi)
sel.register(fh_in, selectors.EVENT_READ, send_wifi)

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

