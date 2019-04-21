import os
import socket
import subprocess as sp

class Antenna:
    def __init__(self, data, file_path):
        self.ant_type, self.modes, *process_args = data.split(" ")
        self.interfaces = {mode:self._create_fifo(self._create_filename(file_path, mode)) for mode in self.modes}
        
        self.process = sp.Popen(" ".join(process_args), shell=True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)

    def get_interfaces(self):
        return [self.interfaces[mode] for mode in self.modes]

    def close(self):
        self.process.terminate()
        [os.remove(self.interfaces[mode]) for mode in self.interfaces]

    def _create_filename(self, file_path, mode):
        return os.path.join(file_path, self.ant_type + "_" + mode)

    def _create_fifo(self, file):
        if not os.path.exists(file):
            os.mkfifo(file)
        return file

class NetworkManager:
    def __init__(self, config):
        self._setup(config)
        
    def reset(self, config):
        self.close()
        self._setup(config)

    def process(self):
        conn, addr = self.server_socket.accept()
        self._handle_connection(conn, addr)

    def close(self):
        [antenna.close() for antenna in self.antennas]
        self.server_socket.close()
        os.remove(self.config["server socket"])

    def _setup(self, config):
        self.config = config

        os.makedirs(self.config["pipe dir"],exist_ok=True)
        self.antennas = []
        self.fifo_files = set()

        try:
            os.remove(self.config["server socket"])
        except OSError:
            pass

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.config["server socket"])
        self.server_socket.listen()

    def _create_connection(self, data):
        antenna = Antenna(data, self.config["pipe dir"])
        print("started antenna")
        self.antennas.append(antenna)
        return " ".join(antenna.get_interfaces())

    def _process_command(self, command_list):
        commands = {"create": self._create_connection}
        command_name, command_data = command_list
        return commands[command_name](command_data)

    def _handle_connection(self, conn, address):
        try:
            data = ""
            while len(data) == 0 or data[-1] != '\0':
                buf = conn.recv(1024)
                data += buf.decode('utf-8')
            data = data[:-1].strip()
            val = self._process_command(data.split(" ", 1))
            conn.send(val.encode('utf-8') + b'\0')
        except IOError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass


def main():
    config = {"server socket": "network_command",
              "pipe dir": "/tmp/wmtb",
              "processes":{"echo":"python3 antennas/echo.py",
                           "bluetooth_client":"python3 antennas/bluetooth_antenna.py",
                           "bluetooth_server":"python3 antennas/bluetooth_antenna.py"}}

    manager = NetworkManager(config)
    try:
        while True:
            manager.process()
    finally:
        manager.close()

main()
