import os
import socket
import subprocess as sp
import selectors

class Interface:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.created = False
        self.opened = False
        self.fh = None
        self._create()

    def _create(self):
        if not os.path.exists(self.filename):
            os.mkfifo(self.filename)
            self.created = True
        return self.filename

    def get_mode(self):
        return self.mode

    def get_file(self):
        return self.filename

    def get_fh(self):
        return self.fh

    def open(self):
        self.fh = os.open(self.filename)
        self.opened = True

    def close(self):
        if self.opened:
            os.close(self.fh)

        if self.created:
            os.remove(self.filename)

class Antenna:
    def __init__(self, data, file_path, interfaces={}):

        self.ant_type, self.modes, *original_process_args = data.split(" ")

        self.interfaces = {mode:self._create_interface(self._create_filename(file_path, mode)
                                                       if mode not in interfaces else interfaces[mode], mode) for mode in self.modes}

        process_args = [self.interfaces[mode].get_file() for mode in self.modes] + original_process_args
        
        self.process = sp.Popen(process_args, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)

    def name(self):
        return self.ant_type

    def get_interfaces(self):
        return [self.interfaces[mode] for mode in self.modes]

    def call(self, data):
        return self.process.communicate(data, timeout=1)

    def close(self):
        self.process.terminate()
        [self.interfaces[mode].close() for mode in self.interfaces]

    def get_stderr(self):
        return self.process.stderr

    def _create_filename(self, file_path, mode):
        return os.path.join(file_path, self.ant_type + "_" + mode)

    def _create_interface(self, file, mode):
        return Interface(file, mode)

class NetworkManager:
    def __init__(self, config):
        self._setup(config)
        
    def reset(self, config):
        self.close()
        self._setup(config)

    def process(self):
        events = self.sel.select()
        for key, mask in events:
            callback = key.data[0]
            callback(key)

    def close(self):
        [antenna.close() for antenna in self.antennas]
        self.server_socket.close()
        os.remove(self.config["server socket"])

    def _setup(self, config):
        self.config = config

        os.makedirs(self.config["pipe dir"],exist_ok=True)
        self.antennas = []
        self.antenna_dict = {}
        self.sel = selectors.DefaultSelector()
        self.fifo_files = set()
        self.in_interface = Interface(os.path.join(self.file_path, "network_manager_r"))
        self.out_interface = Interface(os.path.join(self.file_path, "network_manager_w"))

        try:
            os.remove(self.config["server socket"])
        except OSError:
            pass

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.config["server socket"])
        self.server_socket.listen()
        self.sel.register(self.server_socket, selectors.EVENT_READ, data=(self._handle_connection, None))

    def _create_connection(self, data):
        antenna = Antenna(data, self.config["pipe dir"])
        print("Antenna started")
        self.antennas.append(antenna)
        self.antenna_dict[antenna.name()] = antenna
        self.sel.register(antenna.get_stderr(), selectors.EVENT_READ, data=(self._antenna_error, antenna))
        return " ".join(antenna.get_interfaces())

    def _call_antenna(self, data):
        antenna_name = data[0]
        antenna = self.antenna_dict[antenna.name()] 
        antenna.call(data[1:])

    def _process_command(self, command_list):
        commands = {"create": self._create_connection}
        command_name, command_data = command_list
        try:
            return commands[command_name](command_data)
        except KeyError:
            return ""

    def _close_antenna(self, antenna):
        self.sel.unregister(antenna.get_stderr())
        antenna.close()
        self.antennas.remove(antenna)
        del self.antenna_dict[antenna.name()]

    def _antenna_error(self, key):
        print("Antenna failed")
        print(os.read(key.fd,1024).decode('utf-8'))
        self._close_antenna(key.data[1])

    def _read_command(self, key):
        try:
            data = ""
            while len(data) == 0 or data[-1] != '\0':
                buf = self.in_interface.get_(1024)
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

    def _handle_read(self, key):
        os.read(key.fh
        return blarg

    def _handle_connection(self, key):
        conn, addr = self.server_socket.accept()
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
