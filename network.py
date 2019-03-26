import os
import socket
import subprocess as sp

pipe_path = "/tmp/wmtb"
server_socket = "network_command"
port = 65432

config = {"processes":{"echo":"python3 /home/jack/Dropbox/code/school/capstone/echo.py"}}
processes = []
fifo_files = set()

def create_fifo(filename):
    file_path = os.path.join(pipe_path,filename)
    if not os.path.exists(file_path):
        os.mkfifo(file_path)
    fifo_files.add(file_path)
    return file_path

def create_process(process_name, *args):
    process_run = process_name.split(" ") + list(args)
    print(process_run)
    process = sp.Popen(" ".join(process_run), shell=True)
    print("started process")
    processes.append(process)
    return process

def create_connection(connection_type, connection_mode,*args):
    file_paths = [create_fifo(connection_type + "_" + mode) for mode in connection_mode]
    process = create_process(config["processes"][connection_type], connection_mode, *file_paths, *args)
    return " ".join(file_paths)

def process_command(command_list):
    commands = {"create": create_connection}
    return commands[command_list[0]](*command_list[1:])

def handle_connection(conn, address):
    try:
        data = ""
        while len(data) == 0 or data[-1] != '\0':
            buf = conn.recv(1024)
            data += buf.decode('utf-8')
        data = data[:-1].strip()
        val = process_command(data.split(" "))
        print("Sending val: {}".format(val))
        conn.send(val.encode('utf-8') + b'\0')
    except IOError:
        pass
    finally:
        try:
            conn.close()
        except OSError:
            pass
        

def clean_up():
    [process.terminate() for process in processes]
    os.remove(server_socket)
    [os.remove(file) for file in fifo_files]

def main():
    os.makedirs(pipe_path,exist_ok=True)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        try:
            print("Server started")
            s.bind(server_socket)
            s.listen()
            while True:
                conn, addr = s.accept()
                handle_connection(conn, addr)
        finally:
            s.close()

try:
    main()
finally:
    clean_up()
