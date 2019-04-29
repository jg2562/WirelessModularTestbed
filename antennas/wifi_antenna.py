import argparse
import os
import time
import selectors
import socket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode')
    parser.add_argument('in_filename')
    parser.add_argument('out_filename')
    parser.add_argument('--port', type=int)
    parser.add_argument('--address', required=False)

    args = parser.parse_args()
    mode = args.mode
    
    #setup
    if not mode == "rw":
        print("Bad mode for wifi")
        exit(1)
    sel = selectors.DefaultSelector()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    fh_out = os.open(args.in_filename, os.O_WRONLY)
    fh_in = os.open(args.out_filename, os.O_RDONLY)
    print('Socket intialized.')
    
    def start_wifi(sock,args):
        
        def server(address, port):
            sock.bind((address, port))
            sock.listen(2)
            
            wifi_sock, addr=sock.accept()
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            return wifi_sock

        def client(address, port):
            sock.connect((address, port))
            return sock

        if args.address is None:
            return server('', args.port)
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
            wifi_sock.send(buff)
    
    sel.register(wifi_sock, selectors.EVENT_READ, receive_wifi)
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
        wifi_sock.close()


if __name__ == "__main__":
    main()
