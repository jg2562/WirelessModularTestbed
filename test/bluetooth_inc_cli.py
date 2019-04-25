import socket
import os
import time

server_address = "network_command"
port = 65432
bt_add = "B8:27:EB:4B:65:06"
bt_port = 0x1001

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
        data = send_command("create bluetooth_client rw --address {} --port {}".format(bt_add,bt_port))
        print("Got data: {}".format(data))
        in_file, out_file = data.split(" ")

        in_fh = os.open(in_file, os.O_RDONLY)
        out_fh = os.open(out_file, os.O_WRONLY)
        time.sleep(5)
        print("Starting communication")
        os.write(out_fh, b'1')
        while True:
            try:
                buff = os.read(in_fh, 1024)
                if buff:
                    num = int(buff.decode('utf-8'))
                    print(num)
                    os.write(out_fh,str(num + 1).encode('utf-8'))
            except BlockingIOError as E:
                if E.errno != 11:
                    raise E
    finally:
        os.close(in_fh);
        os.close(out_fh);

if __name__ == "__main__":
    main()
