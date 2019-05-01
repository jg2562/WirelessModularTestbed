import socket
import os
import time

server_address = "network_command"
port = 65432

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
    print("Sending command")
    data = send_command("create echo rw")
    print("Got data: {}".format(data))
    ant_id, in_file, out_file = data.split(" ")

    time.sleep(1)
    print("Starting communication")
    data = send_command("info status {}".format(ant_id))
    print(data)
    data = send_command("close {}".format(ant_id))
    print(data)


if __name__ == "__main__":
    main()
