import socket
import os
import time

server_address = "network_command"
port = 65432
wifi_add = input("Enter IP: ")
wifi_port = 1001

def send_command(command):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(server_address)
        sock.send(command.encode('utf-8') + b'\0')
        data = ""
        while len(data) == 0 or data[-1] != '\0':
            buf = sock.recv(1024)
            data += buf.decode('utf-8')
        return data[:-1].strip()

def main():
    try:
        print("Sending command")
        data = send_command("create wifi_server rw --address {} --port {}".format(wifi_add,wifi_port))
        print("Got data: {}".format(data))
        in_file, out_file = data.split(" ")

        in_fh = os.open(in_file, os.O_RDONLY)
        out_fh = os.open(out_file, os.O_WRONLY)
        print("Starting communication")
        while True:
            try:
                buff = os.read(in_fh, 1024)
                if buff:
                    num = int(buff.decode('utf-8'))
                    print(num)
                    os.write(out_fh,str(num + 1).encode('utf-8'))
                else:
                    print('waiting')
            except BlockingIOError as E:
                if E.errno != 11:
                    raise E
    finally:
        os.close(in_fh);
        os.close(out_fh);

if __name__ == "__main__":
    main()
